"""Split a legal text into article-level passages.

Recognised headings (each on its own line):
  Article 5 · Article (5) · Article 5 - Title · ANNEX III · المادة (5)
Text before the first heading becomes "Preamble" passages. Documents without
article headings (charters, guidelines) are split into numbered sections.
"""
from __future__ import annotations

import re

from compliance.corpus.registry import Source
from compliance.models import Passage

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

HEADING = re.compile(
    r"^(?:"
    r"article\s*\(?\s*(?P<art>\d+[a-z]?(?:\s+(?:bis|ter))?)\s*\)?(?:\s*[-–:.]\s*(?P<title>.{1,100}))?"
    r"|annex\s+(?P<annex>[IVXLC]+)"
    r"|(?:ال)?مادة\s*\(?\s*(?P<ar>[0-9٠-٩]+)\s*\)?"
    r")\s*$",
    re.IGNORECASE | re.MULTILINE,
)

RECITAL = re.compile(r"^\((\d{1,3})\)(?=\s|$)", re.MULTILINE)

MAX_PART_CHARS = 2400
MIN_BODY_CHARS = 40
SECTION_CHARS = 1500


def split_long(body: str, limit: int) -> list[str]:
    if len(body) <= limit:
        return [body]
    parts, current = [], ""
    for para in re.split(r"\n(?=\S)", body):
        if current and len(current) + len(para) + 1 > limit:
            parts.append(current.strip())
            current = ""
        current += ("\n" if current else "") + para
        while len(current) > limit:  # a single paragraph longer than the limit
            parts.append(current[:limit].strip())
            current = current[limit:]
    if current.strip():
        parts.append(current.strip())
    return parts


def _heading_and_body(body: str, inline_title: str | None) -> tuple[str, str]:
    if inline_title:
        return inline_title.strip(), body.strip()
    lines = body.strip().split("\n", 1)
    first = lines[0].strip()
    if 2 < len(first) <= 90 and not re.search(r"[.;:,]$", first) and not re.match(r"^[\d(]", first):
        return first, (lines[1] if len(lines) > 1 else "").strip()
    return "", body.strip()


def make_passage(source: Source, article: str, heading: str, text: str, part: int) -> Passage:
    return Passage(
        id=f"{source.id}:{article}:{part}",
        source_id=source.id,
        jurisdiction=source.jurisdiction,
        source_title=source.title,
        source_short=source.short,
        kind=source.kind,
        article=article,
        heading=heading,
        part=part,
        text=text,
        notes=source.notes,
    )


def chunk_text(text: str, source: Source) -> list[Passage]:
    matches = list(HEADING.finditer(text))
    if not matches:
        return [
            make_passage(source, f"§{i + 1}", "", piece, 0)
            for i, piece in enumerate(split_long(text, SECTION_CHARS))
            if len(piece) >= MIN_BODY_CHARS
        ]

    # Collect (label, heading, body); keep the longest body per label so that
    # tables of contents do not shadow the real article.
    best: dict[str, tuple[int, str, str]] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        raw_body = text[m.end():end]
        if m.group("annex"):
            label = f"Annex {m.group('annex').upper()}"
        else:
            num = (m.group("art") or m.group("ar") or "").translate(ARABIC_DIGITS)
            label = re.sub(r"\s+", " ", num).strip()
        heading, body = _heading_and_body(raw_body, m.group("title"))
        if len(body) < MIN_BODY_CHARS:
            continue
        if label not in best or len(body) > len(best[label][2]):
            best[label] = (m.start(), heading, body)

    passages: list[Passage] = []
    preamble = text[: matches[0].start()].strip()
    recitals = list(RECITAL.finditer(preamble))
    if len(recitals) >= 3:  # EU-style numbered recitals: one passage each
        head = preamble[: recitals[0].start()].strip()
        if len(head) >= MIN_BODY_CHARS:
            passages.append(make_passage(source, "Preamble", "", head[:MAX_PART_CHARS], 0))
        for i, m in enumerate(recitals):
            end = recitals[i + 1].start() if i + 1 < len(recitals) else len(preamble)
            body = preamble[m.end():end].strip()
            for part, piece in enumerate(split_long(body, MAX_PART_CHARS)):
                passages.append(make_passage(source, f"Recital {m.group(1)}", "", piece, part))
    elif len(preamble) >= MIN_BODY_CHARS:
        for part, piece in enumerate(split_long(preamble, MAX_PART_CHARS)):
            passages.append(make_passage(source, "Preamble", "", piece, part))

    for label, (_, heading, body) in sorted(best.items(), key=lambda kv: kv[1][0]):
        for part, piece in enumerate(split_long(body, MAX_PART_CHARS)):
            passages.append(make_passage(source, label, heading, piece, part))
    return passages
