# Latin NLP — Structured Latin Natural Language Processing & Translation

A deterministic, rule-based Latin Natural Language Processing pipeline and browser extension that replaces simulated string lookups with a testable, auditable grammar and syntax analyzer.

```
Latin Text
    │
    ├──> 1. Lexer        (Tokenize, normalize macrons, split enclitics: -que, -ve, -ne)
    │
    ├──> 2. Morphology   (Whitaker-style stem + legal endings, reverse-indexing, stemmer fallback)
    │
    ├──> 3. Dictionary   (Curated lexicon in data/lexicon.json with authoritative irregulars)
    │
    ├──> 4. Parser       (Subject agreement, direct object, ablatives, accusative-plus-infinitive)
    │
    └──> 5. Interfaces   (CLI, FastAPI REST API with OpenAPI docs, and Manifest V3 Chrome Extension)
```

---

## Quick Start

```bash
# Set up environment and run tests
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest -q
# 112 passed

# Run CLI commands
python -m latin_nlp.cli analyze "Arma virumque cano"
python -m latin_nlp.cli parse "Puella servum videt"
python -m latin_nlp.cli aeneid --passage all
# Aeneid 1.1-33 coverage: 212/212 = 100%

# Start the REST API server
uvicorn latin_nlp.api:app --reload
# Interactive OpenAPI documentation available at: http://127.0.0.1:8000/docs
```

---

## Examples

### 1. Syntactic Parsing: Subject, Direct Object, Implied Pronouns

```bash
$ python -m latin_nlp.cli parse "Puella servum videt"
Puella servum videt
verb: videt (video)
subject: ['Puella'] -- Nominative Puella agrees in number (singular) with 3rd-person verb videt.
object: ['servum'] -- Accusative servum not governed by a preposition, so read as direct object(s) of videt.
```

```bash
$ python -m latin_nlp.cli parse "Arma virumque cano"
Arma virumque cano
verb: cano (cano)
subject: ['ego (implied, 1st person)'] -- Verb cano is 1 person, so the subject is the implied pronoun, not a nominative noun in the sentence.
object: ['Arma', 'virumque'] -- Accusative Arma, virumque not governed by a preposition, so read as direct object(s) of cano.
```

### 2. Complex Constructions: Accusative-plus-Infinitive & Ablative Absolute

```bash
$ python -m latin_nlp.cli parse "Progeniem sed enim Troiano a sanguine duci audierat"
verb: audierat (audio)
subject: ['ego (implied, 1st person)'] / 3rd-person implied
object: ['Progeniem']
ablative: Troiano a sanguine [ablative of separation / agent] -- a + ablative sanguine.
indirect statement: Accusative subject 'Progeniem' with infinitive 'duci' (accusative-plus-infinitive)
```

```bash
$ python -m latin_nlp.cli parse "Musa, mihi causas memora, quo numine laeso"
verb: memora (memoro)
subject: [] -- Musa is vocative address before comma, never counted as subject.
object: ['causas']
ablative: quo numine laeso [ablative absolute] -- Noun + participle both in the ablative.
```

---

## Architecture

The system is decoupled into isolated, testable pipeline stages:

| Stage | Module | Responsibility |
|---|---|---|
| **Lexer** | `src/latin_nlp/lexer.py` | Tokenization, macron normalization (`canō` $\rightarrow$ `cano`), enclitic splitting (`virumque` $\rightarrow$ `virum` + `que`, `tantaene` $\rightarrow$ `tantae` + `ne`). Knows nothing about grammar. |
| **Morphology** | `src/latin_nlp/morphology.py` | Whitaker-style morphological generation: declensions 1–5, conjugations 1–4, 3rd-declension i-stems (neuter `-ia`/`-i`/`-ium`, m/f `-es`/`-ium`/poetic `-is`), 3rd-declension adjectives, deponent verbs, pluperfects, syncopations (`audierat`), future participles (`venturum`), passive infinitives (`duci`), and reverse indexing. Stemmer fallback handles unseen regular forms of known stems. |
| **Dictionary** | `src/latin_nlp/lexicon.py` | Reads curated JSON lexicon (`data/lexicon.json`). Authoritative irregular forms are checked first and win over generated forms. |
| **Parser** | `src/latin_nlp/parser.py` | Determines grammatical roles: nominative subject (or implied 1st/2nd pronoun), accusative direct objects, ablative constructions (prepositional phrases, ablative absolute, bare ablative of means, time, place), and indirect statements (accusative-plus-infinitive). Explains every decision. |
| **REST API** | `src/latin_nlp/api.py` | FastAPI application exposing `/analyze`, `/parse`, `/lemmatize`, and `/aeneid`. Strict typing via Pydantic schemas in `schemas.py`. |
| **CLI** | `src/latin_nlp/cli.py` | Command-line tool with subcommands `analyze`, `parse`, `lemmatize`, and `aeneid`. |
| **Browser Extension** | `extension/` | Manifest V3 Chrome extension connecting to the local FastAPI core. |

---

## Chrome Extension Setup

The browser extension provides instant morphological lookup and syntax analysis on any webpage:

