from __future__ import annotations

import json
import re
from typing import Protocol


class LLMError(RuntimeError):
    pass


class LLM(Protocol):
    name: str

    @property
    def available(self) -> bool: ...

    def complete(self, system: str, user: str, max_tokens: int = 16000) -> str: ...


class NoLLM:
    """Placeholder used in extractive mode; never generates text."""

    name = "none"

    @property
    def available(self) -> bool:
        return False

    def complete(self, system: str, user: str, max_tokens: int = 16000) -> str:
        raise LLMError("No LLM configured (LLM_PROVIDER=none)")


def parse_json_object(raw: str) -> dict:
    """Extract the first JSON object from a model response (tolerates code fences)."""
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        raise LLMError("Model response did not contain a JSON object")
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError(f"Model response was not valid JSON: {exc}") from exc
