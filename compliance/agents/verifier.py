"""Deterministic verification of claims against the retrieved passages.

A claim survives only if the passage it cites was actually retrieved and its
quote appears verbatim (after whitespace/case normalisation) in that passage.
No model is involved, so the check cannot itself hallucinate.
"""
from __future__ import annotations

from compliance.models import Claim, ScoredPassage
from compliance.retrieval.text import normalize

MIN_QUOTE_WORDS = 5


def check(claim: Claim, by_label: dict[str, ScoredPassage]) -> Claim:
    sp = by_label.get(claim.passage.strip().strip("[]"))
    if sp is None:
        return claim.model_copy(update={"status": "rejected", "reason": f"cites unknown passage '{claim.passage}'"})
    claim = claim.model_copy(update={"source_id": sp.passage.source_id, "article": sp.passage.article})
    quote = normalize(claim.quote).strip(" \"'.")
    if not claim.text.strip():
        return claim.model_copy(update={"status": "rejected", "reason": "empty statement"})
    if len(quote.split()) < MIN_QUOTE_WORDS:
        return claim.model_copy(update={"status": "rejected", "reason": "quote too short to verify"})
    if quote not in normalize(sp.passage.text):
        return claim.model_copy(update={"status": "rejected", "reason": "quote not found in the cited passage"})
    return claim.model_copy(update={"status": "verified", "reason": ""})


def verify(claims: list[Claim], passages: list[ScoredPassage]) -> tuple[list[Claim], list[Claim]]:
    by_label = {sp.label: sp for sp in passages}
    checked = [check(c, by_label) for c in claims]
    return [c for c in checked if c.status == "verified"], [c for c in checked if c.status == "rejected"]
