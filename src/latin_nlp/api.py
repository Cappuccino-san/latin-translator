"""REST API: FastAPI, typed schemas in schemas.py.

Run:  uvicorn latin_nlp.api:app --reload
Docs: http://127.0.0.1:8000/docs  (OpenAPI, generated from the schemas)
UI:   http://127.0.0.1:8000/      (Web translator and Virgil corpus explorer)

Endpoints:
  GET  /               -> Web UI translator page
  GET  /health         -> Service health and engine version
  POST /analyze        {text, top_n} -> AnalyzeResponse
  POST /parse          {text} -> ParseResponse
  POST /lemmatize      {word} -> LemmatizeResponse
  GET  /aeneid         -> Aeneid Book 1 lines, analyzed line by line
  GET  /virgil         ?work=aeneid&book=1&start=1&end=33 -> list[VirgilLine]
  GET  /virgil/catalog -> list[VirgilCatalogWork]
  GET  /virgil/translation ?work=aeneid&book=1&start=1&end=11 -> VirgilTranslationResponse
  GET  /virgil/read    ?work=aeneid&book=1 -> Full-text bilingual reader HTML page
"""

from __future__ import annotations

import functools
import html
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from .pipeline import analyze_text, get_analyzer, parse_text
from .schemas import (AeneidLine, AnalyzeRequest, AnalyzeResponse,
                      LemmatizeRequest, LemmatizeResponse, ParseRequest,
                      ParseResponse, VirgilCatalogWork, VirgilLine,
                      VirgilTranslationLine, VirgilTranslationResponse)

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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    err_msg = exc.errors()[0]["msg"] if exc.errors() else "Validation error"
    return JSONResponse(status_code=400, content={"detail": f"Invalid request: {err_msg}"})

WEB_DIR = Path(__file__).resolve().parents[2] / "web"
INDEX_FILE = WEB_DIR / "index.html"
if not INDEX_FILE.exists():
    INDEX_FILE = Path(__file__).resolve().parent / "web" / "index.html"

READER_FILE = WEB_DIR / "reader.html"
if not READER_FILE.exists():
    READER_FILE = Path(__file__).resolve().parent / "web" / "reader.html"

AENEID_1_11_FILE = Path(__file__).resolve().parents[2] / "data" / "aeneid" / "book1_1_11.txt"
AENEID_12_33_FILE = Path(__file__).resolve().parents[2] / "data" / "aeneid" / "book1_12_33.txt"
AENEID_FILE = AENEID_1_11_FILE

VIRGIL_DIR = Path(__file__).resolve().parents[2] / "data" / "virgil"
VIRGIL_TRANS_DIR = VIRGIL_DIR / "translation"
VIRGIL_WORKS = {
    "aeneid": {"title": "Aeneid", "books": 12, "lines": 9897},
    "eclogues": {"title": "Eclogues", "books": 10, "lines": 830},
    "georgics": {"title": "Georgics", "books": 4, "lines": 2188},
}


@functools.lru_cache(maxsize=64)
def get_virgil_lines(work: str, book: int) -> list[str] | None:
    """In-memory cache for Virgil text lines to eliminate redundant disk reads."""
    book_file = VIRGIL_DIR / work / f"book{book}.txt"
    if not book_file.exists():
        return None
    return book_file.read_text(encoding="utf-8").splitlines()


@functools.lru_cache(maxsize=64)
def load_translation_data(work: str, book: int) -> dict | None:
    """In-memory cache for Virgil aligned translation JSON data."""
    f = VIRGIL_TRANS_DIR / work / f"book{book}.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return None


@functools.lru_cache(maxsize=4)
def get_reader_template() -> str | None:
    """In-memory cache for reader HTML template."""
    if not READER_FILE.exists():
        return None
    return READER_FILE.read_text(encoding="utf-8")


