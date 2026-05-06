"""
Search models — Request/response types for asset search operations.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from models.trust_score import TrustScore


class SearchResult(BaseModel):
    """A single search result with relevance and trust information."""
    asset_id: str
    asset_name: str
    asset_type: str
    description: str
    domain: Optional[str] = None
    owner: Optional[str] = None
    relevance_score: float = Field(
        ge=0.0, le=1.0, description="Semantic similarity score"
    )
    trust_score: Optional[TrustScore] = None
    source_system: str = "unknown"
    tags: list[str] = Field(default_factory=list)
    snippet: str = Field(
        default="", description="Relevant text snippet from the matched context"
    )


class SearchResponse(BaseModel):
    """Response from a search query across data assets."""
    query: str
    results: list[SearchResult] = Field(default_factory=list)
    total: int = 0
    answer: Optional[str] = Field(
        default=None, description="AI-synthesized answer to the query"
    )
    citations: list[str] = Field(
        default_factory=list, description="Source references for the answer"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall confidence in the response"
    )
    filters_applied: dict = Field(
        default_factory=dict, description="Filters that were applied to the search"
    )
