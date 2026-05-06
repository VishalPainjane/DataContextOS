"""
Reranker abstraction — supports Cohere (paid) and HuggingFace cross-encoder (free/local).

Rerankers improve retrieval precision by re-scoring candidate documents
against the query using a cross-encoder model.

Usage:
    reranker = get_reranker()
    ranked = await reranker.rerank(query="...", documents=["doc1", "doc2"], top_n=5)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import NamedTuple

from config import settings

logger = logging.getLogger(__name__)


class RankedResult(NamedTuple):
    """A reranked document with its relevance score."""
    index: int
    score: float
    text: str


class Reranker(ABC):
    """Abstract base class for rerankers."""

    @abstractmethod
    async def rerank(
        self, query: str, documents: list[str], top_n: int = 5
    ) -> list[RankedResult]:
        """
        Rerank documents by relevance to query.
        
        Returns top_n results sorted by descending relevance score.
        """
        ...


class CrossEncoderReranker(Reranker):
    """
    HuggingFace cross-encoder — free, runs locally.
    
    Default: cross-encoder/ms-marco-MiniLM-L-6-v2
    """

    def __init__(self) -> None:
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(settings.reranker_model)
        except ImportError:
            raise ImportError(
                "Install sentence-transformers: pip install sentence-transformers"
            )

    async def rerank(
        self, query: str, documents: list[str], top_n: int = 5
    ) -> list[RankedResult]:
        # Cross-encoder expects pairs of (query, document)
        pairs = [(query, doc) for doc in documents]
        scores = self.model.predict(pairs)

        # Create indexed results and sort by score
        results = [
            RankedResult(index=i, score=float(score), text=doc)
            for i, (score, doc) in enumerate(zip(scores, documents))
        ]
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_n]


class CohereReranker(Reranker):
    """Cohere Rerank v3.5 — paid, high quality."""

    def __init__(self) -> None:
        try:
            import cohere
            self.client = cohere.ClientV2(settings.cohere_api_key)
        except ImportError:
            raise ImportError("Install cohere: pip install cohere")

    async def rerank(
        self, query: str, documents: list[str], top_n: int = 5
    ) -> list[RankedResult]:
        response = self.client.rerank(
            model="rerank-v3.5",
            query=query,
            documents=documents,
            top_n=top_n,
        )
        return [
            RankedResult(
                index=r.index,
                score=r.relevance_score,
                text=documents[r.index],
            )
            for r in response.results
        ]


class NoOpReranker(Reranker):
    """Pass-through reranker — returns documents in original order."""

    async def rerank(
        self, query: str, documents: list[str], top_n: int = 5
    ) -> list[RankedResult]:
        return [
            RankedResult(index=i, score=1.0 - (i * 0.01), text=doc)
            for i, doc in enumerate(documents[:top_n])
        ]


# ── Factory ──────────────────────────────────────────────────────

_reranker_cache: Reranker | None = None


def get_reranker() -> Reranker:
    """Get the configured reranker."""
    global _reranker_cache
    if _reranker_cache is not None:
        return _reranker_cache

    match settings.reranker:
        case "cross-encoder":
            _reranker_cache = CrossEncoderReranker()
        case "cohere":
            _reranker_cache = CohereReranker()
        case "none":
            _reranker_cache = NoOpReranker()
        case _:
            raise ValueError(f"Unknown reranker: {settings.reranker}")

    logger.info(f"Reranker initialized: {settings.reranker}")
    return _reranker_cache
