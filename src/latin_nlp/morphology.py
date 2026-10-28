"""Morphological analyzer: stage 2 of the pipeline.

Whitaker-style algorithm, in plain terms:
1. Look the form up exactly in the irregular / attested-forms table.
2. Otherwise, generate every regular form from every lemma's stem +
   the ending tables for its declension / conjugation, and reverse-index
   form -> analyses. A match is a stem + a legal ending, not a guess.
3. Otherwise, try the stemmer fallback: strip a known ending, longest
   first, and check whether the remaining stem belongs to a lemma.
   This is what lets an unseen regular form of a known lemma still
   analyze, and what makes the analyzer algorithmic rather than a
   word-list lookup.

Confidence: irregular/exact = 1.0, generated regular = 0.95,
stemmer fallback = 0.75, unknown = 0.0. These are ranking scores for
choosing the best analysis in a sentence, not probabilities.
"""

from __future__ import annotations

from dataclasses import dataclass

from .lexer import normalize, split_enclitic
from .lexicon import Entry, load_lexicon
from .schemas import TokenAnalysis

# ---------------------------------------------------------------- endings
# Each tuple: (case, number, ending) for nouns/adjectives, in order.
DECL1 = [
    ("nominative", "singular", "a"), ("genitive", "singular", "ae"),
    ("dative", "singular", "ae"), ("accusative", "singular", "am"),
    ("ablative", "singular", "a"), ("vocative", "singular", "a"),
    ("nominative", "plural", "ae"), ("genitive", "plural", "arum"),
    ("dative", "plural", "is"), ("accusative", "plural", "as"),
    ("ablative", "plural", "is"), ("vocative", "plural", "ae"),
]
DECL2_M = [
    ("nominative", "singular", "us"), ("genitive", "singular", "i"),
    ("dative", "singular", "o"), ("accusative", "singular", "um"),
    ("ablative", "singular", "o"), ("vocative", "singular", "e"),
    ("nominative", "plural", "i"), ("genitive", "plural", "orum"),
    ("dative", "plural", "is"), ("accusative", "plural", "os"),
    ("ablative", "plural", "is"), ("vocative", "plural", "i"),
]
DECL2_N = [
    ("nominative", "singular", "um"), ("genitive", "singular", "i"),
    ("dative", "singular", "o"), ("accusative", "singular", "um"),
    ("ablative", "singular", "o"), ("vocative", "singular", "um"),
    ("nominative", "plural", "a"), ("genitive", "plural", "orum"),
    ("dative", "plural", "is"), ("accusative", "plural", "a"),
    ("ablative", "plural", "is"), ("vocative", "plural", "a"),
]
DECL3_MF = [
    ("genitive", "singular", "is"), ("dative", "singular", "i"),
    ("accusative", "singular", "em"), ("ablative", "singular", "e"),
    ("nominative", "plural", "es"), ("genitive", "plural", "um"),
    ("dative", "plural", "ibus"), ("accusative", "plural", "es"),
    ("ablative", "plural", "ibus"),
]
DECL3_N = [
    ("genitive", "singular", "is"), ("dative", "singular", "i"),
    ("ablative", "singular", "e"),
    ("nominative", "plural", "a"), ("genitive", "plural", "um"),
    ("dative", "plural", "ibus"), ("accusative", "plural", "a"),
    ("ablative", "plural", "ibus"),
]
DECL3_I_MF = [
    ("genitive", "singular", "is"), ("dative", "singular", "i"),
    ("accusative", "singular", "em"), ("ablative", "singular", "e"),
    ("nominative", "plural", "es"), ("genitive", "plural", "ium"),
    ("dative", "plural", "ibus"), ("accusative", "plural", "es"),
    ("accusative", "plural", "is"),
    ("ablative", "plural", "ibus"),
]
DECL3_I_N = [
    ("genitive", "singular", "is"), ("dative", "singular", "i"),
    ("ablative", "singular", "i"),
    ("nominative", "plural", "ia"), ("genitive", "plural", "ium"),
    ("dative", "plural", "ibus"), ("accusative", "plural", "ia"),
    ("ablative", "plural", "ibus"),
]
DECL3_ADJ_MF = [
    ("nominative", "singular", "is"), ("genitive", "singular", "is"),
    ("dative", "singular", "i"), ("accusative", "singular", "em"),
    ("ablative", "singular", "i"), ("vocative", "singular", "is"),
    ("nominative", "plural", "es"), ("genitive", "plural", "ium"),
    ("dative", "plural", "ibus"), ("accusative", "plural", "es"),
    ("accusative", "plural", "is"), ("ablative", "plural", "ibus"),
    ("vocative", "plural", "es"),
]
DECL3_ADJ_N = [
    ("nominative", "singular", "e"), ("genitive", "singular", "is"),
    ("dative", "singular", "i"), ("accusative", "singular", "e"),
    ("ablative", "singular", "i"), ("vocative", "singular", "e"),
    ("nominative", "plural", "ia"), ("genitive", "plural", "ium"),
    ("dative", "plural", "ibus"), ("accusative", "plural", "ia"),
    ("ablative", "plural", "ibus"), ("vocative", "plural", "ia"),
]
DECL4 = [
    # stem is cas- / man- (the -u- belongs to the ending, not the stem):
    # casus, casus, casui, casum, casu, casus / casus, casuum, casibus...
    ("nominative", "singular", "us"), ("genitive", "singular", "us"),
    ("dative", "singular", "ui"), ("accusative", "singular", "um"),
    ("ablative", "singular", "u"), ("vocative", "singular", "us"),
    ("nominative", "plural", "us"), ("genitive", "plural", "uum"),
    ("dative", "plural", "ibus"), ("accusative", "plural", "us"),
    ("ablative", "plural", "ibus"), ("vocative", "plural", "us"),
]
DECL5 = [
    ("nominative", "singular", "es"), ("genitive", "singular", "ei"),
    ("dative", "singular", "ei"), ("accusative", "singular", "em"),
    ("ablative", "singular", "e"), ("vocative", "singular", "es"),
    ("nominative", "plural", "es"), ("genitive", "plural", "erum"),
    ("dative", "plural", "ebus"), ("accusative", "plural", "es"),
    ("ablative", "plural", "ebus"), ("vocative", "plural", "es"),
]

