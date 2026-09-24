"""LLM providers behind a minimal interface."""
from __future__ import annotations

from compliance.config import get_settings
from compliance.llm.base import LLM, LLMError, NoLLM

DEFAULT_MODELS = {
    "anthropic": "claude-opus-5",
    "openai": "gpt-4o-mini",
}


def get_llm() -> LLM:
    settings = get_settings()
    provider = settings.llm_provider
    if provider in ("", "none"):
        return NoLLM()
    model = settings.llm_model or DEFAULT_MODELS.get(provider, "")
    if provider == "anthropic":
        from compliance.llm.anthropic_llm import AnthropicLLM

        return AnthropicLLM(model)
    if provider == "openai":
        from compliance.llm.openai_llm import OpenAILLM

        return OpenAILLM(model)
    raise LLMError(f"Unknown LLM_PROVIDER '{provider}' (expected none, anthropic or openai)")


__all__ = ["LLM", "LLMError", "NoLLM", "get_llm"]
