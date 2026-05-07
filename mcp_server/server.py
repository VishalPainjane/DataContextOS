"""
MCP Server — Exposes FastMCP tools for LLM agents.
"""

from __future__ import annotations

import logging
from fastmcp import FastMCP

from mcp_server.tools.search import search_assets as search_assets_tool
from mcp_server.tools.lineage import get_lineage as get_lineage_tool
from mcp_server.tools.trust import get_trust_score as get_trust_score_tool
from mcp_server.tools.owner import find_owner as find_owner_tool
from mcp_server.tools.schema import get_schema as get_schema_tool
from mcp_server.tools.governance import assess_governance as assess_governance_tool

logger = logging.getLogger(__name__)

mcp = FastMCP("DataContextOS")

# Register tools while keeping named exports for tests.
search_assets = mcp.tool()(search_assets_tool)
get_lineage = mcp.tool()(get_lineage_tool)
get_trust_score = mcp.tool()(get_trust_score_tool)
find_owner = mcp.tool()(find_owner_tool)
get_schema = mcp.tool()(get_schema_tool)
assess_governance = mcp.tool()(assess_governance_tool)

if __name__ == "__main__":
    mcp.run()