1. Start the backend: `uvicorn latin_nlp.api:app --reload`
2. Open Google Chrome and navigate to `chrome://extensions`.
3. Enable **Developer mode** (toggle in upper right).
4. Click **Load unpacked** and select the [`extension/`](file:///d:/SN850X/Home/Documents/Projects/latin-translator/latin-translator-main/latin-translator-main/latin-translator-updates/latin-translator/extension) directory.
5. Features:
   - **Popup UI**: Enter Latin phrases to view token morphology tables, grammatical roles, and translation glosses. Add words to a personal vocabulary list (max 100) or review translation history (max 20).
   - **Selection Overlay**: Highlight Latin text on any web page to display a floating syntax overlay with subject, object, and ablative constructions.
   - **Resilience**: If the backend is offline, the extension cleanly directs the user to start `uvicorn` rather than falling back to simulated strings.

---

## Clean Repository Structure

```
latin-translator/
├── .gitignore
├── LICENSE                   (MIT License)
├── pyproject.toml            (Build configuration & dependencies)
├── README.md                 (Project documentation)
├── data/
│   ├── lexicon.json          (Curated vocabulary & stems)
│   └── aeneid/
│       ├── book1_1_11.txt    (Virgil Aeneid Book 1, lines 1–11)
│       └── book1_12_33.txt   (Virgil Aeneid Book 1, lines 12–33)
├── docs/
│   ├── aeneid.md             (Aeneid test corpus documentation & notes)
│   ├── API.md                (REST API specification & endpoint schemas)
│   ├── BENCHMARK.md          (Benchmark methodology & evaluation tables)
│   ├── DESIGN.md             (Design rationale, architecture, and tradeoffs)
│   └── whitaker.md           (Whitaker's Words comparison & import notes)
├── eval/
│   ├── evaluate.py           (Precision/recall & corpus coverage evaluator)
│   └── golden.json           (Golden benchmark set of 130 attested forms)
├── extension/
│   ├── background.js         (Manifest V3 service worker communicating with API)
│   ├── content.js            (In-page selection overlay script)
│   ├── manifest.json         (Manifest V3 configuration with host permissions)
│   ├── popup.html            (Popup interface markup)
│   ├── popup.css             (Popup styles)
│   ├── popup.js              (Popup controller & vocabulary management)
│   ├── README.md             (Extension documentation)
│   └── icons/                (Valid PNG icons: 16px, 48px, 128px)
├── src/
│   └── latin_nlp/
│       ├── __init__.py
│       ├── api.py            (FastAPI application & CORS)
│       ├── cli.py            (Command-line interface)
│       ├── lexer.py          (Lexing & enclitic processing)
│       ├── lexicon.py        (Lexicon loader & models)
│       ├── morphology.py     (Morphological analysis & ending tables)
│       ├── parser.py         (Syntax & dependency parser)
│       ├── pipeline.py       (Pipeline orchestration)
│       └── schemas.py        (Pydantic request & response schemas)
└── tests/
    ├── test_aeneid.py        (Poetry tests: morphology, ablatives, coverage)
    ├── test_api.py           (FastAPI TestClient integration tests)
    └── test_morphology.py    (Unit tests for endings, paradigms, syntax)
```

---

## Test & Benchmark Results

Run the test suite and evaluation scripts directly:

```powershell
# Run all unit and integration tests
.\.venv\Scripts\python.exe -m pytest -q
# 112 passed, 1 warning in 0.52s

# Run the golden benchmark
.\.venv\Scripts\python.exe eval\evaluate.py
# Golden forms: 130/130 correct, 130 analyzed
# Precision: 100.0%  Recall: 100.0%  F1: 100.0%
#   adjectives           8/8
#   aeneid               60/60
#   irregular_verbs      20/20
#   nouns                25/25
#   verbs                17/17

# Run poetry corpus coverage
.\.venv\Scripts\python.exe eval\evaluate.py --aeneid
# Aeneid 1.1-11:   73/73 = 100%   unknown: []
# Aeneid 1.12-33:  139/139 = 100%  unknown: []
# Aeneid 1.1-33:   212/212 = 100%
```

---

## Limitations & Benchmark Caveat

- **In-distribution benchmark**: The 130/130 (100% F1) golden form benchmark and 100% Aeneid coverage are **in-distribution regression tests**. The golden forms and lexicon entries were authored alongside the ending tables. While they verify internal consistency across all paradigms, they do not measure out-of-distribution accuracy on unseen Latin texts.
- **Lexicon scope**: The curated dictionary contains ~195 entries. Unseen lemmas are classified as unknown (0.0 confidence). The stemmer fallback operates only on regular forms derived from known stems.
- **Shallow syntactic parsing**: The parser identifies major syntactic constituents (verb, subject, direct object, prepositional phrases, ablative absolute, ablative of time/place, indirect statements) and explains its decisions. It does not attempt full recursive dependency tree generation for poetic clauses with complex hyperbaton or ellipsis.

---

## Source Credit

- **Virgil's *Aeneid***: Book 1, lines 1–11 and 12–33 text from the **Perseus Digital Library**, *Vergil: Aeneid* (ed. J. B. Greenough, 1900), licensed under [CC BY-SA 3.0 US](https://creativecommons.org/licenses/by-sa/3.0/us/). Publius Vergilius Maro died in 19 BCE; the Latin text is in the public domain.

---

## Repository Cleanup Note

During the upgrade, the repository structure was consolidated:
- Replaced the previous mock/simulated extension engine (which hard-coded only three words—`amo`, `regina`, `aqua`—and fallback strings) with a genuine Manifest V3 client communicating with the FastAPI backend.
- Eliminated redundant nested wrapper directories (`latin-translator-main/latin-translator-main/`, `home/ubuntu/latin_translator_extension`), moving duplicates into an archive directory outside the clean project root.
- Replaced 0-byte placeholders with valid PNG icon files (`icon16.png`, `icon48.png`, `icon128.png`).
- Clarified that checkmarks in older `todo.md` files represented conceptual simulated steps, replacing them with verifiable pytest and evaluation benchmarks.
