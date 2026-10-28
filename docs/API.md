# API documentation

Base: run `uvicorn latin_nlp.api:app --reload`, then open
`http://127.0.0.1:8000/docs` for interactive OpenAPI docs. All
schemas below are the Pydantic models in `src/latin_nlp/schemas.py`.

## GET /health

```json
{"status": "ok", "engine": "latin-nlp 0.2.0"}
```

## POST /analyze

Request (`AnalyzeRequest`):

```json
{"text": "Puella servum videt", "top_n": 3}
```

Response (`AnalyzeResponse`):

```json
{
  "text": "Puella servum videt",
  "tokens": [
    {"original": "Puella", "normalized": "puella",
     "analyses": [{"form": "puella", "lemma": "puella", "pos": "noun",
       "gloss": "girl", "case": "nominative", "number": "singular",
       "gender": "f", "confidence": 0.95, "unknown": false}]}
  ],
  "known_tokens": 3, "unknown_tokens": 0, "coverage": 1.0
}
```

`TokenAnalysis` fields: `form, lemma, pos, gloss, case, number,
gender, person, tense, mood, voice, confidence, enclitic, unknown`.
Fields that do not apply to a part of speech are `null`
(a noun has no tense; a verb has no case, except participles, which
have both — a participle is a verb form declined like an adjective).

Unknown words return one analysis with `pos: "unknown"`,
`confidence: 0.0`, `unknown: true`, and `lemma` equal to the
normalized form. They are never guessed.

## POST /parse

Request: `{"text": "Puella servum videt"}`

Response (`ParseResponse`):

```json
{
  "text": "Puella servum videt",
  "verb": {"form": "videt", "lemma": "video", "pos": "verb",
    "person": "3", "number": "singular", "tense": "present",
    "mood": "indicative", "voice": "active", "confidence": 0.95},
  "subject": ["Puella"],
  "subject_explanation": "Nominative Puella agrees in number (singular) with 3rd-person verb videt.",
  "direct_object": ["servum"],
  "object_explanation": "Accusative servum not governed by a preposition, so read as direct object(s) of videt.",
  "ablatives": [],
  "tokens": []
}
```

`AblativeConstruction`: `tokens` (e.g. `["cum", "servo"]` or
`["numine", "laeso"]`), `kind` (e.g. `"ablative of accompaniment"`,
`"ablative absolute"`, `"ablative of means / instrument / separation"`),
`explanation` (the rule used).

## POST /lemmatize

Request: `{"word": "puellae"}` — response is all analyses of that
one form, best first. Use this to inspect ambiguity: `puellae` will
return genitive singular, dative singular, and nominative plural
readings.

## GET /aeneid

Returns Aeneid Book 1, lines 1–11, as a list of `AeneidLine`:
`book, line_start, line_end, latin, source`. It returns the text,
not the analysis — pipe a line into `/analyze` or `/parse` to
analyze it. That separation keeps the endpoint cacheable and the
analysis endpoint single-purpose.
