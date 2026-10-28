"""Lexical analyzer: stage 1 of the pipeline.

Jobs, and only these jobs:
- split text into tokens, keeping punctuation separate
- normalize macrons (a-macron -> a) for lookup, while keeping the original
- split enclitics -que, -ve, -ne when the remainder is a plausible stem

It does NOT decide part of speech or case. That is morphology's job.
"""

from __future__ import annotations

import re

_MACRONS = str.maketrans({
    "ā": "a", "ē": "e", "ī": "i", "ō": "o", "ū": "u", "ȳ": "y",
    "Ā": "A", "Ē": "E", "Ī": "I", "Ō": "O", "Ū": "U",
})

_TOKEN_RE = re.compile(r"[A-Za-zāēīōūȳĀĒĪŌŪ]+|[.,;:!?()\[\]\"'—-]")


def normalize(word: str) -> str:
    """Lowercase and strip macrons, so cano and canō look up the same way."""
    return word.translate(_MACRONS).lower()


def tokenize(text: str) -> list[str]:
    """Return word/punctuation tokens in order, skipping whitespace."""
    return _TOKEN_RE.findall(text)


def split_enclitic(normalized: str) -> tuple[str, str | None]:
    """Split a trailing enclitic if present.

    Returns (stem_form, enclitic) or (form, None). The caller (morphology)
    decides whether the stem actually analyzes; the lexer only proposes
    the split, it does not validate it.
    """
    for enc in ("que", "ve", "ne"):
        if normalized.endswith(enc) and len(normalized) > len(enc) + 1:
            stem = normalized[: -len(enc)]
            # -ne on tantae -> tantaene: stem tantae is a real form.
            # Avoid splitting words that genuinely end in these letters,
            # e.g. ne (the conjunction itself) or ve as a standalone word.
            if stem not in ("", "n"):
                return stem, enc
    return normalized, None


def is_word(token: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-zāēīōūȳĀĒĪŌŪ]+", token))
