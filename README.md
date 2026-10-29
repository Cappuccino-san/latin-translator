# Latin NLP — Structured Latin Natural Language Processing & Translation

A deterministic, rule-based Latin Natural Language Processing pipeline, web UI, complete Virgil corpus explorer, and browser extension that replaces simulated string lookups with a testable, auditable grammar and syntax analyzer.

```
Latin Text / Virgil Corpus
    │
    ├──> 1. Lexer        (Tokenize, normalize macrons, split enclitics: -que, -ve, -ne)
    │
    ├──> 2. Morphology   (Whitaker-style stem + legal endings, reverse-indexing, stemmer fallback)
    │
    ├──> 3. Dictionary   (Curated lexicon in data/lexicon.json with authoritative irregulars)
    │
    ├──> 4. Parser       (Subject agreement, direct object, ablatives, accusative of duration, AcI)
    │
    └──> 5. Interfaces   (Web UI with Virgil Picker, FastAPI REST API, CLI, and Chrome Extension)
```

---

## Quick Start

```bash
# Set up environment and run tests
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest -q
# 137 passed, 1 warning in 0.82s

# Run CLI commands
python -m latin_nlp.cli analyze "Arma virumque cano"
python -m latin_nlp.cli parse "Puella servum videt"
python -m latin_nlp.cli aeneid --passage all
# Aeneid 1.1-33 coverage: 212/212 = 100%

# Start the Web UI & REST API server
uvicorn latin_nlp.api:app --reload

# Open the Web UI translator in your browser:
# http://127.0.0.1:8000
#
# Interactive OpenAPI documentation:
# http://127.0.0.1:8000/docs
```

---

## Web UI & Virgil Corpus Picker

The application includes an interactive, responsive web interface served directly by FastAPI at `http://127.0.0.1:8000`:

1. **Virgil Corpus Browser (Sentence Picker)**:
   - **Work Selector**: Choose between *Aeneid* (Books I–XII), *Eclogues / Bucolica* (Poems I–X), or *Georgics* (Books I–IV).
   - **Dynamic Book Selector**: Automatically adjusts to the selected work (1–12 for Aeneid, 1–10 for Eclogues, 1–4 for Georgics).
   - **Line Range**: Filter transcript lines by verse range (e.g., lines 1–15).
   - **Interactive Browse Pane**: Displays Latin lines directly from the Perseus edition. Clicking any line instantly loads that verse into the main input and triggers the analysis pipeline.
   - **Load Range Button**: Loads entire multiline passages into the analyzer with a single click.

2. **One-Click "Analyze & Parse"**:
   - Executes both morphological tokenization (`POST /analyze`) and syntactic role assignment (`POST /parse`) concurrently.

3. **Plain-English "Case Explained" Column**:
   The word table features an explicit grammatical explanation column driven directly by the syntactic parser's decisions:
   - **Nominative**: Subject of the finite verb (with number agreement explanation) or predicate nominative.
   - **Accusative**: Direct object of the verb, accusative of duration under *per* (*per multos annos*), object of a preposition (*ad*, *in*), or subject accusative of an indirect statement (*accusativus cum infinitivo*).
   - **Ablative**: Ablative of means/instrument, ablative of separation/agent (*ab oris*), ablative of place where (*aequore toto*), ablative of time (*multis annis*), or ablative absolute (*quo numine laeso*).
   - **Vocative**: Direct address (*Musa*, *Tityre*), never counted as subject or object.
   - **Genitive**: Possession / of-phrase modifying another noun.
   - **Dative**: Indirect object / to/for reference or advantage.

4. **Sequential Word-by-Word Reading Aid**:
   - Displays an inline sequence of every Latin token with its literal dictionary gloss beneath it in natural word order.
   - Labeled explicitly as a **reading aid**, NOT as a fluent English translation.
   - Unknown tokens are cleanly identified as `[unknown]` with `0.00` confidence, never masked by fabricated glosses.

