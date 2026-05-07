"""
MCP ownership lookup tool.
"""

from __future__ import annotations

import logging

from sqlalchemy import select, or_

from database.engine import get_session_factory
from database.tables import AssetRecord

logger = logging.getLogger(__name__)


async def find_owner(asset_id: str) -> str:
    """Find the owner for a data asset by ID or name."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = select(AssetRecord).where(
            or_(AssetRecord.id == asset_id, AssetRecord.asset_name == asset_id)
        )
        result = await session.execute(stmt)
        asset = result.scalar_one_or_none()

    if not asset:
        return f"Asset not found: {asset_id}"

    owner = asset.owner or "Unassigned"
    return f"Owner for {asset.asset_name}: {owner}"
