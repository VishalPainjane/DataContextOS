"""
MCP schema lookup tool.
"""

from __future__ import annotations

import logging

from sqlalchemy import select, or_

from database.engine import get_session_factory
from database.tables import AssetRecord

logger = logging.getLogger(__name__)


async def get_schema(table_name: str) -> str:
    """Get the schema for a table by asset name or ID."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = select(AssetRecord).where(
            or_(AssetRecord.id == table_name, AssetRecord.asset_name == table_name)
        )
        result = await session.execute(stmt)
        asset = result.scalar_one_or_none()

    if not asset:
        return f"Asset not found: {table_name}"

    columns = asset.columns_json or []
    if not columns:
        return f"No schema available for {asset.asset_name}"

    lines = []
    for col in columns:
        name = col.get("name") or "unknown"
        data_type = col.get("data_type") or col.get("type") or "unknown"
        description = col.get("description")
        if description:
            lines.append(f"- {name} ({data_type}): {description}")
        else:
            lines.append(f"- {name} ({data_type})")

    return f"Schema for {asset.asset_name}:\n" + "\n".join(lines)
