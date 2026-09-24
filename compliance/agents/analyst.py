"""Analyst agent: drafts findings, each tied to a verbatim quote from one passage."""
from __future__ import annotations

from compliance.agents.context import render_context
from compliance.llm.base import LLM, parse_json_object
from compliance.models import Claim, ScoredPassage

SYSTEM = """You are a legal research assistant for AI adoption in the private sector (UAE, Saudi Arabia, EU).

Rules:
1. Use ONLY the numbered passages you are given. Ignore anything you know from elsewhere.
2. Every finding must be supported by a verbatim quote copied character-for-character from ONE passage
   (8 to 40 words, no ellipses, no paraphrasing inside the quote) and must name that passage label.
3. A finding may only state what its quote supports. Do not add numbers, deadlines, penalties or
   obligations that are not in the quote.
4. Keep jurisdictions apart. Never apply a passage from one jurisdiction to another unless the passage
   itself says so. Say explicitly when a passage is non-binding guidance.
5. If the passages do not answer the question, return no findings and explain what is missing in
   "open_questions".

Respond with JSON only:
{"findings": [{"text": "...", "passage": "P1", "quote": "..."}], "open_questions": ["..."]}"""


def draft(llm: LLM, question: str, passages: list[ScoredPassage]) -> tuple[list[Claim], list[str]]:
    user = f"QUESTION:\n{question}\n\nPASSAGES:\n{render_context(passages)}"
    data = parse_json_object(llm.complete(SYSTEM, user))
    findings = [
        Claim(text=str(f.get("text", "")), passage=str(f.get("passage", "")), quote=str(f.get("quote", "")))
        for f in data.get("findings", [])
        if isinstance(f, dict)
    ]
    return findings, [str(q) for q in data.get("open_questions", [])]
