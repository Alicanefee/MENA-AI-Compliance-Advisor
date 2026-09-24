"""Convert downloaded PDF / HTML sources into clean plain text."""
from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader

from compliance.corpus.registry import Trim

# Government PDFs often have minor structural defects; pypdf's warnings are noise here.
logging.getLogger("pypdf").setLevel(logging.ERROR)

# pypdf renders some ligature glyphs by name, e.g. "/T_he" for "The".
_GLYPH_NAME = re.compile(r"/([A-Z])_([a-z])")
_PAGE_NUMBER_LINE = re.compile(r"^\s*(?:page\s*)?\d{1,4}(?:\s+\d{1,4})?\s*$", re.IGNORECASE)
_SPACES = re.compile(r"[ \t ]+")
_BLANK_LINES = re.compile(r"\n{3,}")


def _page_text(page) -> str:
    """Extract one page. Landscape pages that print two book pages side by side
    are read column by column instead of line by line across both."""
    box = page.mediabox
    width, height = float(box.width), float(box.height)
    if width <= height * 1.2:
        return page.extract_text() or ""
    middle = float(box.left) + width / 2
    columns: tuple[list[str], list[str]] = ([], [])

    def visit(text, cm, tm, font, size):
        x = cm[0] * tm[4] + cm[2] * tm[5] + cm[4]
        columns[0 if x < middle else 1].append(text)

    page.extract_text(visitor_text=visit)
    return "".join(columns[0]) + "\n" + "".join(columns[1])


def pdf_pages(path: Path) -> list[str]:
    return [_page_text(page) for page in PdfReader(str(path)).pages]


def pdf_to_text(path: Path) -> str:
    return "\n".join(pdf_pages(path))


def html_to_text(path: Path) -> str:
    soup = BeautifulSoup(path.read_bytes(), "html.parser")
    for tag in soup.select("script, style, nav, header, footer, aside, form, noscript"):
        tag.decompose()
    main = soup.select_one("main") or soup.select_one("article") or soup.body or soup
    return main.get_text("\n", strip=True)


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _GLYPH_NAME.sub(r"\1\2", text)
    text = text.replace("►", "")
    text = "".join(ch for ch in text if ch in "\n\t" or unicodedata.category(ch)[0] != "C")
    lines = []
    for line in text.split("\n"):
        line = _SPACES.sub(" ", line).strip()
        if _PAGE_NUMBER_LINE.match(line):
            continue
        lines.append(line)
    return _BLANK_LINES.sub("\n\n", "\n".join(lines)).strip()


def apply_trim(text: str, trim: Trim | None) -> str:
    """Cut the text at the n-th occurrence of `trim.end_marker` (case-insensitive)."""
    if not trim:
        return text
    hits = [m.start() for m in re.finditer(re.escape(trim.end_marker), text, re.IGNORECASE)]
    if len(hits) >= trim.occurrence:
        return text[: hits[trim.occurrence - 1]].rstrip()
    return text


def extract(path: Path, trim: Trim | None = None) -> str:
    raw = pdf_to_text(path) if path.suffix.lower() == ".pdf" else html_to_text(path)
    return clean_text(apply_trim(raw, trim))


def extract_pages(path: Path, trim: Trim | None = None) -> list[str]:
    """Cleaned text per PDF page, stopping where `trim` cuts the document."""
    pages, seen = [], ""
    for raw in pdf_pages(path):
        kept = apply_trim(seen + raw, trim)
        if len(kept) < len(seen) + len(raw):  # the trim marker falls on this page
            pages.append(clean_text(kept[len(seen):]))
            break
        seen += raw
        pages.append(clean_text(raw))
    return pages
