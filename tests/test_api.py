"""API tests, via FastAPI TestClient (no server needed)."""

from fastapi.testclient import TestClient

from latin_nlp.api import app

client = TestClient(app)


def test_index_endpoint():
    r = client.get("/")
    assert r.status_code == 200
    assert "Latin NLP" in r.text
    assert "Puella servum videt" in r.text
    assert "btn-analyze" in r.text
    assert "btn-parse" in r.text
    assert "btn-open-read" in r.text
    assert "translation-card" in r.text
    assert "English Translation (Public Domain)" in r.text


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_analyze_endpoint():
    r = client.post("/analyze", json={"text": "Puella servum videt"})
    assert r.status_code == 200
    body = r.json()
    assert body["known_tokens"] == 3
    assert body["coverage"] == 1.0
    assert body["tokens"][0]["analyses"][0]["lemma"] == "puella"


def test_parse_endpoint():
    r = client.post("/parse", json={"text": "Puella servum videt"})
    assert r.status_code == 200
    body = r.json()
    assert body["subject"] == ["Puella"]
    assert body["direct_object"] == ["servum"]


def test_lemmatize_endpoint():
    r = client.post("/lemmatize", json={"word": "puellae"})
    assert r.status_code == 200
    assert any(a["lemma"] == "puella" for a in r.json()["analyses"])


def test_aeneid_endpoint():
    r = client.get("/aeneid")
    assert r.status_code == 200
    lines = r.json()
    assert len(lines) == 11
    assert lines[0]["latin"].startswith("Arma virumque cano")
    assert lines[0]["book"] == 1

    r2 = client.get("/aeneid?passage=12-33")
    assert r2.status_code == 200
    lines2 = r2.json()
    assert len(lines2) == 22
    assert lines2[0]["latin"].startswith("Urbs antiqua fuit")
    assert lines2[-1]["latin"].startswith("Tantae molis erat")


def test_virgil_default_endpoint():
    r = client.get("/virgil")
    assert r.status_code == 200
    lines = r.json()
    assert len(lines) == 33
    assert lines[0]["work"] == "aeneid"
    assert lines[0]["book"] == 1
    assert lines[0]["line"] == 1
    assert lines[0]["latin"].startswith("Arma virumque cano")
    assert lines[32]["line"] == 33


def test_virgil_eclogues_endpoint():
    r = client.get("/virgil?work=eclogues&book=1&start=1&end=5")
    assert r.status_code == 200
    lines = r.json()
    assert len(lines) == 5
    assert lines[0]["work"] == "eclogues"
    assert lines[0]["book"] == 1
    assert lines[0]["line"] == 1
    assert "Tityre" in lines[0]["latin"]


def test_virgil_georgics_endpoint():
    r = client.get("/virgil?work=georgics&book=1&start=1&end=5")
    assert r.status_code == 200
    lines = r.json()
    assert len(lines) == 5
    assert lines[0]["work"] == "georgics"
    assert lines[0]["book"] == 1
    assert lines[0]["line"] == 1
    assert "Quid faciat laetas" in lines[0]["latin"]


def test_virgil_catalog_endpoint():
    r = client.get("/virgil/catalog")
    assert r.status_code == 200
    data = r.json()
    keys = [item["key"] for item in data]
    assert "aeneid" in keys
    assert "eclogues" in keys
    assert "georgics" in keys


def test_virgil_404_error():
    r = client.get("/virgil?work=nonexistent")
    assert r.status_code == 404
    r2 = client.get("/virgil?work=aeneid&book=99")
    assert r2.status_code == 404


def test_virgil_translation_aeneid_1_11():
    r = client.get("/virgil/translation?work=aeneid&book=1&start=1&end=11")
    assert r.status_code == 200
    data = r.json()
    assert data["available"] is True
    assert data["work"] == "aeneid"
    assert data["book"] == 1
    assert data["start"] == 1
    assert data["end"] == 11
    assert data["translator"] == "Theodore C. Williams"
    assert data["year"] == 1910
    assert "Arms and the man I sing" in data["text"]
    assert "O Muse" in data["text"]
    assert len(data["lines"]) == 11
    assert data["lines"][0]["line"] == 1
    assert "Arms and the man I sing" in data["lines"][0]["text"]


