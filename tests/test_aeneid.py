"""Virgil's Aeneid as test material.

Source: Aeneid Book 1, lines 1-11, Perseus / Greenough 1900 text
(CC BY-SA 3.0 US), stored in data/aeneid/book1_1_11.txt. Virgil died
in 19 BCE; the Latin text itself is public domain, the Perseus
edition is credited in the file and in docs/aeneid.md.

These tests do not claim a full parse of an 11-line poetic sentence
(one sentence, many clauses, heavy ellipsis). They assert what the
engine actually does on this text: token coverage, the famous first
line, and ablative constructions that occur in it.
"""

from pathlib import Path

from latin_nlp.pipeline import analyze_text, get_analyzer, parse_text

AENEID_1_11 = Path(__file__).resolve().parents[1] / "data" / "aeneid" / "book1_1_11.txt"
AENEID_12_33 = Path(__file__).resolve().parents[1] / "data" / "aeneid" / "book1_12_33.txt"
analyzer = get_analyzer()


def has(word, lemma, **kwargs):
    for a in analyzer.analyze(word):
        if a.lemma == lemma and all(getattr(a, k, None) == v for k, v in kwargs.items()):
            return True
    return False


def test_aeneid_file_exists_and_starts_correctly():
    text = AENEID_1_11.read_text(encoding="utf-8")
    assert text.startswith("Arma virumque cano")
    assert "Tantaene animis caelestibus irae?" in text


def test_aeneid_coverage():
    res = analyze_text(AENEID_1_11.read_text(encoding="utf-8"))
    # Curated lexicon is built for this passage; coverage should be
    # essentially complete. If it drops below 95%, the lexicon regressed.
    assert res.coverage >= 0.95, f"coverage {res.coverage:.0%}, unknown: {[t.original for t in res.tokens if t.analyses and t.analyses[0].unknown]}"


def test_aeneid_first_line():
    assert has("arma", "arma", case="accusative", number="plural")
    assert has("virumque", "vir", case="accusative", number="singular")
    assert has("cano", "cano", person="1", number="singular", tense="present", mood="indicative")
    assert has("Troiae", "Troia", case="genitive", number="singular")
    assert has("oris", "ora", number="plural")  # dat./abl. plural, ab forces ablative
    assert has("Italiam", "Italia", case="accusative", number="singular")
    assert has("fato", "fatum", number="singular")  # dat./abl. singular, bare ablative of means
    assert has("venit", "venio", person="3", number="singular", tense="present", mood="indicative")
    assert has("litora", "litus", number="plural")


def test_aeneid_participles():
    assert has("iactatus", "iacto", tense="perfect", mood="participle")
    assert has("passus", "patior", tense="perfect", mood="participle")
    assert has("laeso", "laedo", tense="perfect", mood="participle")
    assert has("dolens", "doleo", tense="present", mood="participle")


def test_aeneid_ablatives_in_context():
    res = parse_text("Troiae qui primus ab oris Italiam, fato profugus venit")
    kinds = [(a.tokens, a.kind) for a in res.ablatives]
    assert any("oris" in toks and "separation" in kind for toks, kind in kinds)
    # fato is a bare ablative in this clause
    assert any("fato" in toks for toks, _ in kinds)


def test_aeneid_invocation():
    res = parse_text("Musa, mihi causas memora, quo numine laeso")
    assert res.direct_object == ["causas"]
    assert any(a.kind == "ablative absolute" for a in res.ablatives)


def test_aeneid_12_33_file_exists_and_coverage():
    assert AENEID_12_33.exists()
    text = AENEID_12_33.read_text(encoding="utf-8")
    assert text.startswith("Urbs antiqua fuit")
    assert "Tantae molis erat Romanam condere gentem." in text
    res = analyze_text(text)
    assert res.coverage >= 0.95, f"coverage {res.coverage:.0%}, unknown: {[t.original for t in res.tokens if t.analyses and t.analyses[0].unknown]}"


def test_aeneid_i_stems():
    # Neuter i-stems (nom/acc pl -ia)
    assert has("maria", "mare", case="accusative", number="plural")
    # M/F i-stems (acc pl -es, dat/abl pl -ibus, gen sg -is)
    assert has("arces", "arx", case="accusative", number="plural")
    assert has("gentibus", "gens", case="dative", number="plural")
    assert has("molis", "moles", case="genitive", number="singular")
    # 3rd-declension adjectives
    assert has("immitis", "immitis", case="genitive", number="singular")
    assert has("omnia", "omnis", case="accusative", number="plural")


def test_aeneid_pluperfect_and_syncopation():
    # Pluperfect indicative active
    assert has("audierat", "audio", person="3", number="singular", tense="pluperfect", mood="indicative")
    assert has("gesserat", "gero", person="3", number="singular", tense="pluperfect", mood="indicative")
    assert has("exciderant", "excido", person="3", number="plural", tense="pluperfect", mood="indicative")
    # Poetic 3rd plural perfect in -ere
    assert has("tenuere", "teneo", person="3", number="plural", tense="perfect", mood="indicative")


def test_aeneid_passives_and_participles():
    # Irregular / regular passive
    assert has("fertur", "fero", person="3", number="singular", tense="present", mood="indicative", voice="passive")
    # Present passive infinitive
    assert has("duci", "duco", tense="present", mood="infinitive", voice="passive")
    # Future active participle
    assert has("venturum", "venio", tense="future", mood="participle", voice="active")
    # Perfect passive participle
    assert has("repostum", "repono", tense="perfect", mood="participle", voice="passive")
    # Perfect active infinitive
    assert has("coluisse", "colo", tense="perfect", mood="infinitive", voice="active")


def test_aeneid_indirect_statement():
    res = parse_text("Progeniem duci audierat")
    assert len(res.indirect_statements) > 0
    ind = res.indirect_statements[0]
    assert ind.subject_accusative == "Progeniem"
    assert ind.infinitive == "duci"


def test_aeneid_ablative_place():
    res_place = parse_text("iactatos aequore toto")
    kinds_place = [a.kind for a in res_place.ablatives]
    assert any("place where" in k for k in kinds_place)


def test_accusative_duration_under_per_regression():
    res_time = parse_text("multosque per annos errarent")
    assert res_time.direct_object == []
    assert res_time.ablatives == []
    assert any(p.kind == "accusative of duration under per" for p in res_time.prepositional_phrases)
