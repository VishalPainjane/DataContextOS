"""
LLM Provider abstraction — supports Anthropic, OpenAI, Gemini (free), and Ollama (free).

Usage:
    provider = get_llm_provider()
    response = await provider.generate("What tables exist in the finance domain?")
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

from config import settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> str:
        """Generate a text response from the LLM."""
        ...

    async def generate_structured(
        self, prompt: str, schema: type[T], system_prompt: str = "", **kwargs: Any
    ) -> T:
        """
        Generate a structured response that conforms to a Pydantic model.
        
        Default implementation: ask LLM for JSON output, then parse.
        Providers can override with native structured output support.
        """
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        structured_prompt = (
            f"{prompt}\n\n"
            f"Respond with valid JSON that conforms to this schema:\n"
            f"```json\n{schema_json}\n```\n"
            f"Return ONLY the JSON object, no other text."
        )
        raw = await self.generate(structured_prompt, system_prompt=system_prompt, **kwargs)

        # Extract JSON from response (handle markdown code blocks)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first and last lines (```json and ```)
            json_lines = [l for l in lines[1:] if not l.strip().startswith("```")]
            cleaned = "\n".join(json_lines)

        return schema.model_validate_json(cleaned)


class GeminiProvider(LLMProvider):
    """Google Gemini — free tier with generous limits."""

    def __init__(self) -> None:
        try:
            from google import genai
            self.client = genai.Client(api_key=settings.google_api_key)
        except ImportError:
            raise ImportError("Install google-genai: pip install google-genai")

    async def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> str:
        from google.genai import types
        
        contents = prompt
        config = types.GenerateContentConfig(
            temperature=kwargs.get("temperature", settings.llm_temperature),
            max_output_tokens=kwargs.get("max_tokens", settings.llm_max_tokens),
        )
        if system_prompt:
            config.system_instruction = system_prompt

        response = self.client.models.generate_content(
            model=settings.llm_model,
            contents=contents,
            config=config,
        )
        return response.text or ""


class OllamaProvider(LLMProvider):
    """Ollama — fully local, zero cost."""

    def __init__(self) -> None:
        try:
            import ollama
            self._ollama = ollama
        except ImportError:
            raise ImportError("Install ollama: pip install ollama")

    async def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self._ollama.chat(
            model=settings.llm_model,
            messages=messages,
            options={
                "temperature": kwargs.get("temperature", settings.llm_temperature),
                "num_predict": kwargs.get("max_tokens", settings.llm_max_tokens),
            },
        )
        return response["message"]["content"]


class AnthropicProvider(LLMProvider):
    """Anthropic Claude — production quality."""

    def __init__(self) -> None:
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        except ImportError:
            raise ImportError("Install anthropic: pip install anthropic")

    async def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> str:
        msg = await self.client.messages.create(
            model=settings.llm_model,
            max_tokens=kwargs.get("max_tokens", settings.llm_max_tokens),
            temperature=kwargs.get("temperature", settings.llm_temperature),
            system=system_prompt or "You are a helpful data governance assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text


class OpenAIProvider(LLMProvider):
    """OpenAI GPT — production quality."""

    def __init__(self) -> None:
        try:
            import openai
            self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        except ImportError:
            raise ImportError("Install openai: pip install openai")

    async def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=kwargs.get("temperature", settings.llm_temperature),
            max_tokens=kwargs.get("max_tokens", settings.llm_max_tokens),
        )
        return response.choices[0].message.content or ""


# ── Factory ──────────────────────────────────────────────────────

_provider_cache: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    """
    Get the configured LLM provider.
    
    Reads DCOS_LLM_PROVIDER from settings and returns
    the appropriate provider instance.
    """
    global _provider_cache
    if _provider_cache is not None:
        return _provider_cache

    match settings.llm_provider:
        case "gemini":
            _provider_cache = GeminiProvider()
        case "ollama":
            _provider_cache = OllamaProvider()
        case "anthropic":
            _provider_cache = AnthropicProvider()
        case "openai":
            _provider_cache = OpenAIProvider()
        case _:
            raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")

    logger.info(f"LLM provider initialized: {settings.llm_provider} ({settings.llm_model})")
    return _provider_cache