PERSONS = ["1", "2", "3", "1", "2", "3"]


@dataclass
class _Form:
    form: str
    lemma: str
    pos: str
    gloss: str
    case: str | None = None
    number: str | None = None
    gender: str | None = None
    person: str | None = None
    tense: str | None = None
    mood: str | None = None
    voice: str | None = None


def _noun_forms(e: Entry) -> list[_Form]:
    stem = (e.stem or "").lower()
    out: list[_Form] = []
    decl = str(e.declension)
    if decl == "1":
        for case, num, end in DECL1:
            out.append(_Form(stem + end, e.lemma, e.pos, e.gloss, case, num, "f"))
    elif decl == "2":
        table = DECL2_M if e.gender != "n" else DECL2_N
        for case, num, end in table:
            out.append(_Form(stem + end, e.lemma, e.pos, e.gloss, case, num, e.gender))
        # vir, puer-type nominatives: nominative singular is the stem itself
        if e.lemma.lower() == stem:
            out.append(_Form(stem, e.lemma, e.pos, e.gloss, "nominative", "singular", e.gender))
            out.append(_Form(stem, e.lemma, e.pos, e.gloss, "vocative", "singular", e.gender))
    elif decl in ("3", "3i"):
        if decl == "3i":
            table = DECL3_I_MF if e.gender != "n" else DECL3_I_N
        else:
            table = DECL3_MF if e.gender != "n" else DECL3_N
        out.append(_Form(e.lemma.lower(), e.lemma, e.pos, e.gloss, "nominative", "singular", e.gender))
        out.append(_Form(e.lemma.lower(), e.lemma, e.pos, e.gloss, "vocative", "singular", e.gender))
        if e.gender == "n":
            out.append(_Form(e.lemma.lower(), e.lemma, e.pos, e.gloss, "accusative", "singular", e.gender))
        for case, num, end in table:
            out.append(_Form(stem + end, e.lemma, e.pos, e.gloss, case, num, e.gender))
    elif decl == "4":
        for case, num, end in DECL4:
            out.append(_Form(stem + end, e.lemma, e.pos, e.gloss, case, num, e.gender))
    elif decl == "5":
        for case, num, end in DECL5:
            out.append(_Form(stem + end, e.lemma, e.pos, e.gloss, case, num, e.gender))
    return out


