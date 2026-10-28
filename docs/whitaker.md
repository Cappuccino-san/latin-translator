# Whitaker's Words — what is used, what is not

William Whitaker's WORDS (v1.97) is a Latin-to-English dictionary
program whose source and data are, per its own documentation,
"freely available to anyone who wishes to use them, for whatever
purpose." The distribution (`wordsall.zip` on SourceForge) contains:

- `DICTLINE.GEN` — dictionary lines (lemma + paradigm + gloss)
- `STEMLIST.GEN` — stems
- `INFLECTS.LAT` — inflection ending tables
- `UNIQUES.LAT`, `ADDONS.LAT` — irregulars and special forms

## What this project does

It implements Whitaker's *method* (stem + legal ending table,
irregulars first) with a curated stem list, not Whitaker's dataset.
That is a deliberate scope choice, documented in `docs/DESIGN.md`.

## What importing Whitaker would take

1. Parse `DICTLINE.GEN` into the `data/lexicon.json` entry format
   (lemma, pos, declension/conjugation, stem, gloss, irregulars).
   The format is Ada-era fixed-width text, not JSON, so this is a
   real parser, not a copy.
2. Map Whitaker's paradigm codes to the ending tables in
   `morphology.py`, and add the paradigms this project does not
   yet generate (deponents in full, 3rd-declension i-stems,
   comparatives/superlatives, etc.).
3. Re-run `eval/evaluate.py` on a *held-out* sample of Whitaker
   forms (forms not used to build the tables) and report that
   number separately from the curated golden set. That held-out
   number is the one that could honestly be called
   "precision/recall on inflected vocabulary" at Whitaker scale.

Until step 3 is done, do not quote the curated 102/102 benchmark
as Whitaker-scale accuracy. See `docs/BENCHMARK.md`.
