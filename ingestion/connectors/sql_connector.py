"""
SQL Connector — Crawls INFORMATION_SCHEMA to extract table/column metadata.

Supports PostgreSQL, MySQL, and SQLite databases.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid5, NAMESPACE_URL

from models.data_asset import (
    AssetType,
    ColumnInfo,
    DataAsset,
    SensitivityLevel,
)

logger = logging.getLogger(__name__)


class SqlConnector:
    """
    Extract metadata from SQL databases via INFORMATION_SCHEMA.
    
    Uses SQLAlchemy for cross-database compatibility.
    """

    def __init__(self, connection_string: str, schema_filter: str | None = None) -> None:
        """
        Args:
            connection_string: SQLAlchemy-compatible connection string
            schema_filter: Optional schema name to limit extraction
        """
        self.connection_string = connection_string
        self.schema_filter = schema_filter

    async def extract_assets(self) -> list[DataAsset]:
        """Extract table and column metadata from the database."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(self.connection_string)
        assets: list[DataAsset] = []

        try:
            async with engine.connect() as conn:
                # Get tables
                tables = await self._get_tables(conn)
                for table_info in tables:
                    columns = await self._get_columns(conn, table_info)
                    asset = self._build_asset(table_info, columns)
                    assets.append(asset)

            logger.info(f"Extracted {len(assets)} assets from SQL database")
        finally:
            await engine.dispose()

        return assets

    async def _get_tables(self, conn: Any) -> list[dict]:
        """Query INFORMATION_SCHEMA.TABLES."""
        from sqlalchemy import text

        query = text("""
            SELECT 
                table_schema,
                table_name,
                table_type
            FROM information_schema.tables
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name
        """)

        if self.schema_filter:
            query = text("""
                SELECT 
                    table_schema,
                    table_name,
                    table_type
                FROM information_schema.tables
                WHERE table_schema = :schema
                ORDER BY table_name
            """)
            result = await conn.execute(query, {"schema": self.schema_filter})
        else:
            result = await conn.execute(query)

        return [
            {
                "schema": row[0],
                "name": row[1],
                "type": row[2],
            }
            for row in result.fetchall()
        ]

    async def _get_columns(self, conn: Any, table_info: dict) -> list[ColumnInfo]:
        """Query INFORMATION_SCHEMA.COLUMNS for a specific table."""
        from sqlalchemy import text

        query = text("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = :schema AND table_name = :table
            ORDER BY ordinal_position
        """)

        result = await conn.execute(
            query,
            {"schema": table_info["schema"], "table": table_info["name"]},
        )

        return [
            ColumnInfo(
                name=row[0],
                data_type=row[1],
                is_nullable=row[2] == "YES",
            )
            for row in result.fetchall()
        ]

    def _build_asset(self, table_info: dict, columns: list[ColumnInfo]) -> DataAsset:
        """Build a DataAsset from table and column info."""
        full_name = f"{table_info['schema']}.{table_info['name']}"
        asset_type = (
            AssetType.VIEW if table_info["type"] == "VIEW" else AssetType.TABLE
        )

        return DataAsset(
            id=str(uuid5(NAMESPACE_URL, f"sql.{full_name}")),
            asset_name=full_name,
            asset_type=asset_type,
            description=f"SQL {asset_type.value}: {full_name} with {len(columns)} columns",
            source_system="sql",
            schema_name=table_info["schema"],
            columns=columns,
            sensitivity=SensitivityLevel.INTERNAL,
        )
