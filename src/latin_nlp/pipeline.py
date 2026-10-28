"""Pipeline: wires lexer -> morphology -> (dictionary) -> parser, in order.

analyze_text() runs stages 1-3. parse_text() runs all four stages.
Neither stage reaches into another stage's internals: the lexer
returns tokens, morphology returns analyses, the parser reads only
those analyses.
"""

from __future__ import annotations

from .lexer import is_word, normalize, tokenize
from .morphology import MorphAnalyzer
from .parser import parse_tokens
from .schemas import AnalyzeResponse, ParseResponse, TokenAnalysis, TokenResult

_ANALYZER: MorphAnalyzer | None = None


def get_analyzer() -> MorphAnalyzer:
    global _ANALYZER
    if _ANALYZER is None:
        _ANALYZER = MorphAnalyzer()
    return _ANALYZER


def analyze_tokens(text: str, analyzer: MorphAnalyzer | None = None) -> list[TokenResult]:
    analyzer = analyzer or get_analyzer()
    out: list[TokenResult] = []
    for tok in tokenize(text):
        if not is_word(tok):
            out.append(TokenResult(original=tok, normalized=tok, analyses=[]))
            continue
        analyses = analyzer.analyze(tok)
        if not analyses:
            analyses = [TokenAnalysis(form=normalize(tok), lemma=normalize(tok),
                                      pos="unknown", gloss="", confidence=0.0, unknown=True)]
        out.append(TokenResult(original=tok, normalized=normalize(tok), analyses=analyses))
    return out


def analyze_text(text: str, top_n: int = 3) -> AnalyzeResponse:
    tokens = analyze_tokens(text)
    for t in tokens:
        t.analyses = t.analyses[:top_n]
    word_tokens = [t for t in tokens if is_word(t.original)]
    known = sum(1 for t in word_tokens if t.analyses and not t.analyses[0].unknown)
    unknown = len(word_tokens) - known
    coverage = (known / len(word_tokens)) if word_tokens else 0.0
    return AnalyzeResponse(text=text, tokens=tokens, known_tokens=known,
                           unknown_tokens=unknown, coverage=coverage)


def parse_text(text: str) -> ParseResponse:
    tokens = analyze_tokens(text)
    return parse_tokens(text, tokens)
