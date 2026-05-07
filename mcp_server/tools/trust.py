"""
MCP trust score tool.
"""

from __future__ import annotations

import logging

from context_layer.agents.trust_agent import TrustAgent

logger = logging.getLogger(__name__)


async def get_trust_score(asset_id: str) -> str:
    """Get the composite trust score and governance signals for an asset."""
    agent = TrustAgent()
    score = await agent.get_trust_score(asset_id)
    if not score:
        return f"No trust score available for {asset_id}"
    return (
        f"Trust Score: {score.score} ({score.label.value})\n"
        f"Explanation: {score.explanation}"
    )
