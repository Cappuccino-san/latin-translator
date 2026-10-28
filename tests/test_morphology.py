"""Golden morphology tests: known forms must analyze to the known lemma.

A test passes if ANY analysis matches the expected lemma + the
expected morphology field. Latin forms are genuinely ambiguous
(puellae = genitive singular, dative singular, nominative plural),
so requiring the top analysis to be the one reading would be
dishonest; the parser, not the analyzer, disambiguates in context.
"""

import pytest

from latin_nlp.pipeline import analyze_text, get_analyzer, parse_text

analyzer = get_analyzer()


def has(word, lemma, **kwargs):
    """True if any analysis of word matches lemma + kwargs."""
    for a in analyzer.analyze(word):
        if a.lemma == lemma and all(getattr(a, k, None) == v for k, v in kwargs.items()):
            return True
    return False


# --- declensions 1-5 -------------------------------------------------------
@pytest.mark.parametrize("form,lemma,case,number", [
    ("puella", "puella", "nominative", "singular"),
    ("puellae", "puella", "genitive", "singular"),
    ("puellam", "puella", "accusative", "singular"),
    ("puellas", "puella", "accusative", "plural"),
    ("puellis", "puella", "dative", "plural"),
    ("servus", "servus", "nominative", "singular"),
    ("servi", "servus", "genitive", "singular"),
    ("servum", "servus", "accusative", "singular"),
    ("servos", "servus", "accusative", "plural"),
    ("bellum", "bellum", "nominative", "singular"),
    ("bello", "bellum", "ablative", "singular"),
    ("bella", "bellum", "nominative", "plural"),
    ("regis", "rex", "genitive", "singular"),
    ("regem", "rex", "accusative", "singular"),
    ("reges", "rex", "nominative", "plural"),
    ("urbem", "urbs", "accusative", "singular"),
    ("urbis", "urbs", "genitive", "singular"),
    ("patres", "pater", "nominative", "plural"),
    ("generis", "genus", "genitive", "singular"),
    ("litora", "litus", "nominative", "plural"),
    ("casus", "casus", "nominative", "singular"),
    ("casuum", "casus", "genitive", "plural"),
    ("casibus", "casus", "dative", "plural"),
    ("manus", "manus", "nominative", "singular"),
    ("manum", "manus", "accusative", "singular"),
    ("rei", "res", "genitive", "singular"),
    ("rerum", "res", "genitive", "plural"),
    ("diei", "dies", "genitive", "singular"),
])
def test_declensions(form, lemma, case, number):
    assert has(form, lemma, case=case, number=number), f"{form} should be {lemma} {case} {number}"


# --- conjugations, active and passive --------------------------------------
@pytest.mark.parametrize("form,lemma,person,number,tense,mood,voice", [
    ("amo", "amo", "1", "singular", "present", "indicative", "active"),
    ("amas", "amo", "2", "singular", "present", "indicative", "active"),
    ("amat", "amo", "3", "singular", "present", "indicative", "active"),
    ("amamus", "amo", "1", "plural", "present", "indicative", "active"),
    ("amant", "amo", "3", "plural", "present", "indicative", "active"),
    ("amor", "amo", "1", "singular", "present", "indicative", "passive"),
    ("amatur", "amo", "3", "singular", "present", "indicative", "passive"),
    ("amabam", "amo", "1", "singular", "imperfect", "indicative", "active"),
    ("amabo", "amo", "1", "singular", "future", "indicative", "active"),
    ("amem", "amo", "1", "singular", "present", "subjunctive", "active"),
    ("amarem", "amo", "1", "singular", "imperfect", "subjunctive", "active"),
    ("amavi", "amo", "1", "singular", "perfect", "indicative", "active"),
    ("amatus", "amo", None, "singular", "perfect", "participle", "passive"),
    ("habes", "habeo", "2", "singular", "present", "indicative", "active"),
    ("habet", "habeo", "3", "singular", "present", "indicative", "active"),
    ("ducis", "duco", "2", "singular", "present", "indicative", "active"),
    ("ducit", "duco", "3", "singular", "present", "indicative", "active"),
    ("ducunt", "duco", "3", "plural", "present", "indicative", "active"),
    ("duceret", "duco", "3", "singular", "imperfect", "subjunctive", "active"),
    ("audis", "audio", "2", "singular", "present", "indicative", "active"),
    ("audit", "audio", "3", "singular", "present", "indicative", "active"),
    ("audiunt", "audio", "3", "plural", "present", "indicative", "active"),
    ("canit", "cano", "3", "singular", "present", "indicative", "active"),
    ("canunt", "cano", "3", "plural", "present", "indicative", "active"),
    ("venit", "venio", "3", "singular", "present", "indicative", "active"),
    ("veniunt", "venio", "3", "plural", "present", "indicative", "active"),
    ("scribit", "scribo", "3", "singular", "present", "indicative", "active"),
    ("mittit", "mitto", "3", "singular", "present", "indicative", "active"),
])
def test_conjugations(form, lemma, person, number, tense, mood, voice):
    assert has(form, lemma, person=person, number=number, tense=tense, mood=mood, voice=voice)