def test_virgil_translation_aeneid_single_line():
    r = client.get("/virgil/translation?work=aeneid&book=1&start=1&end=1")
    assert r.status_code == 200
    data = r.json()
    assert data["available"] is True
    assert "Arms and the man I sing" in data["text"]
    assert len(data["lines"]) == 1


def test_virgil_translation_aeneid_12_33():
    r = client.get("/virgil/translation?work=aeneid&book=1&start=12&end=33")
    assert r.status_code == 200
    data = r.json()
    assert data["available"] is True
    assert "ancient city stood" in data["text"]
    assert "Roman line" in data["text"]
    assert len(data["lines"]) == 22


def test_virgil_translation_eclogues():
    r = client.get("/virgil/translation?work=eclogues&book=1&start=1&end=5")
    assert r.status_code == 200
    data = r.json()
    assert data["available"] is True
    assert data["translator"] == "James Rhoades"
    assert data["year"] == 1921
    assert "Tityrus" in data["text"]


def test_virgil_translation_georgics():
    r = client.get("/virgil/translation?work=georgics&book=1&start=1&end=5")
    assert r.status_code == 200
    data = r.json()
    assert data["available"] is True
    assert data["translator"] == "James Rhoades"
    assert "cornfield" in data["text"]


def test_virgil_translation_fallback():
    # Nonexistent work returns available=False
    r = client.get("/virgil/translation?work=nonexistent&book=1&start=1&end=5")
    assert r.status_code == 200
    data = r.json()
    assert data["available"] is False
    assert data["text"] is None

    # Line range out of bounds returns available=False
    r2 = client.get("/virgil/translation?work=aeneid&book=1&start=99999&end=99999")
    assert r2.status_code == 200
    assert r2.json()["available"] is False


def test_virgil_read_aeneid():
    r = client.get("/virgil/read?work=aeneid&book=1")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Aeneid Book 1" in r.text
    assert "Arma virumque cano" in r.text
    assert "Arms and the man I sing" in r.text
    assert "Theodore C. Williams" in r.text
    assert "line-1" in r.text
    assert "line-756" in r.text


def test_virgil_read_eclogues_and_georgics():
    r_ecl = client.get("/virgil/read?work=eclogues&book=1")
    assert r_ecl.status_code == 200
    assert "Eclogue 1" in r_ecl.text
    assert "Tityre" in r_ecl.text
    assert "James Rhoades" in r_ecl.text

    r_geo = client.get("/virgil/read?work=georgics&book=1")
    assert r_geo.status_code == 200
    assert "Georgics Book 1" in r_geo.text
    assert "Quid faciat laetas" in r_geo.text


def test_virgil_read_404():
    r = client.get("/virgil/read?work=nonexistent&book=1")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/json")
    assert "not found" in r.json()["detail"].lower()

    r2 = client.get("/virgil/read?work=aeneid&book=99")
    assert r2.status_code == 404
    assert r2.headers["content-type"].startswith("application/json")
    assert "not found" in r2.json()["detail"].lower()


# --- API Hardening Tests ---

def test_analyze_empty_and_whitespace():
    # Empty string
    r1 = client.post("/analyze", json={"text": ""})
    assert r1.status_code == 400
    assert "cannot be empty" in r1.json()["detail"]

    # Whitespace only
    r2 = client.post("/analyze", json={"text": "   \n\t  "})
    assert r2.status_code == 400
    assert "cannot be empty" in r2.json()["detail"]