def _adj12_forms(e: Entry) -> list[_Form]:
    stem = (e.stem or "").lower()
    out: list[_Form] = []
    for gender, table in (("m", DECL2_M), ("f", DECL1), ("n", DECL2_N)):
        for case, num, end in table:
            out.append(_Form(stem + end, e.lemma, e.pos, e.gloss, case, num, gender))
    return out


def _adj3_forms(e: Entry) -> list[_Form]:
    stem = (e.stem or "").lower()
    out: list[_Form] = []
    lem = e.lemma.lower()
    if lem.endswith("is"):
        for case, num, end in DECL3_ADJ_MF:
            out.append(_Form(stem + end, e.lemma, e.pos, e.gloss, case, num, "m"))
            out.append(_Form(stem + end, e.lemma, e.pos, e.gloss, case, num, "f"))
        for case, num, end in DECL3_ADJ_N:
            out.append(_Form(stem + end, e.lemma, e.pos, e.gloss, case, num, "n"))
    else:
        for g in ("m", "f", "n"):
            out.append(_Form(lem, e.lemma, e.pos, e.gloss, "nominative", "singular", g))
            out.append(_Form(lem, e.lemma, e.pos, e.gloss, "vocative", "singular", g))
        out.append(_Form(lem, e.lemma, e.pos, e.gloss, "accusative", "singular", "n"))
        for case, num, end in DECL3_MF:
            out.append(_Form(stem + end, e.lemma, e.pos, e.gloss, case, num, "m"))
            out.append(_Form(stem + end, e.lemma, e.pos, e.gloss, case, num, "f"))
            if case in ("genitive", "dative", "ablative"):
                out.append(_Form(stem + end, e.lemma, e.pos, e.gloss, case, num, "n"))
        for g in ("m", "f", "n"):
            out.append(_Form(stem + "i", e.lemma, e.pos, e.gloss, "ablative", "singular", g))
        out.append(_Form(stem + "ia", e.lemma, e.pos, e.gloss, "nominative", "plural", "n"))
        out.append(_Form(stem + "ia", e.lemma, e.pos, e.gloss, "accusative", "plural", "n"))
    return out


