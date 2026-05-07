"""
Assets API Router — Handles asset retrieval and metadata.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database.engine import get_session
from database.tables import AssetRecord, TrustScoreRecord
from api.schemas import DataAsset, SearchResult, AssetListResponse
from models.trust_score import TrustScore

router = APIRouter(tags=["Assets"])

@router.get("/assets", response_model=AssetListResponse)
async def list_assets(
    domain: Optional[str] = None,
    asset_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session)
):
    """List data assets with optional filtering."""
    query = select(AssetRecord)
    
    if domain:
        query = query.where(AssetRecord.domain == domain)
    if asset_type:
        query = query.where(AssetRecord.asset_type == asset_type)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.execute(count_query)
    total_count = total.scalar() or 0
    
    # Get paginated results
    query = query.limit(limit).offset(offset)
    result = await session.execute(query)
    records = result.scalars().all()
    
    assets = []
    for rec in records:
        assets.append(SearchResult(
            asset_id=rec.id,
            asset_name=rec.asset_name,
            asset_type=rec.asset_type,
            domain=rec.domain or "",
            owner=rec.owner or "Unassigned",
            description=rec.description,
            snippet=""
        ))
        
    return AssetListResponse(assets=assets, total=total_count)

@router.get("/assets/{asset_id}", response_model=DataAsset)
async def get_asset(
    asset_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get full details for a specific data asset."""
    query = select(AssetRecord).where(AssetRecord.id == asset_id)
    result = await session.execute(query)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Convert SQLAlchemy record to Pydantic model
    return DataAsset(
        id=record.id,
        asset_name=record.asset_name,
        asset_type=record.asset_type,
        description=record.description,
        owner=record.owner,
        domain=record.domain,
        freshness_sla_hours=record.freshness_sla_hours,
        last_updated=record.last_updated,
        sensitivity=record.sensitivity,
        source_system=record.source_system,
        database=record.database_name,
        schema_name=record.schema_name,
        columns=record.columns_json,
        tags=record.tags,
        materialized=record.materialized,
        dbt_tags=record.dbt_tags,
        tests=record.tests,
        raw_metadata=record.raw_metadata,
        created_at=record.created_at,
        updated_at=record.updated_at
    )

@router.get("/assets/{asset_id}/trust", response_model=TrustScore)
async def get_asset_trust_score(
    asset_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get the latest trust score for an asset."""
    query = select(TrustScoreRecord).where(TrustScoreRecord.asset_id == asset_id).order_by(TrustScoreRecord.computed_at.desc())
    result = await session.execute(query)
    record = result.scalar_one_or_none()
    
    if not record:
        # Return a default neutral score if none exists
        return TrustScore(
            asset_id=asset_id,
            score=0.5,
            label="REVIEW",
            explanation="No trust score has been computed for this asset yet."
        )
    
    return TrustScore(
        asset_id=record.asset_id,
        score=record.score,
        label=record.label,
        documentation_score=record.documentation_score,
        freshness_score=record.freshness_score,
        ownership_score=record.ownership_score,
        test_coverage_score=record.test_coverage_score,
        usage_score=record.usage_score,
        explanation=record.explanation,
        computed_at=record.computed_at
    )
