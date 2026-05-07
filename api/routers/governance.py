"""
Governance API Router — Handles compliance and metadata health checks.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database.engine import get_session
from database.tables import AssetRecord, TrustScoreRecord
from api.schemas import (
    GovernanceStats,
    GovernanceAssessment,
    GovernanceCheck,
    ComplianceStatus,
    GovernanceAttentionResponse,
    GovernanceAttentionItem,
)

router = APIRouter(tags=["Governance"])

@router.get("/governance/stats", response_model=GovernanceStats)
async def get_governance_stats(session: AsyncSession = Depends(get_session)):
    """Get aggregate governance statistics across the portfolio."""
    # Total assets
    count_query = select(func.count(AssetRecord.id))
    count_result = await session.execute(count_query)
    total_assets = count_result.scalar() or 0
    
    # Average trust score
    avg_trust_query = select(func.avg(TrustScoreRecord.score))
    avg_trust_result = await session.execute(avg_trust_query)
    avg_trust_score = float(avg_trust_result.scalar() or 0.0)
    
    # Assets by domain
    domain_query = select(AssetRecord.domain, func.count(AssetRecord.id)).group_by(AssetRecord.domain)
    domain_result = await session.execute(domain_query)
    assets_by_domain = {row[0] or "Unknown": row[1] for row in domain_result.all()}
    
    # Mock some data for compliance status until we have a real background scanner
    assets_by_status = {
        "compliant": int(total_assets * 0.6),
        "partial": int(total_assets * 0.3),
        "non_compliant": total_assets - int(total_assets * 0.9)
    }
    
    return GovernanceStats(
        total_assets=total_assets,
        avg_trust_score=avg_trust_score,
        compliant_percentage=60.0, # Placeholder
        assets_by_status=assets_by_status,
        assets_by_domain=assets_by_domain
    )

@router.get("/governance/attention", response_model=GovernanceAttentionResponse)
async def get_governance_attention(
    limit: int = Query(8, ge=1, le=50),
    session: AsyncSession = Depends(get_session)
):
    """Return assets that need governance attention."""
    query = select(AssetRecord)
    result = await session.execute(query)
    assets = result.scalars().all()

    severity_rank = {"high": 3, "medium": 2, "low": 1}
    items: list[GovernanceAttentionItem] = []

    for asset in assets:
        issues: list[tuple[str, str]] = []
        if not asset.owner:
            issues.append(("high", "Owner missing"))

        description = asset.description or ""
        if len(description) <= 20:
            issues.append(("medium", "Description missing or too short"))

        sensitivity = (asset.sensitivity or "unknown").lower()
        if sensitivity in {"unknown", ""}:
            issues.append(("high", "Sensitivity not tagged"))

        if not asset.freshness_sla_hours:
            issues.append(("low", "Freshness SLA not defined"))

        if not issues:
            continue

        issues.sort(key=lambda issue: severity_rank[issue[0]], reverse=True)
        severity, issue = issues[0]
        items.append(
            GovernanceAttentionItem(
                asset_id=asset.id,
                asset_name=asset.asset_name,
                domain=asset.domain,
                owner=asset.owner,
                issue=issue,
                severity=severity,
            )
        )

    items.sort(key=lambda item: severity_rank.get(item.severity, 0), reverse=True)
    return GovernanceAttentionResponse(items=items[:limit])

@router.get("/governance/{asset_id}", response_model=GovernanceAssessment)
async def get_asset_governance(
    asset_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Perform a real-time governance assessment for a specific asset."""
    query = select(AssetRecord).where(AssetRecord.id == asset_id)
    result = await session.execute(query)
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    checks = []
    
    # Check 1: Owner Assigned
    checks.append(GovernanceCheck(
        check_name="Owner Assigned",
        passed=bool(asset.owner),
        details=f"Owner: {asset.owner}" if asset.owner else "No owner assigned to this asset.",
        severity="high",
        remediation="Assign a person or team as the owner in the source system (e.g. dbt YAML)."
    ))
    
    # Check 2: Description Present
    checks.append(GovernanceCheck(
        check_name="Asset Description",
        passed=len(asset.description) > 20,
        details=f"Description length: {len(asset.description)} chars",
        severity="medium",
        remediation="Provide a clear, detailed description of what this asset represents."
    ))
    
    # Check 3: Sensitivity Tagged
    checks.append(GovernanceCheck(
        check_name="Sensitivity Classification",
        passed=bool(asset.sensitivity and asset.sensitivity != "unknown"),
        details=f"Classification: {asset.sensitivity}",
        severity="high",
        remediation="Tag the asset with a sensitivity level (Public, Internal, Confidential, Restricted)."
    ))
    
    # Check 4: Column Documentation
    cols = asset.columns_json or []
    undocumented_cols = [c.get("name") for c in cols if not c.get("description")]
    passed_cols = len(undocumented_cols) == 0 if cols else True
    checks.append(GovernanceCheck(
        check_name="Column Documentation",
        passed=passed_cols,
        details=f"{len(undocumented_cols)} undocumented columns" if undocumented_cols else "All columns documented",
        severity="medium",
        remediation=f"Add descriptions for: {', '.join(undocumented_cols[:3])}..." if undocumented_cols else None
    ))
    
    # Check 5: Freshness SLA
    checks.append(GovernanceCheck(
        check_name="Freshness SLA Defined",
        passed=bool(asset.freshness_sla_hours),
        details=f"SLA: {asset.freshness_sla_hours}h" if asset.freshness_sla_hours else "No freshness SLA defined",
        severity="low",
        remediation="Define a freshness SLA in dbt tests or metadata."
    ))

    return GovernanceAssessment.from_checks(
        asset_id=asset.id,
        asset_name=asset.asset_name,
        checks=checks
    )