def extract_translation_text(
    data: dict, start: int, end: int
) -> tuple[str | None, list[VirgilTranslationLine]]:
    cards = data.get("cards", [])
    lines_dict = data.get("lines", {})

    extracted_lines: list[VirgilTranslationLine] = []
    for l_no in range(start, end + 1):
        t = lines_dict.get(str(l_no), "")
        extracted_lines.append(VirgilTranslationLine(line=l_no, text=t))

    if start == end:
        txt = lines_dict.get(str(start)) or ""
        return (txt if txt.strip() else None, extracted_lines)

    # Check if cards align with start and end
    covering_cards = [c for c in cards if c.get("start", 1) >= start and c.get("end", 1) <= end]
    if covering_cards and sum(c.get("end", 1) - c.get("start", 1) + 1 for c in covering_cards) >= (end - start + 1) * 0.8:
        card_lines: list[str] = []
        for c in covering_cards:
            card_lines.extend(c.get("lines", []))
        if card_lines:
            return ("\n".join(card_lines), extracted_lines)

    # Otherwise join line translations
    txt = "\n".join(item.text for item in extracted_lines if item.text)
    return (txt if txt.strip() else None, extracted_lines)


@app.get("/", response_class=HTMLResponse)
def index() -> Response:
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE, media_type="text/html")
    return HTMLResponse("<h1>Latin NLP API</h1><p><a href='/docs'>API Documentation</a></p>")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "engine": "latin-nlp 0.2.0"}


MAX_TEXT_LENGTH = 50000
MAX_WORD_LENGTH = 1000


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    if not req.text or not req.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Input text cannot be empty or whitespace."
        )
    if len(req.text) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Input text exceeds maximum length of {MAX_TEXT_LENGTH:,} characters."
        )
    return analyze_text(req.text, top_n=req.top_n)


@app.post("/parse", response_model=ParseResponse)
def parse(req: ParseRequest) -> ParseResponse:
    if not req.text or not req.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Input text cannot be empty or whitespace."
        )
    if len(req.text) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Input text exceeds maximum length of {MAX_TEXT_LENGTH:,} characters."
        )
    return parse_text(req.text)


@app.post("/lemmatize", response_model=LemmatizeResponse)
def lemmatize(req: LemmatizeRequest) -> LemmatizeResponse:
    if not req.word or not req.word.strip():
        raise HTTPException(
            status_code=400,
            detail="Word cannot be empty or whitespace."
        )
    if len(req.word) > MAX_WORD_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Word exceeds maximum length of {MAX_WORD_LENGTH:,} characters."
        )
    return LemmatizeResponse(word=req.word, analyses=get_analyzer().analyze(req.word))


