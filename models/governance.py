"""
Governance models — Compliance assessment for data assets.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ComplianceStatus(str, Enum):
    """Overall compliance status."""
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    NOT_ASSESSED = "not_assessed"


class GovernanceCheck(BaseModel):
    """Result of a single governance check."""
    check_name: str
    passed: bool
    details: str
    severity: str = Field(
        default="medium",
        description="low, medium, high, critical"
    )
    remediation: Optional[str] = Field(
        default=None, description="Steps to fix if check failed"
    )


class GovernanceAssessment(BaseModel):
    """
    Full governance assessment for a data asset.
    
    Checks:
    - Has documentation
    - Has defined owner
    - Sensitivity classification set
    - Freshness SLA defined and met
    - Column descriptions present
    - Tests defined and passing
    """
    asset_id: str
    asset_name: str
    status: ComplianceStatus
    checks: list[GovernanceCheck] = Field(default_factory=list)
    score: float = Field(
        ge=0.0, le=1.0,
        description="Governance compliance score (passed checks / total checks)"
    )
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
    recommendations: list[str] = Field(
        default_factory=list,
        description="Prioritized list of improvements"
    )

    @classmethod
    def from_checks(
        cls,
        asset_id: str,
        asset_name: str,
        checks: list[GovernanceCheck],
    ) -> GovernanceAssessment:
        """Create assessment from a list of completed checks."""
        passed = sum(1 for c in checks if c.passed)
        total = len(checks) if checks else 1
        score = round(passed / total, 3)

        if score >= 0.9:
            status = ComplianceStatus.COMPLIANT
        elif score >= 0.5:
            status = ComplianceStatus.PARTIAL
        else:
            status = ComplianceStatus.NON_COMPLIANT

        recommendations = [
            c.remediation
            for c in checks
            if not c.passed and c.remediation
        ]

        return cls(
            asset_id=asset_id,
            asset_name=asset_name,
            status=status,
            checks=checks,
            score=score,
            recommendations=recommendations,
        )
