"""Multi-provider AI switcher.

Tries the configured provider first (default: Anthropic Claude 3.5), then
falls back down the chain — OpenAI, then a local Ollama instance — so a
single provider outage never silences the receptionist. All calls go over
plain HTTPS via httpx; no SDK lock-in.
"""
import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

ANTHROPIC_MODEL_DEFAULT = "claude-3-5-sonnet-20241022"
OPENAI_MODEL_DEFAULT = "gpt-4o-mini"

PROVIDER_CHAIN = ["anthropic", "openai", "ollama"]


class AIProviderError(Exception):
    pass


class AIProvider:
    """generate() returns assistant text for a chat transcript:
    messages = [{"role": "user"|"assistant", "content": "..."}]"""

    def __init__(self, preferred: Optional[str] = None):
        preferred = (preferred or settings.AI_PROVIDER or "anthropic").lower()
        # Preferred provider first, then the rest of the chain as fallbacks
        self.chain = [preferred] + [p for p in PROVIDER_CHAIN if p != preferred]

    async def generate(self, system: str, messages: list[dict], max_tokens: int = 512) -> str:
        last_error: Optional[Exception] = None
        for provider in self.chain:
            try:
                if provider == "anthropic":
                    return await self._anthropic(system, messages, max_tokens)
                if provider == "openai":
                    return await self._openai(system, messages, max_tokens)
                if provider == "ollama":
                    return await self._ollama(system, messages, max_tokens)
            except Exception as exc:  # fall through to the next provider
                last_error = exc
                logger.warning("AI provider %s failed: %s", provider, exc)
        raise AIProviderError(f"All AI providers failed (last: {last_error})")

    async def _anthropic(self, system: str, messages: list[dict], max_tokens: int) -> str:
        if not settings.ANTHROPIC_API_KEY:
            raise AIProviderError("Anthropic API key not configured")
        model = settings.AI_MODEL if settings.AI_PROVIDER == "anthropic" else ANTHROPIC_MODEL_DEFAULT
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "system": system,
                    "messages": messages,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return "".join(
                block["text"] for block in data["content"] if block["type"] == "text"
            )

    async def _openai(self, system: str, messages: list[dict], max_tokens: int) -> str:
        if not settings.OPENAI_API_KEY:
            raise AIProviderError("OpenAI API key not configured")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={
                    "model": OPENAI_MODEL_DEFAULT,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "system", "content": system}, *messages],
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _ollama(self, system: str, messages: list[dict], max_tokens: int) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "stream": False,
                    "messages": [{"role": "system", "content": system}, *messages],
                    "options": {"num_predict": max_tokens},
                },
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]