def _verb_present(e: Entry, conj: int) -> list[_Form]:
    """Present / imperfect / future / subjunctive / imperative / infinitive."""
    stem = (e.stem or "").lower()
    inf = (e.infinitive or "").lower()
    inf_stem = inf[:-2] if inf.endswith("re") else inf  # amare->ama-, etc.
    out: list[_Form] = []
    nums = ["singular", "singular", "singular", "plural", "plural", "plural"]

    def add(forms: list[str], tense: str, mood: str, voice: str):
        for form, person, num in zip(forms, PERSONS, nums):
            out.append(_Form(form, e.lemma, e.pos, e.gloss, None, num, None, person, tense, mood, voice))

    pass_voice = "active" if e.deponent else "passive"
    if conj == 1:
        # 1st conjugation stem is ama-, ambula-, etc.: the -a- is kept
        # before consonant endings (amas, amat, amamus) and dropped
        # before -o / -or (amo, amor). Lexicon stores the base (am-).
        stem_a = stem + "a"
        if not e.deponent:
            add([stem + "o", stem_a + "s", stem_a + "t", stem_a + "mus", stem_a + "tis", stem_a + "nt"], "present", "indicative", "active")
        add([stem + "or", stem_a + "ris", stem_a + "tur", stem_a + "mur", stem_a + "mini", stem_a + "ntur"], "present", "indicative", pass_voice)
        if not e.deponent:
            add([stem_a + x for x in ("bam", "bas", "bat", "bamus", "batis", "bant")], "imperfect", "indicative", "active")
        add([stem_a + x for x in ("bar", "baris", "batur", "bamur", "bamini", "bantur")], "imperfect", "indicative", pass_voice)
        if not e.deponent:
            add([stem_a + x for x in ("bo", "bis", "bit", "bimus", "bitis", "bunt")], "future", "indicative", "active")
        else:
            add([stem_a + x for x in ("bor", "beris", "bitur", "bimur", "bimini", "buntur")], "future", "indicative", pass_voice)
        add([stem + x for x in ("em", "es", "et", "emus", "etis", "ent")], "present", "subjunctive", "active" if not e.deponent else pass_voice)
    elif conj == 2:
        if not e.deponent:
            add([stem + x for x in ("eo", "es", "et", "emus", "etis", "ent")], "present", "indicative", "active")
        add([stem + x for x in ("eor", "eris", "etur", "emur", "emini", "entur")], "present", "indicative", pass_voice)
        if not e.deponent:
            add([stem + x for x in ("ebam", "ebas", "ebat", "ebamus", "ebatis", "ebant")], "imperfect", "indicative", "active")
        add([stem + x for x in ("ebar", "ebaris", "ebatur", "ebamur", "ebamini", "ebantur")], "imperfect", "indicative", pass_voice)
        if not e.deponent:
            add([stem + x for x in ("ebo", "ebis", "ebit", "ebimus", "ebitis", "ebunt")], "future", "indicative", "active")
        else:
            add([stem + x for x in ("ebor", "eberis", "ebitur", "ebimur", "ebimini", "ebuntur")], "future", "indicative", pass_voice)
        add([stem + x for x in ("eam", "eas", "eat", "eamus", "eatis", "eant")], "present", "subjunctive", "active" if not e.deponent else pass_voice)
    elif conj == 3:
        if not e.deponent:
            add([stem + x for x in ("o", "is", "it", "imus", "itis", "unt")], "present", "indicative", "active")
        add([stem + x for x in ("or", "eris", "itur", "imur", "imini", "untur")], "present", "indicative", pass_voice)
        if not e.deponent:
            add([stem + x for x in ("ebam", "ebas", "ebat", "ebamus", "ebatis", "ebant")], "imperfect", "indicative", "active")
        add([stem + x for x in ("ebar", "ebaris", "ebatur", "ebamur", "ebamini", "ebantur")], "imperfect", "indicative", pass_voice)
        if not e.deponent:
            add([stem + x for x in ("am", "es", "et", "emus", "etis", "ent")], "future", "indicative", "active")
        else:
            add([stem + x for x in ("ar", "eris", "etur", "emur", "emini", "entur")], "future", "indicative", pass_voice)
        add([stem + x for x in ("am", "as", "at", "amus", "atis", "ant")], "present", "subjunctive", "active" if not e.deponent else pass_voice)
    elif conj == 4:
        if not e.deponent:
            add([stem + x for x in ("o", "s", "t", "mus", "tis", "unt")], "present", "indicative", "active")
        add([stem + x for x in ("or", "ris", "tur", "mur", "mini", "untur")], "present", "indicative", pass_voice)
        if not e.deponent:
            add([stem + x for x in ("ebam", "ebas", "ebat", "ebamus", "ebatis", "ebant")], "imperfect", "indicative", "active")
        add([stem + x for x in ("ebar", "ebaris", "ebatur", "ebamur", "ebamini", "ebantur")], "imperfect", "indicative", pass_voice)
        if not e.deponent:
            add([stem + x for x in ("am", "es", "et", "emus", "etis", "ent")], "future", "indicative", "active")
        else:
            add([stem + x for x in ("ar", "eris", "etur", "emur", "emini", "entur")], "future", "indicative", pass_voice)
        add([stem + x for x in ("am", "as", "at", "amus", "atis", "ant")], "present", "subjunctive", "active" if not e.deponent else pass_voice)
    # imperfect subjunctive: infinitive stem + rem/res/ret/remus/retis/rent
    add([inf_stem + x for x in ("rem", "res", "ret", "remus", "retis", "rent")], "imperfect", "subjunctive", "active" if not e.deponent else pass_voice)
    # imperative present
    imp_sg = {"1": stem + "a", "2": stem + "e", "3": stem + "e", "4": stem}.get(str(conj), stem)
    # for conj 4, stem already ends in i (audi-), so imperative sg is stem itself
    if conj == 4:
        imp_sg = stem
    imp_pl = {"1": stem + "ate", "2": stem + "ete", "3": stem + "ite", "4": stem + "te"}.get(str(conj), stem + "te")
    out.append(_Form(imp_sg, e.lemma, e.pos, e.gloss, None, "singular", None, "2", "present", "imperative", "active"))
    out.append(_Form(imp_pl, e.lemma, e.pos, e.gloss, None, "plural", None, "2", "present", "imperative", "active"))
    # infinitive present
    if e.deponent:
        pass_inf = {"1": inf_stem + "ari", "2": inf_stem + "eri", "3": stem + "i", "4": inf_stem + "iri"}.get(str(conj), inf)
        out.append(_Form(pass_inf, e.lemma, e.pos, e.gloss, None, None, None, None, "present", "infinitive", "active"))
    else:
        out.append(_Form(inf, e.lemma, e.pos, e.gloss, None, None, None, None, "present", "infinitive", "active"))
        pass_inf = {"1": inf_stem + "ari", "2": inf_stem + "eri", "3": stem + "i", "4": inf_stem + "iri"}.get(str(conj), inf_stem + "ri")
        out.append(_Form(pass_inf, e.lemma, e.pos, e.gloss, None, None, None, None, "present", "infinitive", "passive"))
    # present participle: stem + ns / ntis / nte / ntem
    if conj == 2:
        part = stem + "ens"
    elif conj == 1:
        part = stem + "ans"
    else:
        part = stem + "ens"
    out.append(_Form(part, e.lemma, e.pos, e.gloss, "nominative", "singular", None, None, "present", "participle", "active"))
    return out


