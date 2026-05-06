"""
dbt Connector — Parses dbt manifest.json to extract data assets and lineage.

Handles models, sources, tests, and their dependency graph.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from models.data_asset import (
    AssetType,
    ColumnInfo,
    DataAsset,
    SensitivityLevel,
)
from models.lineage import LineageEdge, LineageEdgeType

logger = logging.getLogger(__name__)


# Map dbt resource types to our AssetType enum
_DBT_TYPE_MAP = {
    "model": AssetType.MODEL,
    "source": AssetType.SOURCE,
    "seed": AssetType.SEED,
    "snapshot": AssetType.SNAPSHOT,
    "metric": AssetType.METRIC,
}

_SENSITIVITY_MAP = {
    "public": SensitivityLevel.PUBLIC,
    "internal": SensitivityLevel.INTERNAL,
    "confidential": SensitivityLevel.CONFIDENTIAL,
    "restricted": SensitivityLevel.RESTRICTED,
}


class DbtConnector:
    """Parse dbt manifest.json and extract data assets + lineage."""

    def __init__(self, manifest_path: str | Path) -> None:
        self.manifest_path = Path(manifest_path)
        self._manifest: dict[str, Any] = {}

    def load(self) -> None:
        """Load the manifest file."""
        with open(self.manifest_path) as f:
            self._manifest = json.load(f)
        logger.info(f"Loaded dbt manifest from {self.manifest_path}")

    def extract_assets(self) -> list[DataAsset]:
        """Extract all data assets from the manifest."""
        assets: list[DataAsset] = []

        # Process nodes (models, seeds, snapshots)
        for node_id, node in self._manifest.get("nodes", {}).items():
            asset = self._parse_node(node_id, node)
            if asset:
                assets.append(asset)

        # Process sources
        for source_id, source in self._manifest.get("sources", {}).items():
            asset = self._parse_source(source_id, source)
            if asset:
                assets.append(asset)

        logger.info(f"Extracted {len(assets)} assets from dbt manifest")
        return assets

    def extract_lineage(self) -> list[LineageEdge]:
        """Extract lineage edges from the manifest dependency graph."""
        edges: list[LineageEdge] = []

        for node_id, node in self._manifest.get("nodes", {}).items():
            depends_on = node.get("depends_on", {}).get("nodes", [])
            for dep_id in depends_on:
                edges.append(
                    LineageEdge(
                        source_id=self._clean_id(dep_id),
                        target_id=self._clean_id(node_id),
                        edge_type=LineageEdgeType.DEPENDS_ON,
                    )
                )

        logger.info(f"Extracted {len(edges)} lineage edges from dbt manifest")
        return edges

    def _parse_node(self, node_id: str, node: dict) -> DataAsset | None:
        """Parse a dbt node into a DataAsset."""
        resource_type = node.get("resource_type", "model")
        asset_type = _DBT_TYPE_MAP.get(resource_type)
        if not asset_type:
            return None

        meta = node.get("meta", {})
        columns = self._parse_columns(node.get("columns", {}))

        sensitivity_str = meta.get("sensitivity", "internal")
        sensitivity = _SENSITIVITY_MAP.get(sensitivity_str, SensitivityLevel.INTERNAL)

        return DataAsset(
            id=self._clean_id(node_id),
            asset_name=f"{node.get('schema', '')}.{node.get('name', '')}",
            asset_type=asset_type,
            description=node.get("description", ""),
            owner=meta.get("owner"),
            domain=meta.get("domain"),
            freshness_sla_hours=meta.get("freshness_sla_hours"),
            tags=node.get("tags", []),
            sensitivity=sensitivity,
            source_system="dbt",
            database=node.get("database"),
            schema_name=node.get("schema"),
            materialized=node.get("config", {}).get("materialized"),
            dbt_tags=node.get("tags", []),
            columns=columns,
            raw_metadata=node,
        )

    def _parse_source(self, source_id: str, source: dict) -> DataAsset | None:
        """Parse a dbt source into a DataAsset."""
        meta = source.get("meta", {})

        return DataAsset(
            id=self._clean_id(source_id),
            asset_name=f"{source.get('schema', '')}.{source.get('name', '')}",
            asset_type=AssetType.SOURCE,
            description=source.get("description", ""),
            owner=meta.get("owner"),
            domain=meta.get("domain"),
            freshness_sla_hours=meta.get("freshness_sla_hours"),
            tags=[],
            sensitivity=SensitivityLevel.INTERNAL,
            source_system="dbt",
            database=source.get("database"),
            schema_name=source.get("schema"),
            raw_metadata=source,
        )

    def _parse_columns(self, columns_dict: dict) -> list[ColumnInfo]:
        """Parse dbt columns into ColumnInfo objects."""
        columns: list[ColumnInfo] = []
        for col_name, col_data in columns_dict.items():
            columns.append(
                ColumnInfo(
                    name=col_data.get("name", col_name),
                    data_type=col_data.get("data_type", "unknown"),
                    description=col_data.get("description"),
                )
            )
        return columns

    @staticmethod
    def _clean_id(raw_id: str) -> str:
        """Create a clean, stable ID from a dbt unique_id."""
        # e.g. "model.ecommerce_analytics.stg_orders" -> "stg_orders"
        parts = raw_id.split(".")
        return parts[-1] if parts else raw_id