def test_parse_empty_and_whitespace():
    # Empty string
    r1 = client.post("/parse", json={"text": ""})
    assert r1.status_code == 400
    assert "cannot be empty" in r1.json()["detail"]

    # Whitespace only
    r2 = client.post("/parse", json={"text": "   \r\n  "})
    assert r2.status_code == 400
    assert "cannot be empty" in r2.json()["detail"]


def test_lemmatize_empty_and_whitespace():
    r1 = client.post("/lemmatize", json={"word": ""})
    assert r1.status_code == 400
    assert "cannot be empty" in r1.json()["detail"]

    r2 = client.post("/lemmatize", json={"word": "   "})
    assert r2.status_code == 400
    assert "cannot be empty" in r2.json()["detail"]


def test_analyze_and_parse_very_long_input():
    huge_text = "Arma virumque cano. " * 3000  # ~63,000 characters
    r_an = client.post("/analyze", json={"text": huge_text})
    assert r_an.status_code == 400
    assert "exceeds maximum length" in r_an.json()["detail"]

    r_parse = client.post("/parse", json={"text": huge_text})
    assert r_parse.status_code == 400
    assert "exceeds maximum length" in r_parse.json()["detail"]


def test_virgil_invalid_work_and_book():
    r_work = client.get("/virgil?work=iliad&book=1")
    assert r_work.status_code == 404
    assert "not found" in r_work.json()["detail"].lower()

    r_book_low = client.get("/virgil?work=aeneid&book=0")
    assert r_book_low.status_code == 404
    assert "not found" in r_book_low.json()["detail"].lower()

    r_book_high = client.get("/virgil?work=aeneid&book=13")
    assert r_book_high.status_code == 404
    assert "not found" in r_book_high.json()["detail"].lower()


def test_virgil_start_greater_than_end_or_negative():
    r_rev = client.get("/virgil?work=aeneid&book=1&start=20&end=10")
    assert r_rev.status_code == 400
    assert "cannot be greater than end" in r_rev.json()["detail"]

    r_neg = client.get("/virgil?work=aeneid&book=1&start=0&end=10")
    assert r_neg.status_code == 400
    assert "greater than or equal to 1" in r_neg.json()["detail"]


def test_virgil_out_of_range_lines():
    # Aeneid Book 1 has 756 lines
    r = client.get("/virgil?work=aeneid&book=1&start=1000&end=1020")
    assert r.status_code == 404
    assert "out of range" in r.json()["detail"].lower()


def test_virgil_translation_start_greater_than_end():
    r = client.get("/virgil/translation?work=aeneid&book=1&start=20&end=10")
    assert r.status_code == 400
    assert "cannot be greater than end" in r.json()["detail"]

    r_zero = client.get("/virgil/translation?work=aeneid&book=1&start=0&end=10")
    assert r_zero.status_code == 400
    assert "greater than or equal to 1" in r_zero.json()["detail"]


def test_aeneid_invalid_passage():
    r = client.get("/aeneid?passage=34-50")
    assert r.status_code == 400
    assert "not supported" in r.json()["detail"]


def test_corpus_in_memory_cache():
    from latin_nlp.api import get_virgil_lines, load_translation_data

    # Clear caches and verify caching behavior
    get_virgil_lines.cache_clear()
    load_translation_data.cache_clear()

    # First access loads from disk
    lines1 = get_virgil_lines("aeneid", 1)
    info1 = get_virgil_lines.cache_info()
    assert info1.misses >= 1
    assert lines1 is not None and len(lines1) == 756

    # Second access hits memory cache directly (zero disk I/O)
    lines2 = get_virgil_lines("aeneid", 1)
    info2 = get_virgil_lines.cache_info()
    assert info2.hits >= 1
    assert lines1 == lines2

    # Translation cache test
    tdata1 = load_translation_data("aeneid", 1)
    t_info1 = load_translation_data.cache_info()
    assert t_info1.misses >= 1

    tdata2 = load_translation_data("aeneid", 1)
    t_info2 = load_translation_data.cache_info()
    assert t_info2.hits >= 1
    assert tdata1 == tdata2


