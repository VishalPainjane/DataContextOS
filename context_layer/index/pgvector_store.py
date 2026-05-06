"""
Vector Store Wrapper — Interfaces with LlamaIndex and underlying DB.
"""

from __future__ import annotations

import logging
from typing import Any, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.engine import get_session_factory
from database.tables import EmbeddingRecord, AssetRecord
from providers.embeddings import get_embedding_provider
from providers.reranker import get_reranker
from models.search import SearchResult

logger = logging.getLogger(__name__)

class VectorStoreWrapper:
    """
    Wraps vector search functionality.
    
    If using SQLite, falls back to basic filtering/keyword matching,
    or we would implement a chroma-based search here.
    For this implementation plan, we assume we fetch top results based on simple matching
    or using the embedding provider and reranker if available.
    """

    def __init__(self) -> None:
        self.embedding_provider = get_embedding_provider()
        self.reranker = get_reranker()
        self.session_factory = get_session_factory()

    async def search(
        self, query: str, domain: str | None = None, top_k: int = 5
    ) -> List[SearchResult]:
        """Search for assets matching the query."""
        
        # 1. Embed query
        # query_embedding = await self.embedding_provider.embed_text(query)
        # Note: A real implementation would use the query_embedding against pgvector.
        # Since we are supporting free mode (sqlite), we'll do a basic fetch and rerank.
        
        logger.info(f"Searching vector store for: {query}")
        
        async with self.session_factory() as session:
            # Fetch all assets, or filter by domain
            stmt = select(AssetRecord)
            if domain:
                stmt = stmt.where(AssetRecord.domain == domain)
                
            result = await session.execute(stmt)
            records = result.scalars().all()
            
        if not records:
            return []

        # Use Reranker to find the best matches
        docs = [(r.asset_name + " - " + r.description) for r in records]
        
        # We need at least some documents
        if not docs:
            return []
            
        ranked_results = await self.reranker.rerank(query, docs, top_n=top_k)
        
        search_results = []
        for rank in ranked_results:
            rec = records[rank.index]
            search_results.append(
                SearchResult(
                    asset_id=rec.id,
                    asset_name=rec.asset_name,
                    asset_type=rec.asset_type,
                    description=rec.description,
                    domain=rec.domain,
                    owner=rec.owner,
                    relevance_score=rank.score,
                    source_system=rec.source_system,
                    tags=rec.tags,
                    snippet=rank.text[:200]
                )
            )
            
        return search_results