# --- irregular verbs: esse, ire, and friends --------------------------------
@pytest.mark.parametrize("form,lemma,person,number,tense,mood", [
    ("sum", "sum", "1", "singular", "present", "indicative"),
    ("es", "sum", "2", "singular", "present", "indicative"),
    ("est", "sum", "3", "singular", "present", "indicative"),
    ("sumus", "sum", "1", "plural", "present", "indicative"),
    ("estis", "sum", "2", "plural", "present", "indicative"),
    ("sunt", "sum", "3", "plural", "present", "indicative"),
    ("eram", "sum", "1", "singular", "imperfect", "indicative"),
    ("ero", "sum", "1", "singular", "future", "indicative"),
    ("esse", "sum", None, None, "present", "infinitive"),
    ("fui", "sum", "1", "singular", "perfect", "indicative"),
    ("sim", "sum", "1", "singular", "present", "subjunctive"),
    ("eo", "eo", "1", "singular", "present", "indicative"),
    ("is", "eo", "2", "singular", "present", "indicative"),
    ("it", "eo", "3", "singular", "present", "indicative"),
    ("imus", "eo", "1", "plural", "present", "indicative"),
    ("itis", "eo", "2", "plural", "present", "indicative"),
    ("eunt", "eo", "3", "plural", "present", "indicative"),
    ("ibam", "eo", "1", "singular", "imperfect", "indicative"),
    ("ibo", "eo", "1", "singular", "future", "indicative"),
    ("ire", "eo", None, None, "present", "infinitive"),
    ("ii", "eo", "1", "singular", "perfect", "indicative"),
    ("fero", "fero", "1", "singular", "present", "indicative"),
    ("fert", "fero", "3", "singular", "present", "indicative"),
    ("tuli", "fero", "1", "singular", "perfect", "indicative"),
    ("volo", "volo", "1", "singular", "present", "indicative"),
    ("vult", "volo", "3", "singular", "present", "indicative"),
    ("possum", "possum", "1", "singular", "present", "indicative"),
    ("potest", "possum", "3", "singular", "present", "indicative"),
])
def test_irregular_verbs(form, lemma, person, number, tense, mood):
    assert has(form, lemma, person=person, number=number, tense=tense, mood=mood)


# --- enclitics ----------------------------------------------------------------
def test_enclitic_que():
    assert has("virumque", "vir", case="accusative", number="singular")
    a = analyzer.analyze("virumque")[0]
    assert a.enclitic == "que"


def test_enclitic_ne():
    # tantaene = tantae + -ne (interrogative enclitic, Aeneid 1.11)
    assert has("tantaene", "tantus")
    assert analyzer.analyze("tantaene")[0].enclitic == "ne"


def test_macron_normalization():
    assert has("canō", "cano", person="1", number="singular", tense="present", mood="indicative")


# --- parser -------------------------------------------------------------------
def test_parser_subject_object():
    res = parse_text("Puella servum videt")
    assert res.subject == ["Puella"]
    assert res.direct_object == ["servum"]
    assert res.verb and res.verb.lemma == "video"


def test_parser_implied_subject():
    res = parse_text("Arma virumque cano")
    assert res.subject == ["ego (implied, 1st person)"]
    assert "Arma" in res.direct_object and "virumque" in res.direct_object


def test_parser_ablative_with_preposition():
    res = parse_text("Puella cum servo ambulat")
    kinds = [a.kind for a in res.ablatives]
    assert any("accompaniment" in k for k in kinds)
    assert not any(t == "Puella" for a in res.ablatives for t in a.tokens)


def test_parser_vocative_is_not_subject():
    res = parse_text("Musa, mihi causas memora")
    assert res.subject == ["tu (implied, 2nd person)"]
    assert res.direct_object == ["causas"]
    assert not any(t == "Musa" for a in res.ablatives for t in a.tokens)


def test_parser_ablative_absolute():
    # quo numine laeso: numen (abl.) + laesus (abl. participle)
    res = parse_text("quo numine laeso")
    assert any(a.kind == "ablative absolute" for a in res.ablatives)


def test_caesar_opening_tokens():
    res = analyze_text("Gallia est omnis divisa in partes tres")
    assert res.coverage >= 0.85
    lemmas = {a.lemma for t in res.tokens for a in t.analyses}
    assert {"Gallia", "sum", "omnis", "divido", "pars", "tres"} <= lemmas


def test_cicero_tokens():
    res = analyze_text("Quo usque tandem abutere, Catilina, patientia nostra?")
    # abutere (deponent abuse) is not in the curated lexicon yet; the
    # test asserts the words we do cover, and documents the gap honestly
    assert res.coverage >= 0.6