def _verb_perfect(e: Entry) -> list[_Form]:
    out: list[_Form] = []
    if e.perfect_stem:
        stem = e.perfect_stem.lower()
        stems = [stem]
        # Syncopated poetic forms (audiverat -> audierat, amavistis -> amastis)
        if stem.endswith("iv"):
            stems.append(stem[:-1])
        nums = ["singular", "singular", "singular", "plural", "plural", "plural"]
        for s in stems:
            for forms, tense, mood in [
                (["i", "isti", "it", "imus", "istis", "erunt"], "perfect", "indicative"),
                (["erim", "eris", "erit", "erimus", "eritis", "erint"], "perfect", "subjunctive"),
                (["eram", "eras", "erat", "eramus", "eratis", "erant"], "pluperfect", "indicative"),
            ]:
                for form_end, person, num in zip(forms, PERSONS, nums):
                    out.append(_Form(s + form_end, e.lemma, e.pos, e.gloss, None, num, None, person, tense, mood, "active"))
            # 3rd-plural perfect alternate in -ere (tenuere, fuere)
            out.append(_Form(s + "ere", e.lemma, e.pos, e.gloss, None, "plural", None, "3", "perfect", "indicative", "active"))
            # perfect active infinitive
            out.append(_Form(s + "isse", e.lemma, e.pos, e.gloss, None, None, None, None, "perfect", "infinitive", "active"))
    # perfect passive / deponent active participle from supine stem, declined 1/2
    if e.supine_stem:
        s = e.supine_stem.lower()
        part_voice = "active" if e.deponent else "passive"
        for gender, table in (("m", DECL2_M), ("f", DECL1), ("n", DECL2_N)):
            for case, num, end in table:
                out.append(_Form(s + end, e.lemma, e.pos, e.gloss, case, num, gender, None, "perfect", "participle", part_voice))
        # future active participle (e.g. venturus, venturum)
        s_fut = s + "ur"
        for gender, table in (("m", DECL2_M), ("f", DECL1), ("n", DECL2_N)):
            for case, num, end in table:
                out.append(_Form(s_fut + end, e.lemma, e.pos, e.gloss, case, num, gender, None, "future", "participle", "active"))
    return out


