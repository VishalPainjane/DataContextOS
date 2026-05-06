"""
Tests for MCP Tools.
"""

import pytest
from mcp_server.server import search_assets, get_lineage, get_trust_score

@pytest.mark.asyncio
async def test_search_assets():
    """Test the search assets tool."""
    # Assuming mocked DB or empty DB fallback
    result = await search_assets("test query")
    assert isinstance(result, str)
    assert "Answer:" in result

@pytest.mark.asyncio
async def test_get_lineage():
    """Test the lineage tool."""
    result = await get_lineage("fake-id")
    assert isinstance(result, str)
    assert "Lineage for fake-id" in result

@pytest.mark.asyncio
async def test_get_trust_score():
    """Test the trust score tool."""
    result = await get_trust_score("fake-id")
    assert isinstance(result, str)
