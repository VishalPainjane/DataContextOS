"""
Markdown Connector — Parses markdown documentation to extract data asset context.

Handles team docs, data dictionaries, and wiki pages.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from models.data_asset import AssetType, DataAsset

logger = logging.getLogger(__name__)


class MarkdownConnector:
    """Parse markdown documentation files into data asset context."""

    def __init__(self, docs_dir: str | Path) -> None:
        self.docs_dir = Path(docs_dir)

    def extract_assets(self) -> list[DataAsset]:
        """Extract data assets from all markdown files in the directory."""
        assets: list[DataAsset] = []

        if not self.docs_dir.exists():
            logger.warning(f"Docs directory not found: {self.docs_dir}")
            return assets

        for md_file in self.docs_dir.rglob("*.md"):
            file_assets = self._parse_file(md_file)
            assets.extend(file_assets)

        logger.info(f"Extracted {len(assets)} assets from markdown docs")
        return assets

    def _parse_file(self, file_path: Path) -> list[DataAsset]:
        """Parse a single markdown file for data asset references."""
        content = file_path.read_text(encoding="utf-8")
        assets: list[DataAsset] = []

        # Extract tables from markdown tables (common in data docs)
        tables = self._extract_tables(content)
        for table_data in tables:
            asset = self._table_to_asset(table_data, file_path.stem)
            if asset:
                assets.append(asset)

        # If no tables found, treat the whole doc as context for a single asset
        if not assets:
            asset_id = str(uuid5(NAMESPACE_URL, str(file_path)))
            assets.append(
                DataAsset(
                    id=asset_id,
                    asset_name=file_path.stem.replace("_", " ").title(),
                    asset_type=AssetType.MODEL,
                    description=self._get_first_paragraph(content),
                    source_system="docs",
                    tags=["documentation"],
                    raw_metadata={"file": str(file_path), "content": content[:2000]},
                )
            )

        return assets

    def _extract_tables(self, content: str) -> list[dict]:
        """Extract markdown tables as list of dicts."""
        tables: list[dict] = []
        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if "|" in line and i + 1 < len(lines) and "---" in lines[i + 1]:
                headers = [h.strip() for h in line.split("|") if h.strip()]
                i += 2  # skip separator
                while i < len(lines) and "|" in lines[i]:
                    values = [v.strip() for v in lines[i].split("|") if v.strip()]
                    if len(values) == len(headers):
                        row = dict(zip(headers, values))
                        tables.append(row)
                    i += 1
            else:
                i += 1
        return tables

    def _table_to_asset(self, row: dict, source_name: str) -> DataAsset | None:
        """Convert a markdown table row to a DataAsset if it looks like one."""
        # Look for common column names
        model = row.get("Model", row.get("model", row.get("Table", "")))
        model = re.sub(r"`", "", model)  # strip backticks
        if not model:
            return None

        desc = row.get("Description", row.get("description", ""))
        domain = row.get("Domain", row.get("domain", ""))
        sla = row.get("SLA", row.get("sla", ""))
        owner = row.get("Owner", row.get("owner", ""))

        # Parse SLA hours
        sla_hours = None
        if sla:
            match = re.search(r"(\d+)", sla)
            if match:
                sla_hours = int(match.group(1))

        return DataAsset(
            id=str(uuid5(NAMESPACE_URL, f"docs.{source_name}.{model}")),
            asset_name=model,
            asset_type=AssetType.MODEL,
            description=desc,
            owner=owner or None,
            domain=domain or None,
            freshness_sla_hours=sla_hours,
            source_system="docs",
            tags=["documentation"],
        )

    @staticmethod
    def _get_first_paragraph(content: str) -> str:
        """Extract first non-header paragraph from markdown."""
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("|"):
                return line[:500]
        return ""
