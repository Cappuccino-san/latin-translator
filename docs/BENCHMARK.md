# Benchmark report

Run: `.venv/bin/python eval/evaluate.py` (and `--aeneid` for poetry coverage)

## Curated golden set — 2026-10-28

| Category | Correct / Total |
|---|---|
| nouns | 25 / 25 |
| adjectives | 8 / 8 |
| verbs (regular) | 17 / 17 |
| irregular verbs | 20 / 20 |
| Aeneid forms (lines 1–33) | 60 / 60 |
| **Total** | **130 / 130** |
| Precision | 100.0% |
| Recall | 100.0% |
| F1 | 100.0% |

## Aeneid 1.1–33 coverage

| Metric | Lines 1.1–11 | Lines 1.12–33 | Combined (1.1–33) |
|---|---|---|---|
| Word tokens | 73 | 139 | 212 |
| Known | 73 | 139 | 212 |
| Unknown | 0 | 0 | 0 |
| Coverage | 100% | 100% | 100% |

## How to read these numbers

Both numbers are **in-distribution**: the golden set and the
Aeneid lexicon entries were built together with the analyzer.
They prove the generator, the lexicon, and the tests agree with
each other — a regression suite, not a generalization claim.

A generalization benchmark would need:

- A held-out form list drawn from a source the tables were not
  tuned on (e.g. a random Whitaker sample, see `docs/whitaker.md`).
- Reporting precision (of forms the analyzer *claimed*) and recall
  (of all gold forms) separately, with unknown forms listed, not
  averaged away.
- Per-paradigm breakdowns, because 1st-declension nouns and
  irregular verbs fail for different reasons and need different fixes.

Until that exists, the honest one-line summary for a resume or
interview is: "Curated golden set of 130 inflected forms, 130/130 (100% P/R/F1),
plus 100% token coverage across 212 tokens of Aeneid 1.1–33; both are
in-distribution regression tests, not held-out accuracy."
