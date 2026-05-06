"""
SQLAlchemy table definitions for DataContextOS.

Stores data assets, embeddings, lineage edges, and trust scores.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class AssetRecord(Base):
    """Persisted data asset metadata."""

    __tablename__ = "assets"

    id = Column(String(64), primary_key=True)
    asset_name = Column(String(255), nullable=False, index=True)
    asset_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False, default="")
    owner = Column(String(255), nullable=True, index=True)
    domain = Column(String(100), nullable=True, index=True)
    freshness_sla_hours = Column(Integer, nullable=True)
    last_updated = Column(DateTime, nullable=True)
    sensitivity = Column(String(50), default="internal")
    source_system = Column(String(100), default="unknown")
    database_name = Column(String(255), nullable=True)
    schema_name = Column(String(255), nullable=True)
    materialized = Column(String(50), nullable=True)
    
    # JSON fields for complex data
    tags = Column(JSON, default=list)
    columns_json = Column(JSON, default=list)
    dbt_tags = Column(JSON, default=list)
    tests = Column(JSON, default=list)
    raw_metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Embedding reference
    embedding_text = Column(Text, nullable=True)

    # Relationships
    trust_scores = relationship(
        "TrustScoreRecord", back_populates="asset", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_assets_domain_type", "domain", "asset_type"),
        Index("ix_assets_owner_domain", "owner", "domain"),
    )


class LineageEdgeRecord(Base):
    """Directed edge in the data lineage graph."""

    __tablename__ = "lineage_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(
        String(64),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_id = Column(
        String(64),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    edge_type = Column(String(50), default="depends_on")
    transformation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_lineage_source_target", "source_id", "target_id", unique=True),
    )


class TrustScoreRecord(Base):
    """Persisted trust score computation."""

    __tablename__ = "trust_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(
        String(64),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score = Column(Float, nullable=False)
    label = Column(String(20), nullable=False)
    
    # Individual signals
    documentation_score = Column(Float, default=0.0)
    freshness_score = Column(Float, default=0.0)
    ownership_score = Column(Float, default=0.0)
    test_coverage_score = Column(Float, default=0.0)
    usage_score = Column(Float, default=0.0)
    
    explanation = Column(Text, default="")
    computed_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    asset = relationship("AssetRecord", back_populates="trust_scores")


class EmbeddingRecord(Base):
    """Vector embeddings for semantic search (used when not using pgvector/chroma directly)."""

    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(
        String(64),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, default=0)
    embedding_model = Column(String(100), nullable=False)
    # Embedding vector stored as JSON for SQLite compatibility
    # For pgvector, this would be a Vector column
    embedding_json = Column(JSON, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_embeddings_asset_chunk", "asset_id", "chunk_index"),
    )
