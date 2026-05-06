"""
Lineage Agent — Traverses dependency graphs.
"""

from __future__ import annotations

import logging
from typing import List

from sqlalchemy import select

from database.engine import get_session_factory
from database.tables import LineageEdgeRecord, AssetRecord
from models.lineage import LineageEdge, LineageNode, LineageDirection, LineageGraph

logger = logging.getLogger(__name__)

class LineageAgent:
    """Agent responsible for lineage graph traversals."""

    def __init__(self) -> None:
        self.session_factory = get_session_factory()

    async def get_lineage(self, asset_id: str, depth: int = 2) -> LineageGraph:
        """Get the lineage graph for an asset up to `depth`."""
        logger.info(f"Traversing lineage for asset {asset_id} to depth {depth}")
        
        edges: List[LineageEdge] = []
        nodes: List[LineageNode] = []
        visited = set()
        
        async with self.session_factory() as session:
            # First, fetch the root node
            root_stmt = select(AssetRecord).where(AssetRecord.id == asset_id)
            root_res = await session.execute(root_stmt)
            root_rec = root_res.scalar_one_or_none()
            
            if not root_rec:
                return LineageGraph(root_asset_id=asset_id)
                
            nodes.append(LineageNode(
                asset_id=root_rec.id,
                asset_name=root_rec.asset_name,
                asset_type=root_rec.asset_type,
                domain=root_rec.domain,
                owner=root_rec.owner,
                depth=0
            ))
            
            # Simple BFS for lineage
            queue = [(asset_id, 0)]
            visited.add(asset_id)
            
            while queue:
                current_id, current_depth = queue.pop(0)
                
                if current_depth >= depth:
                    continue
                    
                # Find all edges where this is source or target
                edge_stmt = select(LineageEdgeRecord).where(
                    (LineageEdgeRecord.source_id == current_id) | 
                    (LineageEdgeRecord.target_id == current_id)
                )
                
                edge_res = await session.execute(edge_stmt)
                for edge_rec in edge_res.scalars().all():
                    edges.append(LineageEdge(
                        source_id=edge_rec.source_id,
                        target_id=edge_rec.target_id,
                        edge_type=edge_rec.edge_type,
                        transformation=edge_rec.transformation
                    ))
                    
                    next_id = edge_rec.target_id if edge_rec.source_id == current_id else edge_rec.source_id
                    
                    if next_id not in visited:
                        visited.add(next_id)
                        queue.append((next_id, current_depth + 1))
                        
                        # Add node
                        node_stmt = select(AssetRecord).where(AssetRecord.id == next_id)
                        node_res = await session.execute(node_stmt)
                        node_rec = node_res.scalar_one_or_none()
                        
                        if node_rec:
                            nodes.append(LineageNode(
                                asset_id=node_rec.id,
                                asset_name=node_rec.asset_name,
                                asset_type=node_rec.asset_type,
                                domain=node_rec.domain,
                                owner=node_rec.owner,
                                depth=current_depth + 1
                            ))
                            
        return LineageGraph(
            root_asset_id=asset_id,
            nodes=nodes,
            edges=list({(e.source_id, e.target_id): e for e in edges}.values()), # deduplicate
            depth=depth,
            direction=LineageDirection.BOTH
        )
