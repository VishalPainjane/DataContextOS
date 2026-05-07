"""
API Schemas — Pydantic models for request/response.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from models.search import SearchResult
from models.trust_score import TrustScore
from models.data_asset import DataAsset, AssetType, SensitivityLevel
from models.lineage import LineageGraph, LineageNode, LineageEdge
from models.governance import GovernanceAssessment, GovernanceCheck, ComplianceStatus

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    domain: Optional[str] = None
    asset_type: Optional[str] = None

class QueryResponse(BaseModel):
    query: str
    answer: str
    results: List[SearchResult]
    citations: List[str]
    confidence: float

class AssetListResponse(BaseModel):
    assets: List[SearchResult]
    total: int

class GovernanceStats(BaseModel):
    total_assets: int
    avg_trust_score: float
    compliant_percentage: float
    assets_by_status: Dict[str, int]
    assets_by_domain: Dict[str, int]

class GovernanceAttentionItem(BaseModel):
    asset_id: str
    asset_name: str
    domain: Optional[str] = None
    owner: Optional[str] = None
    issue: str
    severity: str

class GovernanceAttentionResponse(BaseModel):
    items: List[GovernanceAttentionItem]

class LineageResponse(LineageGraph):
    """Lineage response model, extending the core graph model."""
    pass
