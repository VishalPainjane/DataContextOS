"""
Trust Score Engine — Computes composite trust scores from signals.
"""

from __future__ import annotations

import logging
from typing import Optional
from datetime import datetime, timezone

from models.trust_score import TrustScore, TrustSignals
from models.data_asset import DataAsset

logger = logging.getLogger(__name__)

class TrustScoreEngine:
    """Computes and evaluates trust scores for data assets."""

    def __init__(self, custom_thresholds: Optional[dict[str, float]] = None) -> None:
        self.thresholds = custom_thresholds or {
            "trusted": 0.8,
            "review": 0.6,
            "caution": 0.4,
        }

    def compute_score(self, asset_id: str, signals: TrustSignals) -> TrustScore:
        """Compute the composite trust score from precomputed signals."""
        score = TrustScore.compute(asset_id, signals, self.thresholds)
        logger.debug(f"Computed trust score for {asset_id}: {score.score} ({score.label})")
        return score

    def compute_from_asset(self, asset: DataAsset) -> TrustScore:
        """Compute the composite trust score using asset metadata."""
        signals = self._calculate_signals(asset)
        return self.compute_score(asset.id, signals)

    def _calculate_signals(self, asset: DataAsset) -> TrustSignals:
        """Calculate individual trust signals from asset metadata."""
        
        # 1. Documentation Score
        # Based on description length and column documentation
        doc_score = 0.0
        if asset.description and len(asset.description) > 50:
            doc_score += 0.4
        elif asset.description:
            doc_score += 0.2
            
        if asset.columns:
            documented_cols = sum(1 for col in asset.columns if col.description)
            doc_score += (documented_cols / len(asset.columns)) * 0.6
        else:
            # If no columns (e.g. dashboard), description is more important
            doc_score = min(1.0, doc_score * 2)
            
        # 2. Freshness Score
        fresh_score = 1.0
        if asset.last_updated and asset.freshness_sla_hours:
            now = datetime.now(timezone.utc)
            # Ensure last_updated has timezone
            last_updated = asset.last_updated
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)
                
            age_hours = (now - last_updated).total_seconds() / 3600
            if age_hours > asset.freshness_sla_hours:
                # Penalty for being late
                fresh_score = max(0.0, 1.0 - (age_hours - asset.freshness_sla_hours) / 24)
        elif not asset.last_updated and asset.source_system == "dbt":
            fresh_score = 0.5 # Unknown freshness for dbt asset
            
        # 3. Ownership Score
        owner_score = 0.0
        if asset.owner:
            owner_score += 0.7
            if "@" in asset.owner or "/" in asset.owner: # Team or email
                owner_score += 0.3
        
        # 4. Test Coverage Score
        test_score = 0.0
        if asset.tests:
            # Simple heuristic: more tests = better
            test_score = min(1.0, len(asset.tests) * 0.25)
        elif asset.asset_type.value in ["table", "view"] and asset.source_system == "dbt":
            test_score = 0.0 # dbt tables should have tests
        else:
            test_score = 0.5 # Neutral for non-dbt or non-table assets
            
        # 5. Usage Score (Placeholder - would come from query logs)
        usage_score = 0.7 # Default to a healthy neutral
        
        return TrustSignals(
            documentation=round(min(1.0, doc_score), 2),
            freshness=round(min(1.0, fresh_score), 2),
            ownership=round(min(1.0, owner_score), 2),
            test_coverage=round(min(1.0, test_score), 2),
            usage=round(min(1.0, usage_score), 2)
        )
