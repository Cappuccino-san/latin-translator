"""Benchmark: precision / recall on inflected vocabulary.

Usage:  python eval/evaluate.py [--golden eval/golden.json]
        python eval/evaluate.py --aeneid

For each golden form, the analyzer is correct if ANY analysis matches
the expected lemma and the expected morphology field(s). This is
precision/recall over forms, not over tokens in running text:
  precision = correct / analyzed (forms the analyzer claimed)
  recall    = correct / total golden forms
  F1        = harmonic mean
Unknown forms count against recall, not precision, and are listed
separately so a coverage gap is not hidden inside a precision number.

The --aeneid mode reports token coverage on Aeneid 1.1-11 separately,
because poetry coverage and dictionary-form accuracy are different
claims and should not be averaged together.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from latin_nlp.pipeline import analyze_text, get_analyzer  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def evaluate(golden_path: Path) -> dict:
    analyzer = get_analyzer()
    cases = json.loads(golden_path.read_text(encoding="utf-8"))
    by_cat: dict[str, dict[str, int]] = {}
    correct = analyzed = 0
    misses: list[str] = []
    for case in cases:
        cat = case.get("category", "other")
        by_cat.setdefault(cat, {"total": 0, "correct": 0})
        by_cat[cat]["total"] += 1
        analyses = analyzer.analyze(case["form"])
        ok = False
        if analyses:
            analyzed += 1
            for a in analyses:
                if a.lemma != case["expected_lemma"]:
                    continue
                if case.get("expected_case") and a.case != case["expected_case"]:
                    continue
                if case.get("expected_tense") and a.tense != case["expected_tense"]:
                    continue
                if case.get("expected_mood") and a.mood != case["expected_mood"]:
                    continue
                if case.get("expected_pos") and a.pos != case["expected_pos"]:
                    continue
                ok = True
                break
        if ok:
            correct += 1
            by_cat[cat]["correct"] += 1
        else:
            misses.append(f"{case['form']} -> expected {case['expected_lemma']} {case.get('expected_case') or case.get('expected_tense') or ''} (got {[a.lemma for a in analyses][:3]})")
    total = len(cases)
    precision = correct / analyzed if analyzed else 0.0
    recall = correct / total if total else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"total": total, "correct": correct, "analyzed": analyzed,
            "precision": precision, "recall": recall, "f1": f1,
            "by_category": by_cat, "misses": misses}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default=str(ROOT / "eval" / "golden.json"))
    ap.add_argument("--aeneid", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.aeneid:
        p1 = ROOT / "data" / "aeneid" / "book1_1_11.txt"
        p2 = ROOT / "data" / "aeneid" / "book1_12_33.txt"

        res1 = analyze_text(p1.read_text(encoding="utf-8")) if p1.exists() else None
        res2 = analyze_text(p2.read_text(encoding="utf-8")) if p2.exists() else None

        out: dict = {}
        tot1 = tot2 = comb_tot = comb_known = 0
        if res1:
            tot1 = res1.known_tokens + res1.unknown_tokens
            unk1 = [t.original for t in res1.tokens if t.analyses and t.analyses[0].unknown]
            out["aeneid_1_1_11"] = {
                "tokens": tot1,
                "known": res1.known_tokens,
                "unknown": res1.unknown_tokens,
                "coverage": res1.coverage,
                "unknown_forms": unk1,
            }
        if res2:
            tot2 = res2.known_tokens + res2.unknown_tokens
            unk2 = [t.original for t in res2.tokens if t.analyses and t.analyses[0].unknown]
            out["aeneid_1_12_33"] = {
                "tokens": tot2,
                "known": res2.known_tokens,
                "unknown": res2.unknown_tokens,
                "coverage": res2.coverage,
                "unknown_forms": unk2,
            }
        if res1 and res2:
            comb_known = res1.known_tokens + res2.known_tokens
            comb_tot = tot1 + tot2
            out["aeneid_1_1_33_total"] = {
                "tokens": comb_tot,
                "known": comb_known,
                "unknown": res1.unknown_tokens + res2.unknown_tokens,
                "coverage": comb_known / comb_tot if comb_tot else 0.0,
            }

        if args.json:
            print(json.dumps(out, indent=2))
        else:
            if res1:
                print(f"Aeneid 1.1-11:   {res1.known_tokens}/{tot1} = {res1.coverage:.0%}  unknown: {out['aeneid_1_1_11']['unknown_forms']}")
            if res2:
                print(f"Aeneid 1.12-33:  {res2.known_tokens}/{tot2} = {res2.coverage:.0%}  unknown: {out['aeneid_1_12_33']['unknown_forms']}")
            if res1 and res2:
                print(f"Aeneid 1.1-33:   {comb_known}/{comb_tot} = {out['aeneid_1_1_33_total']['coverage']:.0%}")
        return 0

    res = evaluate(Path(args.golden))
    if args.json:
        print(json.dumps(res, indent=2))
        return 0
    print(f"Golden forms: {res['correct']}/{res['total']} correct, {res['analyzed']} analyzed")
    print(f"Precision: {res['precision']:.1%}  Recall: {res['recall']:.1%}  F1: {res['f1']:.1%}")
    for cat, v in sorted(res["by_category"].items()):
        print(f"  {cat:<20} {v['correct']}/{v['total']}")
    if res["misses"]:
        print("Misses:")
        for m in res["misses"]:
            print(f"  - {m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
