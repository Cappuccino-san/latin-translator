"""API tests, via FastAPI TestClient (no server needed)."""

from fastapi.testclient import TestClient

from latin_nlp.api import app

client = TestClient(app)


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
