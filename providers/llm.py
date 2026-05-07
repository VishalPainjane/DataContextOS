"""
LLM Provider abstraction — supports Anthropic, OpenAI, Gemini (free), and Ollama (free).

Usage:
    provider = get_llm_provider()
    response = await provider.generate("What tables exist in the finance domain?")
"""

from __future__ import annotations

import json
import logging
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
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

        try:
            response = self.client.models.generate_content(
                model=settings.llm_model,
                contents=contents,
                config=config,
            )
            return response.text or ""
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                logger.warning(f"Gemini API quota exhausted: {e}")
                raise
            logger.error(f"Gemini generation failed: {e}")
            raise


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


class FallbackProvider(LLMProvider):
    """A provider that tries a primary provider and falls back to another on failure."""

    def __init__(self, primary: LLMProvider, secondary: LLMProvider) -> None:
        self.primary = primary
        self.secondary = secondary

    async def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> str:
        try:
            return await self.primary.generate(prompt, system_prompt, **kwargs)
        except Exception as e:
            logger.warning(f"Primary LLM failed, falling back to secondary: {e}")
            return await self.secondary.generate(prompt, system_prompt, **kwargs)

    async def generate_structured(
        self, prompt: str, schema: type[T], system_prompt: str = "", **kwargs: Any
    ) -> T:
        try:
            return await self.primary.generate_structured(prompt, schema, system_prompt, **kwargs)
        except Exception as e:
            logger.warning(f"Primary LLM failed (structured), falling back to secondary: {e}")
            return await self.secondary.generate_structured(prompt, schema, system_prompt, **kwargs)


class CachedLLMProvider(LLMProvider):
    """A provider that caches responses to disk."""

    def __init__(self, base: LLMProvider, cache_dir: str = "./data/llm_cache") -> None:
        self.base = base
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, prompt: str, system_prompt: str, **kwargs: Any) -> str:
        data = f"{prompt}:{system_prompt}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(data.encode()).hexdigest()

    async def generate(self, prompt: str, system_prompt: str = "", **kwargs: Any) -> str:
        key = self._get_cache_key(prompt, system_prompt, **kwargs)
        cache_file = self.cache_dir / f"{key}.txt"

        if cache_file.exists():
            logger.debug("LLM cache hit")
            return cache_file.read_text(encoding="utf-8")

        response = await self.base.generate(prompt, system_prompt, **kwargs)
        cache_file.write_text(response, encoding="utf-8")
        return response

    async def generate_structured(
        self, prompt: str, schema: type[T], system_prompt: str = "", **kwargs: Any
    ) -> T:
        key = self._get_cache_key(prompt, system_prompt, schema=schema.__name__, **kwargs)
        cache_file = self.cache_dir / f"{key}.json"

        if cache_file.exists():
            logger.debug("LLM structured cache hit")
            return schema.model_validate_json(cache_file.read_text(encoding="utf-8"))

        result = await self.base.generate_structured(prompt, schema, system_prompt, **kwargs)
        cache_file.write_text(result.model_dump_json(), encoding="utf-8")
        return result


# ── Factory ──────────────────────────────────────────────────────

_provider_cache: LLMProvider | None = None


def _create_provider(name: str) -> LLMProvider:
    """Helper to create a specific provider instance."""
    if name == "gemini":
        return GeminiProvider()
    elif name == "ollama":
        return OllamaProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "openai":
        return OpenAIProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {name}")


def get_llm_provider() -> LLMProvider:
    """
    Get the configured LLM provider with optional fallback and caching.
    """
    global _provider_cache
    if _provider_cache is not None:
        return _provider_cache

    primary = _create_provider(settings.llm_provider)
    
    if settings.llm_fallback_provider and settings.llm_fallback_provider != "none":
        secondary = _create_provider(settings.llm_fallback_provider)
        provider = FallbackProvider(primary, secondary)
        logger.info(
            f"LLM initialized with fallback: {settings.llm_provider} -> {settings.llm_fallback_provider}"
        )
    else:
        provider = primary
        logger.info(f"LLM provider initialized: {settings.llm_provider} ({settings.llm_model})")

    # Wrap in cache
    _provider_cache = CachedLLMProvider(provider)
    return _provider_cache
