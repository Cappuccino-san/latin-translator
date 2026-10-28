"""REST API: FastAPI, typed schemas in schemas.py.

Run:  uvicorn latin_nlp.api:app --reload
Docs: http://127.0.0.1:8000/docs  (OpenAPI, generated from the schemas)

Endpoints:
  GET  /health
  POST /analyze    {text, top_n} -> AnalyzeResponse
  POST /parse      {text} -> ParseResponse
  POST /lemmatize  {word} -> LemmatizeResponse
  GET  /aeneid     -> Aeneid Book 1, lines 1-11, analyzed line by line
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .pipeline import analyze_text, get_analyzer, parse_text
from .schemas import (AeneidLine, AnalyzeRequest, AnalyzeResponse,
                      LemmatizeRequest, LemmatizeResponse, ParseRequest,
                      ParseResponse)

app = FastAPI(title="Latin NLP API", version="0.2.0",
              description="Lexer -> morphology -> dictionary -> parser for Latin. See docs/API.md for typed schemas and examples.")

# CORS middleware for local development (Chrome extension client)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Local development only: browser extensions originate from chrome-extension://
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AENEID_1_11_FILE = Path(__file__).resolve().parents[2] / "data" / "aeneid" / "book1_1_11.txt"
AENEID_12_33_FILE = Path(__file__).resolve().parents[2] / "data" / "aeneid" / "book1_12_33.txt"
AENEID_FILE = AENEID_1_11_FILE


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "engine": "latin-nlp 0.2.0"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    return analyze_text(req.text, top_n=req.top_n)


@app.post("/parse", response_model=ParseResponse)
def parse(req: ParseRequest) -> ParseResponse:
    return parse_text(req.text)


@app.post("/lemmatize", response_model=LemmatizeResponse)
def lemmatize(req: LemmatizeRequest) -> LemmatizeResponse:
    return LemmatizeResponse(word=req.word, analyses=get_analyzer().analyze(req.word))


@app.get("/aeneid", response_model=list[AeneidLine])
def aeneid(passage: str = "1-11") -> list[AeneidLine]:
    target_file = AENEID_12_33_FILE if passage == "12-33" else AENEID_1_11_FILE
    start_line = 12 if passage == "12-33" else 1
    lines = [ln.strip() for ln in target_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
    out: list[AeneidLine] = []
    for i, ln in enumerate(lines, start=start_line):
        out.append(AeneidLine(book=1, line_start=i, line_end=i, latin=ln))
    return out
