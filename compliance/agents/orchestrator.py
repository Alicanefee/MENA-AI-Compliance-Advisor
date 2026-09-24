"""Advice pipeline.

  retrieve -> analyst drafts findings -> challenger reviews them -> verifier
  checks every quote -> document rules -> answer (always flagged for human review)

Without an LLM the pipeline stops after retrieval and returns the provisions
themselves (extractive mode). With too little evidence it abstains.
"""
from __future__ import annotations

import logging
import re

from compliance import disclaimer
from compliance.agents import analyst, challenger, verifier
from compliance.agents.context import citation, label_passages
from compliance.agents.documents import required_documents
from compliance.config import get_settings
from compliance.corpus.lookup import CorpusLookup
from compliance.llm import LLM, LLMError
from compliance.models import Answer, Claim
from compliance.retrieval.hybrid import Retriever
from compliance.retrieval.text import normalize

log = logging.getLogger(__name__)

JURISDICTION_HINTS = {
    "AE": ["uae", "emirates", "dubai", "abu dhabi", "sharjah", "ajman", "mohre", "difc", "adgm", "الإمارات"],
    "SA": ["saudi", "ksa", "riyadh", "jeddah", "sdaia", "kingdom", "السعودية"],
    "EU": ["eu", "europe", "european", "gdpr", "ai act", "germany", "france"],
}
ALL_JURISDICTIONS = ["AE", "SA", "EU"]


def detect_jurisdictions(text: str) -> list[str]:
    norm = normalize(text)
    found = [
        code
        for code, hints in JURISDICTION_HINTS.items()
        if any(re.search(rf"(?<!\w){re.escape(normalize(h))}(?!\w)", norm) for h in hints)
    ]
    return found or ALL_JURISDICTIONS


class Advisor:
    def __init__(self, retriever: Retriever, lookup: CorpusLookup, llm: LLM, k: int = 8):
        self.retriever = retriever
        self.lookup = lookup
        self.llm = llm
        self.k = k

    def ask(self, question: str, jurisdictions: list[str] | None = None, context: str = "", lang: str = "en") -> Answer:
        scope = jurisdictions or detect_jurisdictions(f"{question} {context}")
        min_score = get_settings().min_passage_score
        hits = self.retriever.search(f"{question} {context}".strip(), k=self.k, jurisdictions=set(scope))
        passages = label_passages([h for h in hits if h.score >= min_score or h.retrieval == "vector"])
        documents = required_documents(f"{question} {context}", scope, self.lookup)

        base = dict(
            question=question,
            jurisdictions=scope,
            passages=passages,
            documents=documents,
            disclaimer=disclaimer.short(lang),
        )

        if not passages:
            return Answer(
                **base,
                mode="extractive" if not self.llm.available else "generated",
                status="insufficient_basis",
                summary=(
                    "No indexed provision matches this question closely enough. "
                    "The advisor does not answer without a source; refine the question or add the relevant law."
                    if not self.retriever.empty
                    else "The legal corpus has not been built yet. Run scripts/fetch_laws.py and scripts/build_index.py."
                ),
            )

        if not self.llm.available:
            return Answer(
                **base,
                mode="extractive",
                status="partial",
                summary=(
                    f"No language model is configured, so no conclusions are drawn. The {len(passages)} most relevant "
                    "provisions are listed below; read them directly and have them reviewed."
                ),
            )

        try:
            drafted, open_q = analyst.draft(self.llm, question, passages)
            disputed, counter, open_q2 = challenger.review(self.llm, question, passages, drafted)
        except LLMError as exc:
            log.warning("LLM step failed: %s", exc)
            return Answer(
                **base,
                mode="extractive",
                status="partial",
                summary="The language model step failed, so only the retrieved provisions are shown.",
                open_questions=[str(exc)],
            )

        # Findings the challenger disputed stay visible but are not presented as conclusions.
        by_label = {sp.label: sp for sp in passages}
        kept, disputed_claims, rejected = [], [], []
        for i, claim in enumerate(drafted):
            checked = verifier.check(claim, by_label)
            if checked.status == "rejected":
                rejected.append(checked)
            elif i in disputed:
                disputed_claims.append(checked.model_copy(update={"status": "disputed", "reason": disputed[i]}))
            else:
                kept.append(checked)
        counterpoints, rejected_counter = verifier.verify(counter, passages)

        proposed = len(drafted) + len(counter)
        verified_total = len(kept) + len(disputed_claims) + len(counterpoints)
        coverage = round(verified_total / proposed, 3) if proposed else 0.0

        if not kept:
            status = "insufficient_basis"
        elif disputed_claims or rejected or rejected_counter:
            status = "partial"
        else:
            status = "answered"

        return Answer(
            **base,
            mode="generated",
            status=status,
            summary=_summary(kept, counterpoints, disputed_claims, rejected + rejected_counter, passages),
            findings=kept,
            counterpoints=counterpoints + disputed_claims,
            rejected=rejected + rejected_counter,
            open_questions=_dedupe(open_q + open_q2),
            citation_coverage=coverage,
        )


def _summary(findings: list[Claim], counter: list[Claim], disputed: list[Claim], rejected: list[Claim], passages) -> str:
    """Deterministic summary - the model never writes free text that reaches the user unchecked."""
    if not findings:
        return (
            "No statement could be verified against the retrieved provisions, so no conclusion is given. "
            "Review the provisions below or refine the question."
        )
    by_label = {sp.label: sp for sp in passages}
    cited = sorted({citation(by_label[c.passage]) for c in findings if c.passage in by_label})
    parts = [f"{len(findings)} verified finding(s) based on: {'; '.join(cited)}."]
    if counter:
        parts.append(f"{len(counter)} counterpoint(s) or limitation(s) to consider.")
    if disputed:
        parts.append(f"{len(disputed)} finding(s) disputed by the reviewing agent - treat as unresolved.")
    if rejected:
        parts.append(f"{len(rejected)} statement(s) removed because their quote could not be verified.")
    return " ".join(parts)


def _dedupe(items: list[str]) -> list[str]:
    seen, out = set(), []
    for item in items:
        key = normalize(item)
        if item.strip() and key not in seen:
            seen.add(key)
            out.append(item.strip())
    return out
