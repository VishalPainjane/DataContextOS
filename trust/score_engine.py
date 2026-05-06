"""
Trust Score Engine — Computes composite trust scores from signals.
"""

from __future__ import annotations

import logging
from typing import Optional

from models.trust_score import TrustScore, TrustSignals

logger = logging.getLogger(__name__)

class TrustScoreEngine:
    """Computes and evaluates trust scores for data assets."""

    def __init__(self, custom_thresholds: Optional[dict[str, float]] = None) -> None:
        self.thresholds = custom_thresholds or {
            "trusted": 0.8,
            "review": 0.6,
            "caution": 0.4
        }

    def compute_score(self, asset_id: str, signals: TrustSignals) -> TrustScore:
        """
        Compute the composite trust score based on individual signals.
        """
        score = TrustScore.compute(asset_id, signals, self.thresholds)
        logger.debug(f"Computed trust score for {asset_id}: {score.score} ({score.label})")
        return score
