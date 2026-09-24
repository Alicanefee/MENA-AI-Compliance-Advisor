from __future__ import annotations

import os

from compliance.llm.base import LLMError


class OpenAILLM:
    name = "openai"

    def __init__(self, model: str):
        self.model = model
        self._client = None

    @property
    def available(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY"))

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise LLMError("Install the 'openai' package to use LLM_PROVIDER=openai") from exc
            self._client = OpenAI()
        return self._client

    def complete(self, system: str, user: str, max_tokens: int = 16000) -> str:
        try:
            resp = self._get_client().chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            )
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(f"OpenAI request failed: {exc}") from exc
        return resp.choices[0].message.content or ""