5. **Public-Domain English Translation Section**:
   - Displays authentic, credited public-domain English verse translations for the currently loaded passage (Theodore C. Williams 1910 for *Aeneid*; James Rhoades 1921 for *Eclogues* and *Georgics*).
   - Strict no-hallucination guarantee: when analyzing custom Latin or un-translated lines, the UI displays the exact dictionary gloss sequence clearly labeled: `"Literal gloss - no fluent translation available for this passage"`—with zero invented translation.

6. **Full-Text Bilingual Reader in New Tab (`/virgil/read`)**:
   - Click "Open full passage in new tab" to open an unabridged bilingual reader in a new browser tab.
   - Displays the complete book with line numbers, Latin text, and parallel English translation.
   - Clicking any line or the "Analyze 🔍" link opens that specific verse in the translator analyzer tab. Includes a "Copy" button for each verse.

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

### 2. Complex Constructions: Accusative of Duration, AcI, & Ablative Absolute

```bash
$ python -m latin_nlp.cli parse "multosque per annos errarent"
verb: errarent (erro)
subject: [] -- No nominative token agreeing with 3rd-person verb errarent found; implied.
object: [] -- No ungoverned accusative; errarent is intransitive.
prep phrase: multosque per annos [accusative of duration under per] -- per + accusative annos expresses duration of time ('through/for annos'), not a direct object or ablative of time.
```

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

## Complete Virgil Corpus (`data/virgil/`)

The repository includes the full, unabridged texts of Virgil's major poetic works, split by work, book, and verse line:
- **Aeneid**: Books I–XII (9,897 lines)
- **Eclogues / Bucolica**: Poems I–X (830 lines)
- **Georgics**: Books I–IV (2,188 lines)
- **Total Corpus Size**: 26 files, 12,915 verse lines, 83,612 word tokens.

### REST API Endpoints

- `GET /virgil?work=aeneid&book=1&start=1&end=33` — Fetches verse lines with line numbers and source attribution.
- `GET /virgil/catalog` — Lists all available works, book counts, and line totals.
- `GET /aeneid` — Legacy endpoint for Virgil Aeneid Book 1 introductory passages.
- `POST /analyze` — Lexical tokenization and Whitaker-style morphology.
- `POST /parse` — Syntactic constituent parsing and case role assignment.
- `POST /lemmatize` — Stem and dictionary lookup.
- `GET /health` — Service health and engine version check.

---

## Clean Repository Structure

```
latin-translator/
├── .gitignore
├── LICENSE                   (MIT License)
├── pyproject.toml            (Build configuration & dependencies)
├── README.md                 (Project documentation)
├── web/
│   ├── index.html            (Web UI translator & Virgil picker served at /)
│   └── reader.html           (Bilingual full-text reader served at /virgil/read)
├── data/
│   ├── lexicon.json          (Curated vocabulary & stems)
│   ├── aeneid/
│   │   ├── book1_1_11.txt    (Virgil Aeneid Book 1, lines 1–11)
│   │   └── book1_12_33.txt   (Virgil Aeneid Book 1, lines 12–33)
│   └── virgil/
│       ├── aeneid/           (Books 1–12, 9,897 lines)
│       ├── eclogues/         (Poems 1–10, 830 lines)
│       ├── georgics/         (Books 1–4, 2,188 lines)
│       └── translation/      (Public-domain verse translations: Aeneid, Eclogues, Georgics)
├── docs/
│   ├── aeneid.md             (Aeneid test corpus documentation & notes)
│   ├── API.md                (REST API specification & endpoint schemas)
│   ├── BENCHMARK.md          (Benchmark methodology & evaluation tables)
│   ├── DESIGN.md             (Design rationale, architecture, and tradeoffs)
│   ├── virgil.md             (Complete Virgil corpus metadata & coverage report)
│   └── whitaker.md           (Whitaker's Words comparison & import notes)
├── eval/
│   ├── evaluate.py           (Precision/recall, golden benchmark, and corpus coverage)
│   └── golden.json           (Golden benchmark set of 3,030 attested forms)
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
# 137 passed, 1 warning in 0.82s

# Run the golden benchmark (including 4,400 attested Virgil Batch 1–44 forms)
.\.venv\Scripts\python.exe eval\evaluate.py
# Golden forms: 4530/4530 correct, 4530 analyzed
# Precision: 100.0%  Recall: 100.0%  F1: 100.0%
#   adjectives           8/8
#   aeneid               60/60
#   irregular_verbs      20/20
#   nouns                25/25
#   verbs                17/17
#   virgil_batch1        100/100
#   ...
#   virgil_batch43       100/100
#   virgil_batch44       100/100

# Run poetry corpus coverage on regression baseline
.\.venv\Scripts\python.exe eval\evaluate.py --aeneid
# Aeneid 1.1-11:   73/73 = 100%   unknown: []
# Aeneid 1.12-33:  139/139 = 100%  unknown: []
# Aeneid 1.1-33:   212/212 = 100%

# Run full Virgil corpus coverage report across all 26 books (Batch 1–44 metrics)
.\.venv\Scripts\python.exe eval\evaluate.py --virgil
# Total Aeneid:   60,264 / 63,795 known (94.5%), unknown:  3,531
# Total Eclogues:  5,199 /  5,632 known (92.3%), unknown:    433
# Total Georgics: 13,154 / 14,185 known (92.7%), unknown:  1,031
# GRAND TOTAL:    78,617 / 83,612 known (94.0%), unknown:  4,995
```

