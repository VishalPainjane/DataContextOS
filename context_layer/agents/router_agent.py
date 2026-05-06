"""
Router Agent — Classifies queries to route to appropriate RAG agents.
"""

from __future__ import annotations

import logging
from enum import Enum
from pydantic import BaseModel, Field

from providers.llm import get_llm_provider

logger = logging.getLogger(__name__)

class QueryRoute(str, Enum):
    """Possible query routes."""
    SIMPLE = "simple"
    LINEAGE = "lineage"
    GOVERNANCE = "governance"

class RouteDecision(BaseModel):
    """Decision made by the router."""
    route: QueryRoute = Field(description="The appropriate route for the query")
    reasoning: str = Field(description="Explanation for why this route was chosen")

class RouterAgent:
    """Agent responsible for routing user queries."""

    def __init__(self) -> None:
        self.llm = get_llm_provider()

    async def route_query(self, query: str) -> QueryRoute:
        """Determine the best route for a given query."""
        prompt = (
            f"Given the user query: '{query}'\n\n"
            "Classify it into one of the following categories:\n"
            "- LINEAGE: The user is asking about data dependencies, upstream sources, or downstream impacts.\n"
            "- GOVERNANCE: The user is asking about trust, quality, owners, or compliance of data.\n"
            "- SIMPLE: The user is asking a basic search question, looking for an asset description or general metadata.\n"
        )
        
        system_prompt = "You are a specialized router agent for a metadata intelligence platform."
        
        try:
            decision = await self.llm.generate_structured(prompt, RouteDecision, system_prompt=system_prompt)
            logger.info(f"Routed query to {decision.route.value} (Reason: {decision.reasoning})")
            return decision.route
        except Exception as e:
            logger.error(f"Routing failed, defaulting to simple: {e}")
            return QueryRoute.SIMPLE
