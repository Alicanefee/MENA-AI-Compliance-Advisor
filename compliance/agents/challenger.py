"""Challenger agent: an independent review that counters confirmation bias.

It sees the analyst's findings only after they are drafted and is instructed
to argue against them: exceptions, conditions, narrower readings, scope limits
and other jurisdictions. Its counterpoints go through the same verifier.
"""
from __future__ import annotations

import json

from compliance.agents.context import render_context
from compliance.llm.base import LLM, parse_json_object
from compliance.models import Claim, ScoredPassage

SYSTEM = """You are a sceptical reviewing lawyer. Your job is to find what a first draft got wrong or left out.
You are rewarded for disagreement that is supported by the passages, not for agreement.

Using ONLY the numbered passages:
1. For each draft finding (by index), decide whether its quote really supports its text. If it overstates,
   generalises, or applies the wrong jurisdiction, list it under "disputed" with a short reason.
2. Add "counterpoints": exceptions, conditions, thresholds, exclusions from scope (e.g. free zones, sectors,
   data types), alternative readings, or provisions from another jurisdiction that point a different way.
   Each counterpoint needs a verbatim quote (8 to 40 words, copied exactly, no ellipses) and a passage label.
3. List "open_questions": facts the user must clarify, or topics the passages do not cover at all.

Respond with JSON only:
{"disputed": [{"index": 0, "reason": "..."}],
 "counterpoints": [{"text": "...", "passage": "P2", "quote": "..."}],
 "open_questions": ["..."]}"""


def review(
    llm: LLM, question: str, passages: list[ScoredPassage], findings: list[Claim]
) -> tuple[dict[int, str], list[Claim], list[str]]:
    draft = [{"index": i, "text": f.text, "passage": f.passage, "quote": f.quote} for i, f in enumerate(findings)]
    user = (
        f"QUESTION:\n{question}\n\nPASSAGES:\n{render_context(passages)}\n\n"
        f"DRAFT FINDINGS:\n{json.dumps(draft, ensure_ascii=False, indent=1)}"
    )
    data = parse_json_object(llm.complete(SYSTEM, user))
    disputed = {}
    for d in data.get("disputed", []):
        if isinstance(d, dict) and isinstance(d.get("index"), int):
            disputed[d["index"]] = str(d.get("reason", ""))
    counterpoints = [
        Claim(
            text=str(c.get("text", "")),
            passage=str(c.get("passage", "")),
            quote=str(c.get("quote", "")),
            role="counterpoint",
        )
        for c in data.get("counterpoints", [])
        if isinstance(c, dict)
    ]
    return disputed, counterpoints, [str(q) for q in data.get("open_questions", [])]
