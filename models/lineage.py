"""
Lineage models — DAG representation of data asset dependencies.

Supports upstream (what feeds this) and downstream (what depends on this) traversal.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LineageDirection(str, Enum):
    """Direction of lineage traversal."""
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    BOTH = "both"


class LineageEdgeType(str, Enum):
    """Type of relationship between assets."""
    DEPENDS_ON = "depends_on"         # Model depends on source/model
    FEEDS_INTO = "feeds_into"         # Source feeds into model
    DERIVED_FROM = "derived_from"     # View derived from table
    TESTED_BY = "tested_by"           # Asset tested by test
    EXPOSES = "exposes"               # Dashboard exposes model
    TRANSFORMS = "transforms"         # Pipeline transforms data


class LineageNode(BaseModel):
    """A node in the lineage graph representing a data asset."""
    asset_id: str
    asset_name: str
    asset_type: str
    domain: Optional[str] = None
    owner: Optional[str] = None
    depth: int = Field(
        default=0, description="Distance from the queried asset (0 = the asset itself)"
    )


class LineageEdge(BaseModel):
    """A directed edge in the lineage graph."""
    source_id: str = Field(description="Upstream asset ID")
    target_id: str = Field(description="Downstream asset ID")
    edge_type: LineageEdgeType = Field(default=LineageEdgeType.DEPENDS_ON)
    transformation: Optional[str] = Field(
        default=None, description="Description of how data is transformed"
    )


class LineageGraph(BaseModel):
    """
    Complete lineage graph for an asset query.
    
    Contains all nodes and edges within the requested depth,
    centered on the queried asset.
    """
    root_asset_id: str = Field(description="The asset this lineage is centered on")
    nodes: list[LineageNode] = Field(default_factory=list)
    edges: list[LineageEdge] = Field(default_factory=list)
    depth: int = Field(default=2, description="Maximum traversal depth")
    direction: LineageDirection = Field(default=LineageDirection.BOTH)

    @property
    def upstream_nodes(self) -> list[LineageNode]:
        """Get all upstream (source) nodes."""
        upstream_ids = {e.source_id for e in self.edges if e.target_id == self.root_asset_id}
        return [n for n in self.nodes if n.asset_id in upstream_ids]

    @property
    def downstream_nodes(self) -> list[LineageNode]:
        """Get all downstream (dependent) nodes."""
        downstream_ids = {e.target_id for e in self.edges if e.source_id == self.root_asset_id}
        return [n for n in self.nodes if n.asset_id in downstream_ids]

    def to_adjacency_dict(self) -> dict[str, list[str]]:
        """Convert to adjacency list for graph algorithms."""
        adj: dict[str, list[str]] = {}
        for edge in self.edges:
            adj.setdefault(edge.source_id, []).append(edge.target_id)
        return adj
