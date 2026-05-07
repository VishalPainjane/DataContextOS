"""
Lineage API Router — Handles data asset dependency graphs.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from database.engine import get_session
from database.tables import AssetRecord, LineageEdgeRecord
from api.schemas import LineageResponse, LineageNode, LineageEdge
from models.lineage import LineageDirection

router = APIRouter(tags=["Lineage"])

@router.get("/lineage/{asset_id}", response_model=LineageResponse)
async def get_lineage(
    asset_id: str,
    depth: int = Query(2, ge=1, le=5),
    direction: LineageDirection = LineageDirection.BOTH,
    session: AsyncSession = Depends(get_session)
):
    """Get the lineage graph for a specific data asset."""
    # Check if root asset exists
    root_query = select(AssetRecord).where(AssetRecord.id == asset_id)
    root_result = await session.execute(root_query)
    root_asset = root_result.scalar_one_or_none()
    
    if not root_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    nodes = {}
    edges = []
    
    # Add root node
    nodes[asset_id] = LineageNode(
        asset_id=root_asset.id,
        asset_name=root_asset.asset_name,
        asset_type=root_asset.asset_type,
        domain=root_asset.domain,
        owner=root_asset.owner,
        depth=0
    )
    
    # BFS traversal to find nodes and edges up to requested depth
    current_layer = [asset_id]
    visited_nodes = {asset_id}
    
    for d in range(1, depth + 1):
        if not current_layer:
            break
            
        # Find all edges connected to current layer
        edge_query = select(LineageEdgeRecord)
        if direction == LineageDirection.UPSTREAM:
            edge_query = edge_query.where(LineageEdgeRecord.target_id.in_(current_layer))
        elif direction == LineageDirection.DOWNSTREAM:
            edge_query = edge_query.where(LineageEdgeRecord.source_id.in_(current_layer))
        else: # BOTH
            edge_query = edge_query.where(
                or_(
                    LineageEdgeRecord.source_id.in_(current_layer),
                    LineageEdgeRecord.target_id.in_(current_layer)
                )
            )
            
        edge_result = await session.execute(edge_query)
        layer_edges = edge_result.scalars().all()
        
        next_layer = []
        for e in layer_edges:
            edges.append(LineageEdge(
                source_id=e.source_id,
                target_id=e.target_id,
                edge_type=e.edge_type,
                transformation=e.transformation
            ))
            
            # Find the "other" node in the edge
            other_id = e.target_id if e.source_id in current_layer else e.source_id
            
            if other_id not in visited_nodes:
                visited_nodes.add(other_id)
                next_layer.append(other_id)
                
                # Fetch node details
                node_query = select(AssetRecord).where(AssetRecord.id == other_id)
                node_result = await session.execute(node_query)
                node_rec = node_result.scalar_one_or_none()
                
                if node_rec:
                    nodes[other_id] = LineageNode(
                        asset_id=node_rec.id,
                        asset_name=node_rec.asset_name,
                        asset_type=node_rec.asset_type,
                        domain=node_rec.domain,
                        owner=node_rec.owner,
                        depth=d
                    )
        
        current_layer = next_layer

    return LineageResponse(
        root_asset_id=asset_id,
        nodes=list(nodes.values()),
        edges=edges,
        depth=depth,
        direction=direction
    )
