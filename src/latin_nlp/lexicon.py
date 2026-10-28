"""Dictionary lookup: stage 3 of the pipeline (conceptually).

Loads the curated Whitaker-style lexicon (data/lexicon.json). Each entry
is a lemma + stem(s); morphology.py does the generation. Irregular forms
in the JSON are authoritative and are checked before generated forms.

Whitaker contract (see docs/whitaker.md): a DICTLINE-style file placed in
data/whitaker/ with lines like ``lemma|pos|stem|...`` can be added later
without changing this loader's public API -- load_lexicon() merges it in
and morphology regenerates from the new stems.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_LEXICON = Path(__file__).resolve().parents[2] / "data" / "lexicon.json"


@dataclass
class Entry:
    lemma: str
    pos: str
    gloss: str = ""
    declension: str | int | None = None
    conjugation: int | None = None
    gender: str | None = None
    stem: str | None = None
    perfect_stem: str | None = None
    supine_stem: str | None = None
    infinitive: str | None = None
    deponent: bool = False
    plural_only: bool = False
    irregular: dict[str, dict] = field(default_factory=dict)


def load_lexicon(path: str | Path | None = None) -> list[Entry]:
    """Load lexicon entries from JSON. Returns entries in file order."""
    p = Path(path) if path else DEFAULT_LEXICON
    data = json.loads(p.read_text(encoding="utf-8"))
    entries: list[Entry] = []
    for raw in data["entries"]:
        entries.append(Entry(
            lemma=raw["lemma"],
            pos=raw["pos"],
            gloss=raw.get("gloss", ""),
            declension=raw.get("decl"),
            conjugation=raw.get("conj"),
            gender=raw.get("gender"),
            stem=raw.get("stem"),
            perfect_stem=raw.get("perfect"),
            supine_stem=raw.get("supine"),
            infinitive=raw.get("infinitive"),
            deponent=bool(raw.get("deponent", False)),
            plural_only=bool(raw.get("plural_only", False)),
            irregular=raw.get("irregular", {}) or {},
        ))
    return entries


def find_entry(entries: list[Entry], lemma: str) -> Entry | None:
    for e in entries:
        if e.lemma.lower() == lemma.lower():
            return e
    return None
