"""Retriever facade: BM25, optionally fused with vector search (reciprocal rank fusion)."""
from __future__ import annotations

from compliance.config import get_settings
from compliance.models import Passage, ScoredPassage
from compliance.retrieval.bm25 import BM25Index

RRF_K = 60


def rrf(rankings: list[list[str]], k: int = RRF_K) -> dict[str, float]:
    fused: dict[str, float] = {}
    for ranking in rankings:
        for rank, pid in enumerate(ranking):
            fused[pid] = fused.get(pid, 0.0) + 1.0 / (k + rank + 1)
    return fused


class Retriever:
    def __init__(self, passages: list[Passage], use_vector: bool | None = None):
        self.passages = passages
        self.bm25 = BM25Index(passages)
        self.vector = None
        if use_vector if use_vector is not None else get_settings().retrieval == "hybrid":
            from compliance.retrieval.vector import VectorIndex

            self.vector = VectorIndex(passages)

    @property
    def empty(self) -> bool:
        return not self.passages

    def search(self, query: str, k: int = 8, jurisdictions: set[str] | None = None) -> list[ScoredPassage]:
        lexical = self.bm25.search(query, k=k * 2, jurisdictions=jurisdictions)
        if not self.vector:
            return [ScoredPassage(passage=p, score=round(s, 3), retrieval="bm25") for p, s in lexical[:k]]

        semantic = self.vector.search(query, k=k * 2, jurisdictions=jurisdictions)
        by_id = {p.id: p for p, _ in lexical + semantic}
        bm25_score = {p.id: s for p, s in lexical}
        fused = rrf([[p.id for p, _ in lexical], [p.id for p, _ in semantic]])
        ranked = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)[:k]
        return [
            ScoredPassage(
                passage=by_id[pid],
                # Keep the lexical score for thresholds; vector-only hits score 0.
                score=round(bm25_score.get(pid, 0.0), 3),
                retrieval="hybrid" if pid in bm25_score else "vector",
            )
            for pid, _ in ranked
        ]
