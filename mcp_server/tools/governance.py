"""
MCP governance assessment tool.
"""

from __future__ import annotations

import logging

from sqlalchemy import select, or_

from database.engine import get_session_factory
from database.tables import AssetRecord
from models.governance import GovernanceAssessment, GovernanceCheck

logger = logging.getLogger(__name__)


async def assess_governance(asset_id: str) -> str:
    """Assess governance compliance for a data asset by ID or name."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = select(AssetRecord).where(
            or_(AssetRecord.id == asset_id, AssetRecord.asset_name == asset_id)
        )
        result = await session.execute(stmt)
        asset = result.scalar_one_or_none()

    if not asset:
        return f"Asset not found: {asset_id}"

    checks = []

    # Owner assigned
    checks.append(
        GovernanceCheck(
            check_name="Owner Assigned",
            passed=bool(asset.owner),
            details=f"Owner: {asset.owner}" if asset.owner else "No owner assigned to this asset.",
            severity="high",
            remediation="Assign a person or team as the owner in the source system.",
        )
    )

    # Description present
    description = asset.description or ""
    checks.append(
        GovernanceCheck(
            check_name="Asset Description",
            passed=len(description) > 20,
            details=f"Description length: {len(description)} chars",
            severity="medium",
            remediation="Provide a clear, detailed description of what this asset represents.",
        )
    )

    # Sensitivity tagged
    sensitivity = asset.sensitivity or "unknown"
    checks.append(
        GovernanceCheck(
            check_name="Sensitivity Classification",
            passed=sensitivity not in {"unknown", ""},
            details=f"Classification: {sensitivity}",
            severity="high",
            remediation="Tag the asset with a sensitivity level (public/internal/confidential/restricted).",
        )
    )

    # Column documentation
    cols = asset.columns_json or []
    undocumented_cols = [c.get("name") for c in cols if not c.get("description")]
    passed_cols = len(undocumented_cols) == 0 if cols else True
    checks.append(
        GovernanceCheck(
            check_name="Column Documentation",
            passed=passed_cols,
            details=(
                f"{len(undocumented_cols)} undocumented columns"
                if undocumented_cols
                else "All columns documented"
            ),
            severity="medium",
            remediation=(
                f"Add descriptions for: {', '.join(undocumented_cols[:3])}..."
                if undocumented_cols
                else None
            ),
        )
    )

    # Freshness SLA
    checks.append(
        GovernanceCheck(
            check_name="Freshness SLA Defined",
            passed=bool(asset.freshness_sla_hours),
            details=(
                f"SLA: {asset.freshness_sla_hours}h"
                if asset.freshness_sla_hours
                else "No freshness SLA defined"
            ),
            severity="low",
            remediation="Define a freshness SLA in metadata or dbt tests.",
        )
    )

    assessment = GovernanceAssessment.from_checks(
        asset_id=asset.id,
        asset_name=asset.asset_name,
        checks=checks,
    )

    lines = [
        f"Governance for {asset.asset_name}: {assessment.status.value} (score {assessment.score})",
        "Checks:",
    ]

    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        line = f"- {check.check_name}: {status} - {check.details}"
        if not check.passed and check.remediation:
            line += f" | Remediation: {check.remediation}"
        lines.append(line)

    return "\n".join(lines)
