"""LLM provider adapter for OpenAI and Anthropic.

Swap providers via LLM_PROVIDER env (openai | anthropic).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.settings import settings


class LLMClient(ABC):
    @abstractmethod
    def complete(self, *, system: str, user: str) -> str:
        """Return the model's text completion."""
        ...


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str | None = None) -> None:
        self._key = api_key or settings.llm_api_key
        if not self._key:
            raise RuntimeError("OpenAI API key not set. Set LLM_API_KEY in .env.")

    def complete(self, *, system: str, user: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self._key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content or ""


class AnthropicClient(LLMClient):
    def __init__(self, api_key: str | None = None) -> None:
        self._key = api_key or settings.llm_api_key
        if not self._key:
            raise RuntimeError("Anthropic API key not set. Set LLM_API_KEY in .env.")

    def complete(self, *, system: str, user: str) -> str:
        from anthropic import Anthropic

        client = Anthropic(api_key=self._key)
        resp = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text if resp.content else ""


def get_llm_client() -> LLMClient | None:
    """Return the configured LLM client, or None if no API key is set."""
    if not settings.llm_api_key:
        return None

    provider = (settings.llm_provider or "openai").lower()
    if provider == "openai":
        return OpenAIClient()
    if provider == "anthropic":
        return AnthropicClient()
    return OpenAIClient()
