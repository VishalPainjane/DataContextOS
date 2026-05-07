"""
MCP search tool.
"""

from __future__ import annotations

import logging

from context_layer.rag_engine import RagEngine

logger = logging.getLogger(__name__)


async def search_assets(query: str) -> str:
    """Search for data assets using natural language."""
    engine = RagEngine()
    response = await engine.run(query)
    return (
        f"Answer: {response.answer}\n"
        f"Citations: {response.citations}\n"
        f"Results found: {response.total}"
    )
