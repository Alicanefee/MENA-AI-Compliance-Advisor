"""AI-assisted transcription of PDFs whose layout defeats text extraction,
including scanned PDFs without a text layer (OCR).

The model reads the PDF itself and returns articles in a fixed format. Its
output is then checked word-for-word against the PDF's own text layer: each
article gets a `coverage` score (share of its 6-word sequences found in the
text layer). Articles the text layer does not support are not indexed, so the
model can restructure the document but cannot add wording to it.

Scanned PDFs have no text layer to check against; their articles are indexed
with a visible "unverified OCR" warning.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from compliance.config import get_settings
from compliance.corpus.extract import extract_pages
from compliance.corpus.fetch import raw_file, sha256
from compliance.corpus.registry import Source
from compliance.llm.base import LLMError
from compliance.retrieval.text import normalize

SHINGLE = 6
MATCHED, PARTIAL = 0.9, 0.6
MIN_TEXT_LAYER_CHARS = 500

SYSTEM = (
    "You transcribe official legal documents for a compliance database. Accuracy of wording is the only "
    "goal: copy text exactly as printed. Never summarise, translate, correct, complete or reorder wording."
)

INSTRUCTION = """Transcribe the articles that START on PDF pages {first} to {last} (1-indexed) of the attached document.
Some pages may print two book pages side by side, and article headings may be printed next to or after
their text - reconstruct the correct article order and numbering from the document itself.

Output format, one block per article, nothing else:
=== Article <number> | <article title, or empty>
<exact article text, paragraphs and numbering preserved>

Rules:
- Copy words exactly. If a word is illegible write [illegible]; never guess.
- If an article that starts in this range continues onto later pages, include its full text.
- Leave out running headers, footers, page numbers, the table of contents and footnote markers.
- If no article starts in this range, output exactly: NONE"""

_BLOCK = re.compile(r"^===\s*Article\s+(.+?)\s*\|\s*(.*?)\s*$", re.MULTILINE)


@dataclass
class AIArticle:
    article: str
    title: str
    text: str
    coverage: float | None = None
    status: str = "unchecked"  # matched | partial | unmatched | unverified_ocr


def ai_text_path(source_id: str) -> Path:
    return get_settings().data_dir / "laws" / "ai_text" / f"{source_id}.json"


def parse_blocks(raw: str) -> list[AIArticle]:
    matches = list(_BLOCK.finditer(raw))
    out = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        number = re.sub(r"[()\s]", "", m.group(1))
        text = raw[m.end() : end].strip()
        if number and text:
            out.append(AIArticle(article=number, title=m.group(2).strip(), text=text))
    return out


def _shingles(text: str) -> list[str]:
    words = normalize(text).replace("[illegible]", " ").split()
    return [" ".join(words[i : i + SHINGLE]) for i in range(max(len(words) - SHINGLE + 1, 1))]


def score_against_text_layer(articles: list[AIArticle], text_layer: str) -> None:
    has_layer = len(text_layer.strip()) >= MIN_TEXT_LAYER_CHARS
    layer = set(_shingles(text_layer)) if has_layer else set()
    for a in articles:
        if not has_layer:
            a.coverage, a.status = None, "unverified_ocr"
            continue
        shingles = _shingles(a.text)
        a.coverage = round(sum(s in layer for s in shingles) / len(shingles), 3)
        a.status = "matched" if a.coverage >= MATCHED else "partial" if a.coverage >= PARTIAL else "unmatched"


def transcribe(source: Source, llm, pages_per_call: int = 4, log=print) -> dict:
    if not hasattr(llm, "read_pdf"):
        raise LLMError("AI extraction needs LLM_PROVIDER=anthropic (PDF input)")
    path = raw_file(source.id)
    if path is None or path.suffix.lower() != ".pdf":
        raise FileNotFoundError(f"No PDF for {source.id}; run scripts/fetch_laws.py first")

    pages = extract_pages(path, source.trim)  # stops at the trim marker
    pdf = path.read_bytes()
    found: dict[str, AIArticle] = {}
    for first in range(1, len(pages) + 1, pages_per_call):
        last = min(first + pages_per_call - 1, len(pages))
        log(f"  pages {first}-{last} ...")
        raw = llm.read_pdf(pdf, SYSTEM, INSTRUCTION.format(first=first, last=last))
        if raw.strip() == "NONE":
            continue
        for art in parse_blocks(raw):
            # An article spanning two ranges may be returned twice; keep the fuller copy.
            if art.article not in found or len(art.text) > len(found[art.article].text):
                found[art.article] = art

    articles = sorted(found.values(), key=lambda a: _sort_key(a.article))
    score_against_text_layer(articles, "\n".join(pages))
    result = {
        "source_id": source.id,
        "model": getattr(llm, "model", ""),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pdf_sha256": sha256(path),
        "pages": len(pages),
        "articles": [asdict(a) for a in articles],
    }
    out = ai_text_path(source.id)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def load_transcription(source_id: str) -> dict | None:
    """Return the saved transcription if it was made from the current PDF."""
    path, raw = ai_text_path(source_id), raw_file(source_id)
    if not path.exists() or raw is None:
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if data.get("pdf_sha256") == sha256(raw) else None


def _sort_key(article: str) -> tuple:
    m = re.match(r"(\d+)(.*)", article)
    return (int(m.group(1)), m.group(2)) if m else (10**6, article)
