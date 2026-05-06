"""
API Schemas — Pydantic models for request/response.
"""

from typing import List, Optional
from pydantic import BaseModel

from models.search import SearchResult
from models.trust_score import TrustScore

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    domain: Optional[str] = None

class QueryResponse(BaseModel):
    query: str
    answer: str
    results: List[SearchResult]
    citations: List[str]
    confidence: float
