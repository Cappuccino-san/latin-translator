"""Benchmark: precision / recall on inflected vocabulary and Virgil coverage.

Usage:  python eval/evaluate.py [--golden eval/golden.json]
        python eval/evaluate.py --aeneid
        python eval/evaluate.py --virgil [--work aeneid|eclogues|georgics]

For each golden form, the analyzer is correct if ANY analysis matches
the expected lemma and the expected morphology field(s). This is
precision/recall over forms, not over tokens in running text:
  precision = correct / analyzed (forms the analyzer claimed)
  recall    = correct / total golden forms
  F1        = harmonic mean

The --aeneid mode reports token coverage on Aeneid 1.1-11 and 1.12-33 separately.
The --virgil mode reports token coverage across all works of Virgil by book.
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


def evaluate_virgil(target_work: str | None = None) -> dict:
    virgil_dir = ROOT / "data" / "virgil"
    works = ["aeneid", "eclogues", "georgics"]
    if target_work and target_work.lower() in works:
        works = [target_work.lower()]

    results: dict[str, dict] = {}
    grand_total = grand_known = grand_unknown = 0

    for work in works:
        work_dir = virgil_dir / work
        if not work_dir.exists():
            continue
        files = sorted(work_dir.glob("book*.txt"), key=lambda p: int("".join(filter(str.isdigit, p.stem))))
        work_total = work_known = work_unknown = 0
        book_stats = []

        for f in files:
            b_num = int("".join(filter(str.isdigit, f.stem)))
            text = f.read_text(encoding="utf-8")
            res = analyze_text(text)
            tot = res.known_tokens + res.unknown_tokens
            work_total += tot
            work_known += res.known_tokens
            work_unknown += res.unknown_tokens
            book_stats.append({
                "book": b_num,
                "lines": len(text.splitlines()),
                "total_tokens": tot,
                "known_tokens": res.known_tokens,
                "unknown_tokens": res.unknown_tokens,
                "coverage": res.coverage
            })

        cov = work_known / work_total if work_total else 0.0
        results[work] = {
            "total_tokens": work_total,
            "known_tokens": work_known,
            "unknown_tokens": work_unknown,
            "coverage": cov,
            "books": book_stats
        }
        grand_total += work_total
        grand_known += work_known
        grand_unknown += work_unknown

    results["corpus_total"] = {
        "total_tokens": grand_total,
        "known_tokens": grand_known,
        "unknown_tokens": grand_unknown,
        "coverage": grand_known / grand_total if grand_total else 0.0
    }
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default=str(ROOT / "eval" / "golden.json"))
    ap.add_argument("--aeneid", action="store_true")
    ap.add_argument("--virgil", action="store_true")
    ap.add_argument("--work", choices=["aeneid", "eclogues", "georgics"], default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.virgil:
        v_res = evaluate_virgil(args.work)
        if args.json:
            print(json.dumps(v_res, indent=2))
            return 0
        print("=================================================================")
        print("VIRGIL CORPUS COVERAGE REPORT (Perseus / Greenough 1900 Edition)")
        print("=================================================================")
        for work, data in v_res.items():
            if work == "corpus_total":
                continue
            print(f"\n--- {work.upper()} ---")
            for b in data["books"]:
                print(f"  Book {b['book']:>2} ({b['lines']:>3} lines): {b['known_tokens']:>4} / {b['total_tokens']:>4} known ({b['coverage']:>5.1%}), unknown: {b['unknown_tokens']:>4}")
            print(f"Total {work.capitalize()}: {data['known_tokens']} / {data['total_tokens']} known ({data['coverage']:.1%}), unknown: {data['unknown_tokens']}")
        total = v_res["corpus_total"]
        print("\n-----------------------------------------------------------------")
        print(f"GRAND TOTAL VIRGIL: {total['known_tokens']} / {total['total_tokens']} tokens known ({total['coverage']:.1%}), unknown: {total['unknown_tokens']}")
        print("-----------------------------------------------------------------")
        lex_count = len(get_analyzer().entries)
        print(f"Note: The curated lexicon contains {lex_count:,} core entries (with Batches 1-44). Coverage reflects")
        print("real Whitaker-style lexical coverage on unabridged hexameter poetry.")
        return 0

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
