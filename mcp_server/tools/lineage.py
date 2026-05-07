"""
MCP lineage tool.
"""

from __future__ import annotations

import logging

from context_layer.agents.lineage_agent import LineageAgent

logger = logging.getLogger(__name__)


async def get_lineage(asset_id: str, depth: int = 2) -> str:
    """Get the upstream and downstream lineage graph for a specific asset."""
    agent = LineageAgent()
    graph = await agent.get_lineage(asset_id, depth)

    nodes_info = "\n".join(
        [f"- {n.asset_name} ({n.asset_type})" for n in graph.nodes]
    )
    return (
        f"Lineage for {asset_id} (Depth {depth}):\n"
        f"Nodes:\n{nodes_info}\n"
        f"Edges count: {len(graph.edges)}"
    )