class MorphAnalyzer:
    """Builds the reverse index once, then analyzes forms in O(1) lookup."""

    def __init__(self, entries: list[Entry] | None = None):
        self.entries = entries if entries is not None else load_lexicon()
        self._index: dict[str, list[_Form]] = {}
        self._irregular: dict[str, list[_Form]] = {}
        self._build()

    def _add(self, form: _Form, irregular: bool = False):
        key = form.form.lower()
        target = self._irregular if irregular else self._index
        target.setdefault(key, []).append(form)

    def _build(self):
        for e in self.entries:
            # irregular / attested forms first, they win on lookup
            for form, meta in (e.irregular or {}).items():
                self._add(_Form(form.lower(), e.lemma, e.pos, e.gloss,
                                meta.get("case"), meta.get("number"), meta.get("gender"),
                                meta.get("person"), meta.get("tense"), meta.get("mood"), meta.get("voice")),
                          irregular=True)
            if e.pos in ("preposition", "conjunction", "adverb"):
                self._add(_Form(e.lemma.lower(), e.lemma, e.pos, e.gloss))
                continue
            if e.pos == "adjective" and e.declension is None:
                # indeclinable adjective, e.g. tot: the lemma is the form
                self._add(_Form(e.lemma.lower(), e.lemma, e.pos, e.gloss))
                continue
            if e.plural_only:
                # plural-only nouns: nominative plural form is also
                # accusative plural (arma, moenia), so add both readings
                for form, meta in list((e.irregular or {}).items()):
                    if meta.get("case") == "nominative" and meta.get("number") == "plural":
                        self._add(_Form(form.lower(), e.lemma, e.pos, e.gloss,
                                        "accusative", "plural", meta.get("gender")),
                                  irregular=True)
            if e.pos == "pronoun":
                continue  # pronouns are fully listed in irregular
            if e.pos == "noun":
                for f in _noun_forms(e):
                    self._add(f)
            elif e.pos == "adjective":
                if str(e.declension) == "1/2":
                    for f in _adj12_forms(e):
                        self._add(f)
                elif str(e.declension) in ("3", "3i"):
                    for f in _adj3_forms(e):
                        self._add(f)
                else:
                    # other adjectives: irregular table covers the
                    # attested forms; stemmer fallback covers the rest
                    pass
            elif e.pos == "verb":
                if e.irregular and e.lemma in ("sum", "eo", "adeo", "infero", "fero", "volo", "possum"):
                    # irregular verbs: only irregular + participle generation
                    if e.supine_stem:
                        for f in _verb_perfect(e):
                            # _verb_perfect also adds perfect indicative
                            # from perfect_stem, which irregular verbs
                            # already list -- skip those, keep participles
                            if f.mood == "participle":
                                self._add(f)
                    continue
                conj = int(e.conjugation or 1)
                for f in _verb_present(e, conj):
                    self._add(f)
                for f in _verb_perfect(e):
                    self._add(f)

    def analyze(self, word: str) -> list[TokenAnalysis]:
        """Return analyses for one form, best first. Empty list if unknown."""
        norm = normalize(word)
        # 1. exact irregular
        if norm in self._irregular:
            return [self._to_analysis(f, norm, 1.0) for f in self._irregular[norm]]
        # 2. generated regular
        if norm in self._index:
            return [self._to_analysis(f, norm, 0.95) for f in self._index[norm]]
        # 3. enclitic split: virumque -> virum + que
        stem_form, enc = split_enclitic(norm)
        if enc and stem_form != norm:
            inner = self.analyze(stem_form)
            if inner:
                out = []
                for a in inner:
                    a = a.model_copy(update={"enclitic": enc, "confidence": 0.9})
                    out.append(a)
                return out
        # 4. stemmer fallback: strip a known ending, longest first
        for ending in sorted(_all_endings(), key=len, reverse=True):
            if norm.endswith(ending) and len(norm) > len(ending):
                stem = norm[: -len(ending)] if ending else norm
                for e in self.entries:
                    if e.stem and e.stem.lower() == stem:
                        # ending alone does not give case/tense safely;
                        # report it as a stem match, low confidence
                        return [TokenAnalysis(form=norm, lemma=e.lemma, pos=e.pos,
                                              gloss=e.gloss, confidence=0.75)]
        return []

    @staticmethod
    def _to_analysis(f: _Form, form: str, conf: float) -> TokenAnalysis:
        return TokenAnalysis(form=form, lemma=f.lemma, pos=f.pos, gloss=f.gloss,
                             case=f.case, number=f.number, gender=f.gender,
                             person=f.person, tense=f.tense, mood=f.mood,
                             voice=f.voice, confidence=conf)


def _all_endings() -> set[str]:
    ends: set[str] = set()
    for table in (DECL1, DECL2_M, DECL2_N, DECL3_MF, DECL3_N, DECL3_I_MF, DECL3_I_N, DECL3_ADJ_MF, DECL3_ADJ_N, DECL4, DECL5):
        for _, _, end in table:
            if end:
                ends.add(end)
    return ends
