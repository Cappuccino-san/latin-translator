# Testing with Virgil's Aeneid

## Sources

- `data/aeneid/book1_1_11.txt` — Aeneid Book 1, lines 1–11:
  > Arma virumque cano, Troiae qui primus ab oris …
- `data/aeneid/book1_12_33.txt` — Aeneid Book 1, lines 12–33:
  > Urbs antiqua fuit, Tyrii tenuere coloni …
  > Tantae molis erat Romanam condere gentem.

Text: Perseus Digital Library, Greenough 1900 edition, licensed
CC BY-SA 3.0 US. Virgil (P. Vergilius Maro) died in 19 BCE, so the
Latin text itself is public domain; the Perseus edition is credited
here and in the API's `source` field. No modern translation is
bundled — only the Latin lines.

## How to use it

```bash
.venv/bin/python -m latin_nlp.cli aeneid
.venv/bin/python eval/evaluate.py --aeneid
# -> Aeneid 1.1-11:   73/73 = 100%
# -> Aeneid 1.12-33:  139/139 = 100%
# -> Aeneid 1.1-33:   212/212 = 100%
.venv/bin/python -m pytest tests/test_aeneid.py -q
```

## What the tests actually assert

- Token coverage on all 73 word tokens in lines 1–11 and 139 word tokens in lines 12–33 (212 tokens total).
- First-line morphology: `arma` (acc. pl.), `virumque`
  (acc. sg. + `-que`), `cano` (1st sg. present), `Troiae`
  (gen. sg.), `oris` (abl. pl., forced by `ab`), `Italiam`
  (acc. sg.), `fato` (bare ablative), `venit`, `litora`.
- Participles & Deponents: `iactatus`, `passus` (deponent), `laeso`, `dolens`, `venturum` (future active participle), `repostum`.
- 3rd-declension i-stems & adjectives: `maria` (neuter pl.), `arces`, `gentibus`, `molis`, `immitis`, `omnia`.
- Pluperfect & Poetic Syncopation: `audierat` (pluperfect syncopated from audiverat), `gesserat`, `exciderant`, `tenuere` (poetic 3rd pl. perfect in -ere).
- Accusative-plus-Infinitive (Indirect Statement): `Progeniem duci audierat`.
- Ablative constructions:
  - Ablative absolute: `quo numine laeso`, `posthabita Samo`.
  - Ablative of separation: `ab oris`.
  - Ablative of place where: `aequore toto`, `alta mente`.
  - Invocation address: `Musa, mihi causas memora` — vocative is not a subject, `causas` is the object.

## Caveat, stated plainly

Coverage on lines 1–33 is 100% because the curated lexicon was
expanded specifically to handle the vocabulary in these lines.
That is useful as a regression test (a change that breaks Virgil
is caught immediately), but it is in-distribution and not evidence
the engine handles arbitrary unseen Virgil without extending the
lexicon entries.
