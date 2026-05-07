"""
Vector Store Wrapper — Interfaces with ChromaDB and underlying DB.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.engine import get_session_factory
from database.tables import AssetRecord
from providers.embeddings import get_embedding_provider
from providers.reranker import get_reranker
from models.search import SearchResult

logger = logging.getLogger(__name__)

class VectorStoreWrapper:
    """
    Wraps vector search functionality, supporting ChromaDB and fallback search.
    """

    def __init__(self) -> None:
        self.embedding_provider = get_embedding_provider()
        self.reranker = get_reranker()
        self.session_factory = get_session_factory()
        
        # Initialize Chroma
        if settings.vector_store == "chroma":
            chroma_path = Path(settings.chroma_path)
            chroma_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(
                path=str(chroma_path),
                settings=ChromaSettings(allow_reset=True)
            )
            self.collection = self.chroma_client.get_or_create_collection(
                name="datacontextos_assets"
            )
            logger.info(f"ChromaDB initialized at {chroma_path}")
        else:
            self.chroma_client = None
            self.collection = None

    async def add_assets(self, assets: List[Any], embeddings: List[List[float]]) -> None:
        """Add assets and their embeddings to the vector store."""
        if self.collection:
            ids = [str(a.id) for a in assets]
            documents = [a.to_embedding_text() for a in assets]
            metadatas = [
                {
                    "asset_name": a.asset_name,
                    "asset_type": a.asset_type.value,
                    "domain": a.domain or "unknown",
                    "owner": a.owner or "unknown"
                } for a in assets
            ]
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Added {len(ids)} assets to ChromaDB")

    async def search(
        self,
        query: str,
        domain: str | None = None,
        asset_type: str | None = None,
        top_k: int = 5,
    ) -> List[SearchResult]:
        """Search for assets matching the query."""
        
        logger.info(f"Searching vector store for: {query}")
        
        if self.collection:
            # 1. Semantic Search via Chroma
            query_embedding = await self.embedding_provider.embed_text(query)
            
            where = {}
            if domain:
                where["domain"] = domain
            if asset_type:
                where["asset_type"] = asset_type
                
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k * 2, # Fetch more for reranking
                where=where if where else None
            )
            
            if not results["ids"] or not results["ids"][0]:
                return []
                
            # Fetch full records from DB to populate SearchResult
            async with self.session_factory() as session:
                asset_ids = results["ids"][0]
                stmt = select(AssetRecord).where(AssetRecord.id.in_(asset_ids))
                res = await session.execute(stmt)
                records_map = {r.id: r for r in res.scalars().all()}
                
            # Create docs for reranking
            records = []
            docs = []
            for i, asset_id in enumerate(results["ids"][0]):
                if asset_id in records_map:
                    rec = records_map[asset_id]
                    records.append(rec)
                    docs.append(results["documents"][0][i])
                    
            if not docs:
                return []
                
            # 2. Rerank results
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
            
        else:
            # Fallback to basic DB fetch and rerank
            async with self.session_factory() as session:
                stmt = select(AssetRecord)
                if domain:
                    stmt = stmt.where(AssetRecord.domain == domain)
                if asset_type:
                    stmt = stmt.where(AssetRecord.asset_type == asset_type)
                result = await session.execute(stmt)
                records = result.scalars().all()
                
            if not records:
                return []

            docs = [(r.asset_name + " - " + r.description) for r in records]
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
