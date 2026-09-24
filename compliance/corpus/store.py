"""Build and load the passage index (`data/index/passages.jsonl`)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from compliance.config import get_settings
from compliance.corpus.ai_extract import load_transcription
from compliance.corpus.chunker import MIN_BODY_CHARS, chunk_text, make_passage, split_long
from compliance.corpus.extract import extract, extract_pages
from compliance.corpus.fetch import raw_file
from compliance.corpus.registry import Source, load_registry
from compliance.models import Passage


@dataclass
class BuildReport:
    source_id: str
    status: str  # indexed | missing
    passages: int = 0
    articles: int = 0
    chars: int = 0
    detail: str = ""


def _from_transcription(source: Source, data: dict) -> tuple[list[Passage], str]:
    passages, skipped = [], []
    for art in data["articles"]:
        if art["status"] == "unmatched":
            skipped.append(art["article"])
            continue
        if art["status"] == "unverified_ocr":
            note = "AI transcription of a scanned PDF (OCR) - wording not verified against a text layer."
        else:
            note = f"AI transcription; {round((art['coverage'] or 0) * 100)}% of its wording matched the PDF text layer."
        src = source.model_copy(update={"notes": f"{source.notes} {note}".strip()})
        for part, piece in enumerate(split_long(art["text"], 2400)):
            passages.append(make_passage(src, art["article"], art["title"], piece, part))
    detail = f"AI transcription ({data.get('model')}, {data.get('created_at')})"
    if skipped:
        detail += f"; not indexed, wording not found in PDF: articles {', '.join(skipped)}"
    return passages, detail


def _by_page(source: Source, path: Path) -> list[Passage]:
    src = source.model_copy(
        update={"notes": f"{source.notes} Article numbers could not be read from this PDF; indexed by page. "
                         "Run scripts/ai_extract.py for article-level passages.".strip()}
    )
    passages = []
    for n, page in enumerate(extract_pages(path, source.trim), start=1):
        for part, piece in enumerate(split_long(page, 2400)):
            if len(piece) >= MIN_BODY_CHARS:
                passages.append(make_passage(src, f"p. {n}", "", piece, part))
    return passages


def build_source(source: Source) -> tuple[list[Passage], BuildReport]:
    path = raw_file(source.id)
    if not path:
        return [], BuildReport(source.id, "missing")
    text = extract(path, source.trim)
    get_settings().text_dir.mkdir(parents=True, exist_ok=True)
    (get_settings().text_dir / f"{source.id}.txt").write_text(text, encoding="utf-8")

    detail = ""
    if source.extraction == "ai" and path.suffix.lower() == ".pdf":
        transcription = load_transcription(source.id)
        if transcription:
            chunks, detail = _from_transcription(source, transcription)
        else:
            chunks, detail = _by_page(source, path), "indexed by page - run scripts/ai_extract.py"
    else:
        chunks = chunk_text(text, source)
    report = BuildReport(source.id, "indexed", len(chunks), len({c.article for c in chunks}), len(text), detail)
    return chunks, report


def build_passages() -> tuple[list[Passage], list[BuildReport]]:
    passages: list[Passage] = []
    reports: list[BuildReport] = []
    for source in load_registry().sources:
        chunks, report = build_source(source)
        passages.extend(chunks)
        reports.append(report)
    return passages, reports


def save_passages(passages: list[Passage], path: Path | None = None) -> Path:
    path = path or get_settings().chunks_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for p in passages:
            fh.write(p.model_dump_json() + "\n")
    return path


def load_passages(path: Path | None = None) -> list[Passage]:
    path = path or get_settings().chunks_path
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as fh:
        return [Passage.model_validate(json.loads(line)) for line in fh if line.strip()]
