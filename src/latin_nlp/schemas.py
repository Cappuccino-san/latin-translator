"""Typed request/response schemas for the CLI and REST API.

Every boundary uses these models, never raw dicts. This is the contract
a downstream system (or the browser extension) can code against.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="Latin text to analyze")
    top_n: int = Field(3, ge=1, le=10, description="Analyses kept per token")


class TokenAnalysis(BaseModel):
    form: str
    lemma: str
    pos: str
    gloss: str = ""
    case: str | None = None
    number: str | None = None
    gender: str | None = None
    person: str | None = None
    tense: str | None = None
    mood: str | None = None
    voice: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    enclitic: str | None = None
    unknown: bool = False


class TokenResult(BaseModel):
    original: str
    normalized: str
    analyses: list[TokenAnalysis] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    text: str
    tokens: list[TokenResult]
    known_tokens: int
    unknown_tokens: int
    coverage: float


class AblativeConstruction(BaseModel):
    tokens: list[str]
    kind: str
    explanation: str


class IndirectStatement(BaseModel):
    subject_accusative: str
    infinitive: str
    head_verb: str | None = None
    explanation: str = "Accusative subject with infinitive verb forming an indirect statement (oratio obliqua)."


class PrepositionalPhrase(BaseModel):
    tokens: list[str]
    preposition: str
    case: str
    kind: str
    explanation: str


class ParseResponse(BaseModel):
    text: str
    verb: TokenAnalysis | None = None
    subject: list[str] = Field(default_factory=list)
    subject_explanation: str = ""
    direct_object: list[str] = Field(default_factory=list)
    object_explanation: str = ""
    ablatives: list[AblativeConstruction] = Field(default_factory=list)
    indirect_statements: list[IndirectStatement] = Field(default_factory=list)
    prepositional_phrases: list[PrepositionalPhrase] = Field(default_factory=list)
    tokens: list[TokenResult] = Field(default_factory=list)


class ParseRequest(BaseModel):
    text: str = Field(..., description="Latin text to parse")


class LemmatizeRequest(BaseModel):
    word: str = Field(..., description="Latin word to lemmatize")


class LemmatizeResponse(BaseModel):
    word: str
    analyses: list[TokenAnalysis] = Field(default_factory=list)


class AeneidLine(BaseModel):
    book: int
    line_start: int
    line_end: int
    latin: str
    source: str = "Vergil, Aeneid 1 (Perseus / Greenough 1900, CC BY-SA 3.0 US)"


class VirgilLine(BaseModel):
    work: str
    book: int
    line: int
    latin: str
    source: str = "P. Vergilius Maro (Perseus / Greenough 1900, CC BY-SA 3.0 US)"


class VirgilCatalogWork(BaseModel):
    key: str
    title: str
    books: int
    total_lines: int


class VirgilTranslationLine(BaseModel):
    line: int
    text: str


class VirgilTranslationResponse(BaseModel):
    work: str
    book: int
    start: int
    end: int
    translator: str | None = None
    year: int | None = None
    source: str | None = None
    text: str | None = None
    lines: list[VirgilTranslationLine] = Field(default_factory=list)
    available: bool = False


class BenchmarkEntry(BaseModel):
    form: str
    expected_lemma: str
    expected_pos: str
    expected_case: str | None = None
    expected_tense: str | None = None
    expected_mood: str | None = None
    category: str = ""
