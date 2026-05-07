"""
Search API Router — Handles RAG and basic searches.
"""

from fastapi import APIRouter, Depends

from api.schemas import QueryRequest, QueryResponse
from context_layer.rag_engine import RagEngine

router = APIRouter(tags=["Search"])

@router.post("/search", response_model=QueryResponse)
async def search_assets(request: QueryRequest):
    """Search for data assets using the Agentic RAG Engine."""
    engine = RagEngine()
    response = await engine.run(
        request.query,
        top_k=request.top_k,
        domain=request.domain,
        asset_type=request.asset_type,
    )
    
    return QueryResponse(
        query=response.query,
        answer=response.answer or "",
        results=response.results,
        citations=response.citations,
        confidence=response.confidence
    )
