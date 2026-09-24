"""Loads `config/sources.yaml`."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from compliance.config import get_settings


class Trim(BaseModel):
    end_marker: str
    occurrence: int = 1


class Source(BaseModel):
    id: str
    jurisdiction: str
    title: str
    short: str
    kind: str = "law"
    language: str = "en"
    urls: list[str] = Field(default_factory=list)
    accept: str = ""
    manual_url: str = ""
    trim: Trim | None = None
    # text: article structure is read from the PDF text layer
    # ai:   the layout defeats text extraction; run scripts/ai_extract.py
    extraction: Literal["text", "ai"] = "text"
    notes: str = ""


class Registry(BaseModel):
    sources: list[Source]
    jurisdictions: dict[str, dict[str, str]]

    def get(self, source_id: str) -> Source | None:
        return next((s for s in self.sources if s.id == source_id), None)

    def jurisdiction_name(self, code: str, lang: str = "en") -> str:
        names = self.jurisdictions.get(code, {})
        return names.get(lang) or names.get("en") or code


def load_registry(path: Path | None = None) -> Registry:
    path = path or get_settings().config_dir / "sources.yaml"
    return _load(str(path))


@lru_cache(maxsize=4)
def _load(path: str) -> Registry:
    with open(path, encoding="utf-8") as fh:
        return Registry.model_validate(yaml.safe_load(fh))
