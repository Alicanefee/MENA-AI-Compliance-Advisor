"""Check a citation (source + article + expected wording) against the indexed text.

Used for the curated content (curriculum, scenarios, document rules): each
citation carries phrases the official text is expected to contain, so a wrong
article number or a mis-remembered rule shows up as `not_confirmed` instead of
being presented as law.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Literal

from compliance.models import Passage
from compliance.retrieval.text import normalize

Status = Literal["confirmed", "not_confirmed", "article_missing", "source_missing"]


class CorpusLookup:
    def __init__(self, passages: list[Passage]):
        self._source: dict[str, list[str]] = defaultdict(list)
        self._article: dict[tuple[str, str], list[str]] = defaultdict(list)
        for p in passages:
            text = normalize(f"{p.heading} {p.text}")
            self._source[p.source_id].append(text)
            self._article[(p.source_id, p.article)].append(text)

    def has_source(self, source_id: str) -> bool:
        return source_id in self._source

    def check(self, source_id: str, article: str | None = None, expect: list[str] | None = None) -> Status:
        if source_id not in self._source:
            return "source_missing"
        if article:
            texts = self._article.get((source_id, str(article)))
            if not texts:
                return "article_missing"
        else:
            texts = self._source[source_id]
        haystack = " ".join(texts)
        if all(normalize(phrase) in haystack for phrase in (expect or [])):
            return "confirmed"
        return "not_confirmed"
