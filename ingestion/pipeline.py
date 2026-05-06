"""
Ingestion Pipeline — Orchestrates metadata ingestion from all sources.

Connects: Connectors → Chunking → Embedding → Storage
"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import select, text

from config import settings
from database.engine import get_session_factory, init_db
from database.tables import AssetRecord, LineageEdgeRecord, EmbeddingRecord
from ingestion.connectors.dbt_connector import DbtConnector
from ingestion.connectors.markdown_connector import MarkdownConnector
from ingestion.connectors.openapi_connector import OpenApiConnector
from models.data_asset import DataAsset
from models.lineage import LineageEdge
from providers.embeddings import get_embedding_provider

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Main ingestion pipeline for DataContextOS.
    
    Orchestrates:
    1. Loading metadata from connectors (dbt, docs, SQL)
    2. Generating embeddings
    3. Storing in database + vector store
    """

    def __init__(self) -> None:
        self.assets: list[DataAsset] = []
        self.lineage_edges: list[LineageEdge] = []

    async def run(self, source_dir: str | Path) -> dict:
        """
        Run the full ingestion pipeline on a source directory.
        
        Args:
            source_dir: Path to directory containing metadata sources
            
        Returns:
            Summary dict with counts
        """
        source_dir = Path(source_dir)
        logger.info(f"Starting ingestion from {source_dir}")

        # Initialize database
        await init_db()

        # Step 1: Extract from all connectors
        self._extract_from_sources(source_dir)

        # Step 2: Deduplicate by asset name
        self._deduplicate()

        # Step 3: Generate embeddings and store
        await self._embed_and_store()

        summary = {
            "assets_ingested": len(self.assets),
            "lineage_edges": len(self.lineage_edges),
            "source_dir": str(source_dir),
        }
        logger.info(f"Ingestion complete: {summary}")
        return summary

    def _extract_from_sources(self, source_dir: Path) -> None:
        """Run all connectors on the source directory."""
        # dbt manifest
        manifest_path = source_dir / "dbt_manifest.json"
        if manifest_path.exists():
            connector = DbtConnector(manifest_path)
            connector.load()
            self.assets.extend(connector.extract_assets())
            self.lineage_edges.extend(connector.extract_lineage())
            logger.info(f"dbt: {len(self.assets)} assets, {len(self.lineage_edges)} edges")

        # Markdown docs
        docs_dir = source_dir / "docs"
        if docs_dir.exists():
            connector = MarkdownConnector(docs_dir)  # type: ignore[assignment]
            doc_assets = connector.extract_assets()
            self.assets.extend(doc_assets)
            logger.info(f"Docs: {len(doc_assets)} assets from markdown")

        # OpenAPI Specs
        openapi_dir = source_dir / "openapi"
        if openapi_dir.exists():
            for spec_file in openapi_dir.glob("*.*"):
                if spec_file.suffix in (".json", ".yaml", ".yml"):
                    api_connector = OpenApiConnector(spec_file)
                    api_connector.load()
                    api_assets = api_connector.extract_assets()
                    self.assets.extend(api_assets)
                    logger.info(f"OpenAPI: {len(api_assets)} assets from {spec_file.name}")

    def _deduplicate(self) -> None:
        """Deduplicate assets by name, preferring dbt over docs."""
        seen: dict[str, DataAsset] = {}
        for asset in self.assets:
            name = asset.asset_name.lower().strip().replace("`", "")
            if name not in seen or asset.source_system == "dbt":
                seen[name] = asset
        self.assets = list(seen.values())
        logger.info(f"After dedup: {len(self.assets)} unique assets")

    async def _embed_and_store(self) -> None:
        """Generate embeddings and store everything in the database."""
        embedding_provider = get_embedding_provider()
        session_factory = get_session_factory()

        # Generate embedding texts
        texts = [asset.to_embedding_text() for asset in self.assets]

        # Batch embed
        logger.info(f"Embedding {len(texts)} asset texts...")
        embeddings = await embedding_provider.embed_batch(texts)

        async with session_factory() as session:
            async with session.begin():
                # Store assets
                for asset in self.assets:
                    record = AssetRecord(
                        id=str(asset.id),
                        asset_name=asset.asset_name,
                        asset_type=asset.asset_type.value,
                        description=asset.description,
                        owner=asset.owner,
                        domain=asset.domain,
                        freshness_sla_hours=asset.freshness_sla_hours,
                        last_updated=asset.last_updated,
                        sensitivity=asset.sensitivity.value,
                        source_system=asset.source_system,
                        database_name=asset.database,
                        schema_name=asset.schema_name,
                        materialized=asset.materialized,
                        tags=asset.tags,
                        columns_json=[c.model_dump() for c in asset.columns],
                        dbt_tags=asset.dbt_tags,
                        tests=asset.tests,
                        raw_metadata=asset.raw_metadata,
                        embedding_text=asset.to_embedding_text(),
                    )
                    await session.merge(record)

                # Store lineage edges
                for edge in self.lineage_edges:
                    record = LineageEdgeRecord(
                        source_id=edge.source_id,
                        target_id=edge.target_id,
                        edge_type=edge.edge_type.value,
                        transformation=edge.transformation,
                    )
                    # Use merge to handle duplicates
                    existing = await session.execute(
                        select(LineageEdgeRecord).where(
                            LineageEdgeRecord.source_id == edge.source_id,
                            LineageEdgeRecord.target_id == edge.target_id,
                        )
                    )
                    if not existing.scalar_one_or_none():
                        session.add(record)

                # Store embeddings
                for i, (asset, embedding) in enumerate(zip(self.assets, embeddings)):
                    emb_record = EmbeddingRecord(
                        asset_id=str(asset.id),
                        chunk_text=texts[i],
                        chunk_index=0,
                        embedding_model=settings.embedding_model,
                        embedding_json=embedding,
                        metadata_json={
                            "asset_name": asset.asset_name,
                            "asset_type": asset.asset_type.value,
                            "domain": asset.domain,
                            "owner": asset.owner,
                        },
                    )
                    session.add(emb_record)

        logger.info(
            f"Stored {len(self.assets)} assets, "
            f"{len(self.lineage_edges)} edges, "
            f"{len(embeddings)} embeddings"
        )


async def run_ingestion(source_dir: str = "sample_data") -> dict:
    """Convenience function to run the ingestion pipeline."""
    pipeline = IngestionPipeline()
    return await pipeline.run(source_dir)
