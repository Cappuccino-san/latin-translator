"""CLI: python -m latin_nlp.cli analyze "Arma virumque cano" [--json]
     python -m latin_nlp.cli parse "Puella servum videt"
     python -m latin_nlp.cli lemmatize puellae
     python -m latin_nlp.cli aeneid
     python -m latin_nlp.cli aeneid --book1-lines 1-11
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .pipeline import analyze_text, get_analyzer, parse_text

AENEID_DIR = Path(__file__).resolve().parents[2] / "data" / "aeneid"
AENEID_1_11 = AENEID_DIR / "book1_1_11.txt"
AENEID_12_33 = AENEID_DIR / "book1_12_33.txt"
AENEID_FILE = AENEID_1_11


def _print_token(t):
    a = t.analyses[0] if t.analyses else None
    if not a or a.unknown:
        print(f"  {t.original:<16} ? unknown")
        return
    morph = ", ".join(x for x in [a.case, a.number, a.gender, a.person, a.tense, a.mood, a.voice] if x)
    extra = f" +-{a.enclitic}" if a.enclitic else ""
    print(f"  {t.original:<16} {a.lemma} ({a.pos}) [{morph}] '{a.gloss}'{extra} conf={a.confidence:.2f}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="latin-nlp", description="Structured Latin NLP: lexer -> morphology -> parser")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("analyze"); p.add_argument("text"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("parse"); p.add_argument("text"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("lemmatize"); p.add_argument("word")
    p = sub.add_parser("aeneid")
    p.add_argument("--file", default=None)
    p.add_argument("--passage", choices=["1-11", "12-33", "all"], default="1-11")
    args = parser.parse_args(argv)

    if args.cmd == "analyze":
        res = analyze_text(args.text)
        if args.json:
            print(res.model_dump_json(indent=2)); return 0
        print(f"{args.text}\ncoverage: {res.known_tokens}/{res.known_tokens + res.unknown_tokens} = {res.coverage:.0%}")
        for t in res.tokens:
            if t.analyses:
                _print_token(t)
        return 0
    if args.cmd == "parse":
        res = parse_text(args.text)
        if args.json:
            print(res.model_dump_json(indent=2)); return 0
        print(args.text)
        print(f"verb: {res.verb.form if res.verb else '?'} ({res.verb.lemma if res.verb else ''})")
        print(f"subject: {res.subject} -- {res.subject_explanation}")
        print(f"object: {res.direct_object} -- {res.object_explanation}")
        for ab in res.ablatives:
            print(f"ablative: {' '.join(ab.tokens)} [{ab.kind}] -- {ab.explanation}")
        for ind in res.indirect_statements:
            print(f"indirect statement: subject={ind.subject_accusative}, inf={ind.infinitive} -- {ind.explanation}")
        for pp in res.prepositional_phrases:
            print(f"prep phrase: {' '.join(pp.tokens)} [{pp.kind}] -- {pp.explanation}")
        print("tokens:")
        for t in res.tokens:
            if t.analyses:
                _print_token(t)
        return 0
    if args.cmd == "lemmatize":
        analyzer = get_analyzer()
        for a in analyzer.analyze(args.word):
            morph = ", ".join(x for x in [a.case, a.number, a.gender, a.person, a.tense, a.mood, a.voice] if x)
            print(f"{args.word} -> {a.lemma} ({a.pos}) [{morph}] '{a.gloss}'")
        if not analyzer.analyze(args.word):
            print(f"{args.word}: unknown"); return 1
        return 0
    if args.cmd == "aeneid":
        if args.file:
            text = Path(args.file).read_text(encoding="utf-8")
        elif args.passage == "12-33":
            text = AENEID_12_33.read_text(encoding="utf-8")
        elif args.passage == "all":
            text = AENEID_1_11.read_text(encoding="utf-8") + "\n" + AENEID_12_33.read_text(encoding="utf-8")
        else:
            text = AENEID_1_11.read_text(encoding="utf-8")
        res = analyze_text(text)
        print(text)
        print(f"\ncoverage: {res.known_tokens}/{res.known_tokens + res.unknown_tokens} = {res.coverage:.0%}")
        for t in res.tokens:
            if t.analyses:
                _print_token(t)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
