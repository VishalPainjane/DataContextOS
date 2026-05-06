"""
Trust Score model — composite governance signal for data assets.

Computes a weighted score from 5 trust signals:
- Documentation Coverage (0.25)
- Freshness (0.30)
- Ownership (0.20)
- Test Coverage (0.15)
- Usage (0.10)
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TrustLabel(str, Enum):
    """Human-readable trust classification."""
    TRUSTED = "trusted"       # >= 0.8
    REVIEW = "review"         # >= 0.6
    CAUTION = "caution"       # >= 0.4
    UNKNOWN = "unknown"       # < 0.4


class TrustSignals(BaseModel):
    """Individual trust signal scores (each 0.0 to 1.0)."""
    documentation: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Are columns and asset documented?"
    )
    freshness: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Is data within its SLA?"
    )
    ownership: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Is there a named owner and team?"
    )
    test_coverage: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="dbt test pass rate"
    )
    usage: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Is this asset actively queried?"
    )


class TrustScore(BaseModel):
    """
    Composite trust score for a data asset.
    
    The final score is a weighted average of 5 signals,
    mapped to a human-readable label.
    """
    asset_id: str
    score: float = Field(ge=0.0, le=1.0, description="Composite trust score")
    label: TrustLabel
    signals: TrustSignals
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    explanation: str = Field(
        default="", description="Human-readable explanation of the score"
    )

    @classmethod
    def compute(
        cls,
        asset_id: str,
        signals: TrustSignals,
        thresholds: dict[str, float] | None = None,
    ) -> TrustScore:
        """
        Compute a trust score from individual signals.
        
        Args:
            asset_id: The asset identifier
            signals: Individual trust signal scores
            thresholds: Override default label thresholds
        """
        weights = {
            "documentation": 0.25,
            "freshness": 0.30,
            "ownership": 0.20,
            "test_coverage": 0.15,
            "usage": 0.10,
        }
        
        weighted_score = (
            signals.documentation * weights["documentation"]
            + signals.freshness * weights["freshness"]
            + signals.ownership * weights["ownership"]
            + signals.test_coverage * weights["test_coverage"]
            + signals.usage * weights["usage"]
        )
        
        score = round(weighted_score, 3)
        
        # Determine label
        t = thresholds or {}
        trusted_t = t.get("trusted", 0.8)
        review_t = t.get("review", 0.6)
        caution_t = t.get("caution", 0.4)
        
        if score >= trusted_t:
            label = TrustLabel.TRUSTED
        elif score >= review_t:
            label = TrustLabel.REVIEW
        elif score >= caution_t:
            label = TrustLabel.CAUTION
        else:
            label = TrustLabel.UNKNOWN
        
        # Generate explanation
        explanations: list[str] = []
        if signals.freshness < 0.5:
            explanations.append("Data freshness is below acceptable threshold")
        if signals.documentation < 0.5:
            explanations.append("Documentation coverage is insufficient")
        if signals.ownership < 0.5:
            explanations.append("No clear ownership defined")
        if signals.test_coverage < 0.5:
            explanations.append("Test coverage is low")
        if not explanations:
            explanations.append("All trust signals are within acceptable range")
        
        return cls(
            asset_id=asset_id,
            score=score,
            label=label,
            signals=signals,
            explanation="; ".join(explanations),
        )
