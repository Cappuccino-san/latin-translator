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

## GET /virgil/catalog

Returns all works in the Virgil corpus with metadata:

```json
[
  {"key": "aeneid", "title": "Aeneid", "books": 12, "total_lines": 9897},
  {"key": "eclogues", "title": "Eclogues", "books": 10, "total_lines": 830},
  {"key": "georgics", "title": "Georgics", "books": 4, "total_lines": 2188}
]
```

## GET /virgil

Fetch transcript lines from the Virgil corpus:

Query Parameters:
- `work`: `aeneid` (default), `eclogues`, or `georgics`
- `book`: Book/Poem number (1..12)
- `start`: Start line (default 1)
- `end`: End line (default 33)

Response: list of `VirgilLine`:
```json
[
  {
    "work": "aeneid",
    "book": 1,
    "line": 1,
    "latin": "Arma virumque cano, Troiae qui primus ab oris",
    "source": "P. Vergilius Maro (Perseus / Greenough 1900, CC BY-SA 3.0 US)"
  }
]
```

## GET /virgil/translation

Fetch aligned public-domain English translation for a given work, book, and line range:

Query Parameters:
- `work`: `aeneid`, `eclogues`, or `georgics`
- `book`: Book/Poem number
- `start`: Start line
- `end`: End line

Response (`VirgilTranslationResponse`):
```json
{
  "work": "aeneid",
  "book": 1,
  "start": 1,
  "end": 1,
  "translator": "Theodore C. Williams",
  "year": 1910,
  "source": "Perseus Digital Library / Houghton Mifflin Co. (1910)",
  "text": "Arms and the man I sing, who first made way,",
  "lines": [
    {"line": 1, "text": "Arms and the man I sing, who first made way,"}
  ],
  "available": true
}
```

If no public-domain translation is available or the work/range is invalid, returns:
`{"available": false, "text": null, "lines": []}`

## GET /virgil/read

Renders the full-text bilingual reader HTML view for an entire book:

Query Parameters:
- `work`: `aeneid`, `eclogues`, or `georgics`
- `book`: Book number (e.g. 1)

Response: `text/html` page featuring line numbers, Latin verse, parallel English translation, quick "Analyze 🔍" link to open that verse in the translator analyzer, and a "Copy" button.

---

## Error Handling & Validation Contract

All endpoints strictly validate inputs and return typed JSON error responses (`{"detail": "..."}`), never a 500 error or stack trace:

| Status Code | Cause | Example Trigger |
|:---:|:---|:---|
| **400 Bad Request** | Empty or whitespace-only input | `POST /analyze` with `{"text": "   "}` |
| **400 Bad Request** | Exceeds maximum length (50k chars) | `POST /analyze` with >50,000 characters |
| **400 Bad Request** | Inverted line range (`start > end`) | `GET /virgil?start=20&end=10` |
| **400 Bad Request** | Negative or zero line index (`start < 1`) | `GET /virgil?start=0` |
| **400 Bad Request** | Unsupported passage selector | `GET /aeneid?passage=34-50` |
| **404 Not Found** | Invalid or uncataloged work | `GET /virgil?work=iliad` |
| **404 Not Found** | Book out of range for work | `GET /virgil?work=aeneid&book=99` |
| **404 Not Found** | Start line beyond book end | `GET /virgil?work=aeneid&book=1&start=1000` |

### High-Performance In-Memory Caching

All 26 Virgil Latin books and aligned translation files are cached in memory using `@functools.lru_cache`:
- `get_virgil_lines(work, book)`: Caches all parsed text lines per book (0ms disk latency after first access).
- `load_translation_data(work, book)`: Caches parsed translation JSON cards and line maps.
- `get_reader_template()`: Caches reader HTML template.