---

## Limitations & Benchmark Caveat

- **In-distribution baseline**: The 4530/4530 (100% F1) golden form benchmark and 100% Aeneid 1.1–33 coverage are **in-distribution regression tests**. The golden forms and lexicon entries were authored alongside the ending tables. While they verify internal consistency across all paradigms, they do not measure out-of-distribution accuracy on unseen Latin texts.
- **Coverage vs Parse Accuracy**: Token coverage measures vocabulary recognition and inflection by the lexicon and morphology engine (the percentage of tokens whose lemma and grammatical forms are recognized). It does not imply 100% end-to-end dependency parse or semantic interpretation accuracy on complex poetic syntax.
- **Lexicon scope**: The curated dictionary contains 4,596 verified entries (196 original entries + 4,400 Batch 1–44 verified lemmas). Unseen lemmas are honestly reported as unknown (0.0 confidence). The stemmer fallback operates only on regular forms derived from known stems.
- **Whole-corpus coverage**: Across all 83,612 word tokens of Virgil's hexameter poetry, the 4,596 curated stems recognize **94.0%** of all running tokens (up from 30.6% baseline prior to Batch 1, adding 53,032 recognized tokens overall). Full coverage of arbitrary unseen Latin requires expanding the root dictionary (e.g. from Whitaker's Wordlist) rather than hard-coding fallback guesses.
- **In-Memory Caching & Hardening**: All 26 Virgil book texts and translation JSON files are loaded through thread-safe `@functools.lru_cache` memory caches, preventing repetitive disk I/O. All endpoints strictly validate input bounds, returning clean 400/404 JSON for empty/whitespace input, out-of-range lines, and invalid books without 500 errors.

---

## Source Credit

- **Virgil's Works (*Aeneid*, *Eclogues*, *Georgics*)**: Full Latin texts from the **Perseus Digital Library** (Tufts University), *The Bucolics, Aeneid, and Georgics of Virgil* (ed. J. B. Greenough, Ginn and Company, Boston, 1900), licensed under [CC BY-SA 3.0 US](https://creativecommons.org/licenses/by-sa/3.0/us/). Publius Vergilius Maro died in 19 BCE; the Latin text is in the public domain.
- **English Verse Translations (Public Domain)**:
  - *Aeneid* (Books I–XII): **Theodore C. Williams** (1910), Houghton Mifflin Co., Boston. Digitized by Perseus Digital Library (CC BY-SA 3.0 US).
  - *Eclogues* (Poems I–X) & *Georgics* (Books I–IV): **James Rhoades** (1921), *The Poems of Vergil*, Oxford University Press, London. Digitized by Perseus Digital Library (CC BY-SA 3.0 US).
  - Historic Reference: **John Dryden** (1697), Project Gutenberg #228.
  - See [`docs/virgil.md`](docs/virgil.md) for full metadata.
