from __future__ import annotations

import base64
import os

from compliance.llm.base import LLMError

# Server-side fallback: if the requested model declines, the API re-runs the
# request on a fallback model chosen by refusal category.
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class AnthropicLLM:
    name = "anthropic"

    def __init__(self, model: str):
        self.model = model
        self._client = None

    @property
    def available(self) -> bool:
        return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError as exc:
                raise LLMError("Install the 'anthropic' package to use LLM_PROVIDER=anthropic") from exc
            self._client = anthropic.Anthropic()
        return self._client

    def _run(self, system, content, max_tokens: int) -> str:
        import anthropic

        try:
            with self._get_client().beta.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": content}],
                betas=[FALLBACK_BETA],
                fallbacks="default",
            ) as stream:
                resp = stream.get_final_message()
        except anthropic.APIConnectionError as exc:
            raise LLMError(f"Could not reach the Anthropic API: {exc}") from exc
        except anthropic.APIStatusError as exc:
            raise LLMError(f"Anthropic API error {exc.status_code}: {exc.message}") from exc
        if resp.stop_reason == "refusal":
            raise LLMError("The model declined this request")
        if resp.stop_reason == "max_tokens":
            raise LLMError("The model response was cut off (max_tokens reached)")
        return "".join(block.text for block in resp.content if block.type == "text")

    def complete(self, system: str, user: str, max_tokens: int = 16000) -> str:
        return self._run(system, user, max_tokens)

    def read_pdf(self, pdf: bytes, system: str, instruction: str, max_tokens: int = 64000) -> str:
        """Ask the model about a PDF. The document block is cached, so repeated
        page-range requests over the same file only pay for it once."""
        document = {
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf", "data": base64.standard_b64encode(pdf).decode()},
            "cache_control": {"type": "ephemeral"},
        }
        system_blocks = [{"type": "text", "text": system}]
        return self._run(system_blocks, [document, {"type": "text", "text": instruction}], max_tokens)
