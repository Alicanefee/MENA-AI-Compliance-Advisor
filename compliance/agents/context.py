"""Formats retrieved passages for the agents."""
from __future__ import annotations

from compliance.models import ScoredPassage


def label_passages(passages: list[ScoredPassage]) -> list[ScoredPassage]:
    for i, sp in enumerate(passages, start=1):
        sp.label = f"P{i}"
    return passages


def citation(sp: ScoredPassage) -> str:
    p = sp.passage
    art = f"Article {p.article}" if p.article[:1].isdigit() else p.article
    heading = f" - {p.heading}" if p.heading else ""
    return f"{p.source_short}, {art}{heading}"


def render_context(passages: list[ScoredPassage]) -> str:
    blocks = []
    for sp in passages:
        p = sp.passage
        kind = "binding law" if p.kind in ("law", "regulation") else "non-binding guidance"
        blocks.append(f"[{sp.label}] {citation(sp)} ({p.jurisdiction}, {kind})\n{p.text}")
    return "\n\n---\n\n".join(blocks)
