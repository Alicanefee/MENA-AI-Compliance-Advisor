"""Okapi BM25 over passages - deterministic and dependency-free."""
from __future__ import annotations

import math
from collections import Counter

from compliance.models import Passage
from compliance.retrieval.text import tokenize


# Recitals and preambles explain a law but do not bind; prefer operative articles.
NON_OPERATIVE_WEIGHT = 0.75


def passage_document(p: Passage) -> str:
    # Headings are repeated so that a match on an article title weighs more.
    return f"{p.heading} {p.heading} {p.source_short} article {p.article} {p.text}"


class BM25Index:
    def __init__(self, passages: list[Passage], k1: float = 1.5, b: float = 0.75):
        self.passages = passages
        self.k1, self.b = k1, b
        self._tf = [Counter(tokenize(passage_document(p))) for p in passages]
        self._len = [sum(tf.values()) for tf in self._tf]
        self._avg = (sum(self._len) / len(self._len)) if self._len else 0.0
        df: Counter = Counter()
        for tf in self._tf:
            df.update(tf.keys())
        n = len(passages)
        self._idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    def search(self, query: str, k: int = 8, jurisdictions: set[str] | None = None) -> list[tuple[Passage, float]]:
        terms = set(tokenize(query))
        scored = []
        for i, p in enumerate(self.passages):
            if jurisdictions and p.jurisdiction not in jurisdictions:
                continue
            tf, length = self._tf[i], self._len[i]
            score = 0.0
            for t in terms:
                f = tf.get(t)
                if not f:
                    continue
                norm = self.k1 * (1 - self.b + self.b * length / self._avg)
                score += self._idf[t] * f * (self.k1 + 1) / (f + norm)
            if score > 0:
                if p.article.startswith(("Recital", "Preamble")):
                    score *= NON_OPERATIVE_WEIGHT
                scored.append((p, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]