@app.get("/aeneid", response_model=list[AeneidLine])
def aeneid(passage: str = "1-11") -> list[AeneidLine]:
    if passage not in ("1-11", "12-33"):
        raise HTTPException(
            status_code=400,
            detail=f"Passage '{passage}' not supported. Supported passages: '1-11', '12-33'"
        )
    target_file = AENEID_12_33_FILE if passage == "12-33" else AENEID_1_11_FILE
    start_line = 12 if passage == "12-33" else 1
    lines = [ln.strip() for ln in target_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
    out: list[AeneidLine] = []
    for i, ln in enumerate(lines, start=start_line):
        out.append(AeneidLine(book=1, line_start=i, line_end=i, latin=ln))
    return out


@app.get("/virgil/catalog", response_model=list[VirgilCatalogWork])
def virgil_catalog() -> list[VirgilCatalogWork]:
    return [
        VirgilCatalogWork(key=k, title=v["title"], books=v["books"], total_lines=v["lines"])
        for k, v in VIRGIL_WORKS.items()
    ]


@app.get("/virgil", response_model=list[VirgilLine])
def virgil(work: str = "aeneid", book: int = 1, start: int = 1, end: int = 33) -> list[VirgilLine]:
    w = work.strip().lower()
    if w in ("bucolica", "bucolics", "eclogue"):
        w = "eclogues"
    elif w in ("georgic",):
        w = "georgics"
    elif w in ("aeneis",):
        w = "aeneid"

    if w not in VIRGIL_WORKS:
        raise HTTPException(
            status_code=404,
            detail=f"Work '{work}' not found. Available works: {list(VIRGIL_WORKS.keys())}"
        )

    max_books = VIRGIL_WORKS[w]["books"]
    if book < 1 or book > max_books:
        raise HTTPException(
            status_code=404,
            detail=f"Work '{w}' book {book} not found. Available books: 1 to {max_books}"
        )

    if start < 1:
        raise HTTPException(
            status_code=400,
            detail="Start line must be greater than or equal to 1."
        )

    if start > end:
        raise HTTPException(
            status_code=400,
            detail=f"Start line ({start}) cannot be greater than end line ({end})."
        )

    all_lines = get_virgil_lines(w, book)
    if all_lines is None:
        raise HTTPException(
            status_code=404,
            detail=f"Work '{w}' book {book} not found. Available books: 1 to {max_books}"
        )

    total = len(all_lines)
    if start > total:
        raise HTTPException(
            status_code=404,
            detail=f"Start line {start} is out of range. Work '{w}' book {book} has {total} lines."
        )

    s = start
    e = min(total, end)

    out: list[VirgilLine] = []
    for line_no in range(s, e + 1):
        latin_text = all_lines[line_no - 1].strip()
        out.append(VirgilLine(
            work=w,
            book=book,
            line=line_no,
            latin=latin_text,
            source="P. Vergilius Maro (Perseus / Greenough 1900, CC BY-SA 3.0 US)"
        ))
    return out


@app.get("/virgil/translation", response_model=VirgilTranslationResponse)
def virgil_translation(
    work: str = "aeneid", book: int = 1, start: int = 1, end: int = 11
) -> VirgilTranslationResponse:
    if start < 1:
        raise HTTPException(
            status_code=400,
            detail="Start line must be greater than or equal to 1."
        )
    if start > end:
        raise HTTPException(
            status_code=400,
            detail=f"Start line ({start}) cannot be greater than end line ({end})."
        )

    w = work.strip().lower()
    if w in ("bucolica", "bucolics", "eclogue"):
        w = "eclogues"
    elif w in ("georgic",):
        w = "georgics"
    elif w in ("aeneis",):
        w = "aeneid"

    if w not in VIRGIL_WORKS:
        return VirgilTranslationResponse(
            work=work, book=book, start=start, end=end, available=False
        )

    tdata = load_translation_data(w, book)
    if not tdata:
        return VirgilTranslationResponse(
            work=w, book=book, start=start, end=end, available=False
        )

    tot = tdata.get("total_latin_lines", 99999)
    s = max(1, start)
    e = min(tot, end if end >= s else s)
    if s > tot:
        return VirgilTranslationResponse(
            work=w, book=book, start=start, end=end, available=False
        )

    pass_text, lines = extract_translation_text(tdata, s, e)
    if not pass_text and not any(l.text for l in lines):
        return VirgilTranslationResponse(
            work=w, book=book, start=start, end=end, available=False
        )

    return VirgilTranslationResponse(
        work=w,
        book=book,
        start=s,
        end=e,
        translator=tdata.get("translator"),
        year=tdata.get("year"),
        source=tdata.get("source"),
        text=pass_text,
        lines=lines,
        available=True,
    )


@app.get("/virgil/read", response_class=HTMLResponse)
def virgil_read(work: str = "aeneid", book: int = 1) -> HTMLResponse:
    w = work.strip().lower()
    if w in ("bucolica", "bucolics", "eclogue"):
        w = "eclogues"
    elif w in ("georgic",):
        w = "georgics"
    elif w in ("aeneis",):
        w = "aeneid"

    if w not in VIRGIL_WORKS:
        raise HTTPException(
            status_code=404,
            detail=f"Work '{work}' not found. Available works: {list(VIRGIL_WORKS.keys())}"
        )

    max_books = VIRGIL_WORKS[w]["books"]
    if book < 1 or book > max_books:
        raise HTTPException(
            status_code=404,
            detail=f"Work '{w}' book {book} not found. Available books: 1 to {max_books}"
        )

    latin_lines = get_virgil_lines(w, book)
    if latin_lines is None:
        raise HTTPException(
            status_code=404,
            detail=f"Work '{w}' book {book} not found. Available books: 1 to {max_books}"
        )

    template = get_reader_template()
    if not template:
        return HTMLResponse("<h1>Reader template not found</h1>", status_code=500)

    total_lines = len(latin_lines)

    tdata = load_translation_data(w, book)
    trans_lines = tdata.get("lines", {}) if tdata else {}
    translator_name = tdata.get("translator", "Public Domain Translator") if tdata else "Public Domain"
    translator_year = str(tdata.get("year", "")) if tdata else ""
    translator_source = tdata.get("source", "Public Domain") if tdata else ""

    work_title = VIRGIL_WORKS[w]["title"]
    book_label = "Eclogue" if w == "eclogues" else "Book"

    # Build Book options
    max_books = VIRGIL_WORKS[w]["books"]
    book_options_parts = []
    for b_num in range(1, max_books + 1):
        selected_attr = 'selected="selected"' if b_num == book else ""
        book_options_parts.append(f'<option value="{b_num}" {selected_attr}>{book_label} {b_num}</option>')
    book_options_html = "\n".join(book_options_parts)

    # Build rows
    rows_parts = []
    for idx, raw_lat in enumerate(latin_lines, start=1):
        lat = raw_lat.strip()
        eng = trans_lines.get(str(idx), "")
        safe_lat = html.escape(lat)
        safe_eng = html.escape(eng) if eng else '<span style="color: var(--text-dim); font-style: italic;">[No fluent translation available]</span>'
        escaped_js_lat = lat.replace("\\", "\\\\").replace("'", "\\'").replace('"', "&quot;")

        row_html = f"""<tr id="line-{idx}" class="reader-row">
  <td class="cell-num">{idx}</td>
  <td class="cell-latin">
    <a href="/?work={w}&book={book}&start={idx}&end={idx}" target="_blank" title="Click to analyze line {idx} in translator">{safe_lat}</a>
  </td>
  <td class="cell-english">{safe_eng}</td>
  <td class="cell-actions">
    <a href="/?work={w}&book={book}&start={idx}&end={idx}" target="_blank" class="action-btn" title="Analyze line {idx}">Analyze &#x1F50D;</a>
    <button type="button" class="action-btn" onclick="copyLine('{escaped_js_lat}', this)" title="Copy Latin verse">Copy</button>
  </td>
</tr>"""
        rows_parts.append(row_html)

    rows_html = "\n".join(rows_parts)

    title_str = f"{work_title} {book_label} {book}"
    rendered = template.replace("{{TITLE}}", title_str)
    rendered = rendered.replace("{{WORK_TITLE}}", work_title)
    rendered = rendered.replace("{{BOOK_LABEL}}", book_label)
    rendered = rendered.replace("{{BOOK_NUM}}", str(book))
    rendered = rendered.replace("{{TOTAL_LINES}}", str(total_lines))
    rendered = rendered.replace("{{TRANSLATOR_NAME}}", html.escape(translator_name))
    rendered = rendered.replace("{{TRANSLATOR_YEAR}}", html.escape(translator_year))
    rendered = rendered.replace("{{TRANSLATOR_SOURCE}}", html.escape(translator_source))
    rendered = rendered.replace("{{BOOK_OPTIONS}}", book_options_html)
    rendered = rendered.replace("{{ROWS_HTML}}", rows_html)
    rendered = rendered.replace("{{AENEID_SELECTED}}", 'selected="selected"' if w == "aeneid" else "")
    rendered = rendered.replace("{{ECLOGUES_SELECTED}}", 'selected="selected"' if w == "eclogues" else "")
    rendered = rendered.replace("{{GEORGICS_SELECTED}}", 'selected="selected"' if w == "georgics" else "")

    return HTMLResponse(content=rendered, status_code=200)

