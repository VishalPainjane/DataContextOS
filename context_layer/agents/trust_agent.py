"""
Trust Agent — Evaluates data governance and trust signals.
"""

from __future__ import annotations

import logging

from sqlalchemy import select

from database.engine import get_session_factory
from database.tables import AssetRecord
from models.trust_score import TrustScore, TrustSignals
from trust.score_engine import TrustScoreEngine

logger = logging.getLogger(__name__)

class TrustAgent:
    """Agent responsible for computing and retrieving trust scores."""

    def __init__(self) -> None:
        self.engine = TrustScoreEngine()
        self.session_factory = get_session_factory()

    async def get_trust_score(self, asset_id: str) -> TrustScore | None:
        """Compute the trust score for an asset."""
        async with self.session_factory() as session:
            stmt = select(AssetRecord).where(AssetRecord.id == asset_id)
            res = await session.execute(stmt)
            rec = res.scalar_one_or_none()
            
            if not rec:
                logger.warning(f"Cannot compute trust score: Asset {asset_id} not found")
                return None
                
            # Naive heuristic signal generation based on available metadata
            # In production, these would be derived from actual metrics/logs
            signals = TrustSignals(
                documentation=1.0 if rec.description else 0.0,
                freshness=1.0 if rec.freshness_sla_hours else 0.5,
                ownership=1.0 if rec.owner else 0.0,
                test_coverage=1.0 if rec.tests else 0.0,
                usage=0.8 # Placeholder
            )
            
            return self.engine.compute_score(asset_id, signals)
