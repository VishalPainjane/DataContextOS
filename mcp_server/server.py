"""
MCP Server — Exposes FastMCP tools for LLM agents.
"""

from __future__ import annotations

import logging
from fastmcp import FastMCP

from context_layer.rag_engine import RagEngine
from context_layer.agents.lineage_agent import LineageAgent
from context_layer.agents.trust_agent import TrustAgent

logger = logging.getLogger(__name__)

mcp = FastMCP("DataContextOS", description="Metadata Intelligence MCP Server")

@mcp.tool()
async def search_assets(query: str) -> str:
    """Search for data assets using natural language. Use this to find tables, models, or pipelines."""
    engine = RagEngine()
    response = await engine.run(query)
    return f"Answer: {response.answer}\nCitations: {response.citations}\nResults found: {response.total}"

@mcp.tool()
async def get_lineage(asset_id: str, depth: int = 2) -> str:
    """Get the upstream and downstream lineage graph for a specific asset."""
    agent = LineageAgent()
    graph = await agent.get_lineage(asset_id, depth)
    
    nodes_info = "\n".join([f"- {n.asset_name} ({n.asset_type})" for n in graph.nodes])
    return f"Lineage for {asset_id} (Depth {depth}):\nNodes:\n{nodes_info}\nEdges count: {len(graph.edges)}"

@mcp.tool()
async def get_trust_score(asset_id: str) -> str:
    """Get the composite trust score and governance signals for an asset."""
    agent = TrustAgent()
    score = await agent.get_trust_score(asset_id)
    if not score:
        return f"No trust score available for {asset_id}"
    return f"Trust Score: {score.score} ({score.label.value})\nExplanation: {score.explanation}"

if __name__ == "__main__":
    mcp.run()
