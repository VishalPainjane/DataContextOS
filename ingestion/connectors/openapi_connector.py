"""
OpenAPI Connector — Extracts metadata from OpenAPI/Swagger spec files.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from uuid import uuid5, NAMESPACE_URL

import yaml

from models.data_asset import AssetType, DataAsset, SensitivityLevel

logger = logging.getLogger(__name__)

class OpenApiConnector:
    """Parse OpenAPI specifications to extract API endpoints as DataAssets."""

    def __init__(self, spec_path: str | Path) -> None:
        self.spec_path = Path(spec_path)
        self._spec: dict[str, Any] = {}

    def load(self) -> None:
        """Load the OpenAPI spec file (JSON or YAML)."""
        content = self.spec_path.read_text(encoding="utf-8")
        if self.spec_path.suffix in (".yaml", ".yml"):
            self._spec = yaml.safe_load(content)
        else:
            self._spec = json.loads(content)
        logger.info(f"Loaded OpenAPI spec from {self.spec_path}")

    def extract_assets(self) -> list[DataAsset]:
        """Extract API endpoints as data assets."""
        assets: list[DataAsset] = []
        
        if not self._spec:
            return assets

        info = self._spec.get("info", {})
        api_title = info.get("title", "Unknown API")
        
        paths = self._spec.get("paths", {})
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() not in ("get", "post", "put", "patch", "delete"):
                    continue
                
                asset = self._parse_endpoint(api_title, path, method, operation)
                if asset:
                    assets.append(asset)

        logger.info(f"Extracted {len(assets)} API endpoints from OpenAPI spec")
        return assets

    def _parse_endpoint(self, api_title: str, path: str, method: str, operation: dict) -> DataAsset:
        """Parse a single API endpoint operation into a DataAsset."""
        endpoint_name = f"{method.upper()} {path}"
        description = operation.get("summary", "")
        if operation.get("description"):
            description += f" - {operation['description']}"
            
        tags = operation.get("tags", [])
        
        return DataAsset(
            id=str(uuid5(NAMESPACE_URL, f"openapi.{api_title}.{method}.{path}")),
            asset_name=endpoint_name,
            asset_type=AssetType.API_ENDPOINT,
            description=description.strip(),
            domain=tags[0] if tags else "engineering",
            tags=tags,
            sensitivity=SensitivityLevel.INTERNAL,
            source_system="openapi",
            raw_metadata={"operationId": operation.get("operationId", "")},
        )
