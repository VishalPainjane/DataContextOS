"""
Retrieval Agent — Performs semantic search for context.
"""

from __future__ import annotations

import logging
from typing import List

from context_layer.index.pgvector_store import VectorStoreWrapper
from models.search import SearchResult

logger = logging.getLogger(__name__)

class RetrievalAgent:
    """Agent responsible for retrieving context from the vector store."""

    def __init__(self) -> None:
        self.store = VectorStoreWrapper()

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        domain: str | None = None,
        asset_type: str | None = None,
    ) -> List[SearchResult]:
        """Retrieve relevant assets for the query."""
        logger.info(f"Retrieving context for query: {query}")
        results = await self.store.search(
            query=query,
            top_k=top_k,
            domain=domain,
            asset_type=asset_type,
        )
        return results
