"""
Core DataAsset model — the fundamental unit of metadata in DataContextOS.

Represents any data asset: table, column, dashboard, pipeline, model, etc.
Designed for structured extraction via Pydantic AI.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class AssetType(str, Enum):
    """Types of data assets tracked by the platform."""
    TABLE = "table"
    VIEW = "view"
    COLUMN = "column"
    DASHBOARD = "dashboard"
    PIPELINE = "pipeline"
    MODEL = "model"            # dbt model
    SOURCE = "source"          # dbt source
    API_ENDPOINT = "api_endpoint"
    METRIC = "metric"
    SEED = "seed"
    SNAPSHOT = "snapshot"


class SensitivityLevel(str, Enum):
    """Data sensitivity classification."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class ColumnInfo(BaseModel):
    """Schema information for a single column."""
    name: str
    data_type: str
    description: Optional[str] = None
    is_nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_ref: Optional[str] = None  # "schema.table.column"
    tags: list[str] = Field(default_factory=list)
    sensitivity: Optional[SensitivityLevel] = None


class DataAsset(BaseModel):
    """
    Core metadata entity representing any data asset in the enterprise.
    
    This is the primary model used for:
    - Structured extraction from raw docs (Pydantic AI)
    - Storage in the metadata database
    - API responses
    - MCP tool results
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    asset_name: str = Field(description="Fully qualified name (e.g., 'analytics.orders')")
    asset_type: AssetType = Field(description="Type of data asset")
    description: str = Field(description="Human-readable description of the asset")
    
    # Ownership & Organization
    owner: Optional[str] = Field(
        default=None, description="Person or team responsible for this asset"
    )
    domain: Optional[str] = Field(
        default=None, description="Business domain (finance, marketing, engineering, etc.)"
    )
    
    # Data Quality Signals
    freshness_sla_hours: Optional[int] = Field(
        default=None, description="Maximum acceptable data staleness in hours"
    )
    last_updated: Optional[datetime] = Field(
        default=None, description="When the data was last refreshed"
    )
    
    # Classification
    tags: list[str] = Field(default_factory=list, description="Descriptive tags")
    sensitivity: SensitivityLevel = Field(
        default=SensitivityLevel.INTERNAL, description="Data sensitivity level"
    )
    
    # Source & Schema
    source_system: str = Field(
        default="unknown", description="Origin system (dbt, postgres, api, docs)"
    )
    database: Optional[str] = Field(default=None, description="Database name")
    schema_name: Optional[str] = Field(default=None, description="Schema name")
    columns: list[ColumnInfo] = Field(
        default_factory=list, description="Column definitions (for tables/views)"
    )
    
    # dbt-specific
    materialized: Optional[str] = Field(
        default=None, description="dbt materialization strategy"
    )
    dbt_tags: list[str] = Field(default_factory=list)
    tests: list[str] = Field(
        default_factory=list, description="dbt tests applied to this asset"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    raw_metadata: dict = Field(
        default_factory=dict, description="Original raw metadata from source"
    )

    def to_embedding_text(self) -> str:
        """Generate text representation for embedding."""
        parts = [
            f"Asset: {self.asset_name}",
            f"Type: {self.asset_type.value}",
            f"Description: {self.description}",
        ]
        if self.owner:
            parts.append(f"Owner: {self.owner}")
        if self.domain:
            parts.append(f"Domain: {self.domain}")
        if self.tags:
            parts.append(f"Tags: {', '.join(self.tags)}")
        if self.columns:
            col_descs = []
            for col in self.columns:
                desc = f"{col.name} ({col.data_type})"
                if col.description:
                    desc += f": {col.description}"
                col_descs.append(desc)
            parts.append(f"Columns: {'; '.join(col_descs)}")
        if self.sensitivity:
            parts.append(f"Sensitivity: {self.sensitivity.value}")
        if self.source_system:
            parts.append(f"Source: {self.source_system}")
        return "\n".join(parts)
