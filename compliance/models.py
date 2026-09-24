"""Shared data models."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Passage(BaseModel):
    """One article (or part of an article) of an official source."""

    id: str
    source_id: str
    jurisdiction: str
    source_title: str
    source_short: str
    kind: str
    article: str
    heading: str = ""
    part: int = 0
    text: str
    notes: str = ""


class ScoredPassage(BaseModel):
    passage: Passage
    score: float
    retrieval: str = "bm25"
    label: str = ""  # "P1", "P2", ... as shown to the agents and the user


class Claim(BaseModel):
    """A statement that must be backed by a verbatim quote from a retrieved passage."""

    text: str
    passage: str  # passage label, e.g. "P2"
    quote: str
    role: Literal["finding", "counterpoint"] = "finding"
    status: Literal["verified", "rejected", "disputed"] = "verified"
    reason: str = ""
    source_id: str = ""
    article: str = ""


class RequiredDocument(BaseModel):
    id: str
    name: str
    mandatory: bool
    why: str
    basis: list[dict] = Field(default_factory=list)  # [{"source": ..., "article": ..., "in_corpus": bool}]
    kind: Literal["legal", "practice"] = "legal"


class Answer(BaseModel):
    question: str
    jurisdictions: list[str]
    mode: Literal["generated", "extractive"]
    status: Literal["answered", "partial", "insufficient_basis"]
    summary: str
    findings: list[Claim] = Field(default_factory=list)
    counterpoints: list[Claim] = Field(default_factory=list)
    rejected: list[Claim] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    passages: list[ScoredPassage] = Field(default_factory=list)
    documents: list[RequiredDocument] = Field(default_factory=list)
    citation_coverage: float = 0.0
    review_required: bool = True
    disclaimer: str = ""
