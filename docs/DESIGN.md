# Design

## Why Python, when the old repo was JavaScript?

The old repo was a browser extension in JS. The roadmap asks for a
CLI + REST API + pytest/vitest, and the author's other two pinned
repos are Python/FastAPI. Python is also the language he can explain
in an interview. So the new core is Python/FastAPI/pytest, and the
extension becomes a client of the API, not the engine. If a
TypeScript port is wanted later, the pipeline stages and the
lexicon JSON port 1:1 — the design, not the language, is the point.

## Pipeline stages, decoupled

- `lexer.py` knows nothing about Latin grammar. It tokenizes,
  normalizes macrons, and proposes enclitic splits.
- `morphology.py` knows endings, not sentences. It generates forms
  from stems and reverse-indexes them. Irregular forms are checked
  first, generated forms second, stemmer fallback third.
- `lexicon.py` knows data, not rules. Adding a lemma is adding a
  JSON entry with a stem; no code change.
- `parser.py` knows sentences, not endings. It reads only the
  analyses and applies agreement + preposition rules, and it
  explains each decision in the response.

A stage can be tested alone: lexer tests need no dictionary,
morphology tests need no parser, parser tests can use hand-built
token analyses.

## Whitaker-style, not Whitaker

William Whitaker's WORDS works from STEMLIST + INFLECTS: a stem,
plus a table of legal endings for its paradigm. This project does
the same thing, in miniature, with `data/lexicon.json` as the stem
list and the ending tables in `morphology.py`. The full Whitaker
dataset (SourceForge `wordsall.zip`: DICTLINE.GEN, STEMLIST.GEN,
INFLECTS.LAT) is freely available for any purpose, per its own
documentation, but it is not bundled here — it is large, in Ada-era
formats, and bundling it would hide which forms this project
actually claims to handle. See `docs/whitaker.md` for the import
contract that would be needed to claim Whitaker-scale coverage.

## Ambiguity is a feature, not a bug

Latin is highly syncretic: `puella` is nominative, ablative, and
vocative singular; `puellae` is three different readings. An
analyzer that returns one answer is lying about one of them. So
`analyze()` returns all readings, and the parser disambiguates
only where it has evidence: verb person/number agreement, a
preceding preposition, a comma before an imperative (vocative).
Where it has no evidence, it says so in the explanation field.

## What is not built, and why

- No statistical tagger, no neural model. The point of this repo
  is deterministic, auditable morphology — the same reason the
  author's Workflow-Orchestrator uses rules, not an LLM, for
  priority. A model would hide exactly the decisions an interviewer
  will ask about.
- No full dependency tree. Latin free word order + poetry ellipsis
  makes a full tree a research project, not a portfolio upgrade.
  Subject / object / ablative with stated rules is the honest
  scope, and it is what the roadmap asked for.
- No English sentence translation. Glosses are headwords; turning
  a parse into fluent English is a separate (and much harder)
  generation problem.
