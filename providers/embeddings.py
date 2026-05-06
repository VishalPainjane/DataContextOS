"""
Embedding Provider abstraction — supports OpenAI (paid) and HuggingFace (free/local).

Usage:
    provider = get_embedding_provider()
    vector = await provider.embed_text("orders table in finance domain")
    vectors = await provider.embed_batch(["text1", "text2", "text3"])
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from config import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the dimensionality of the embeddings."""
        ...

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string into a vector."""
        ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Embed multiple texts. Default: sequential calls.
        Providers should override for batch efficiency.
        """
        return [await self.embed_text(t) for t in texts]


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """
    HuggingFace sentence-transformers — free, runs locally.
    
    Default model: all-MiniLM-L6-v2 (384 dims, fast, good quality)
    """

    def __init__(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(settings.embedding_model)
            self._dims = self.model.get_sentence_embedding_dimension()
        except ImportError:
            raise ImportError(
                "Install sentence-transformers: pip install sentence-transformers"
            )

    @property
    def dimensions(self) -> int:
        return self._dims  # type: ignore[return-value]

    async def embed_text(self, text: str) -> list[float]:
        # sentence-transformers is synchronous, but fast enough for our use
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True, batch_size=32)
        return embeddings.tolist()


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI text-embedding-3-small — paid, high quality."""

    def __init__(self) -> None:
        try:
            import openai
            self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        except ImportError:
            raise ImportError("Install openai: pip install openai")

    @property
    def dimensions(self) -> int:
        return settings.embedding_dimensions

    async def embed_text(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            model=settings.embedding_model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        # OpenAI supports batch embedding natively
        response = await self.client.embeddings.create(
            model=settings.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]


# ── Factory ──────────────────────────────────────────────────────

_provider_cache: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    """Get the configured embedding provider."""
    global _provider_cache
    if _provider_cache is not None:
        return _provider_cache

    match settings.embedding_provider:
        case "huggingface":
            _provider_cache = HuggingFaceEmbeddingProvider()
        case "openai":
            _provider_cache = OpenAIEmbeddingProvider()
        case _:
            raise ValueError(f"Unknown embedding provider: {settings.embedding_provider}")

    logger.info(
        f"Embedding provider initialized: {settings.embedding_provider} "
        f"({settings.embedding_model}, {_provider_cache.dimensions}d)"
    )
    return _provider_cache
