"""
RAG Engine — Wires all agents together using a LangGraph-style workflow.
"""

from __future__ import annotations

import logging
from typing import TypedDict, List, Optional

from context_layer.agents.router_agent import RouterAgent, QueryRoute
from context_layer.agents.retrieval_agent import RetrievalAgent
from context_layer.agents.lineage_agent import LineageAgent
from context_layer.agents.trust_agent import TrustAgent
from context_layer.agents.synthesis_agent import SynthesisAgent
from models.search import SearchResponse, SearchResult

logger = logging.getLogger(__name__)

class ContextState(TypedDict):
    """The state of the RAG graph."""
    query: str
    route: Optional[QueryRoute]
    context: List[SearchResult]
    answer: Optional[str]
    citations: List[str]
    confidence: float

class RagEngine:
    """Orchestrates the entire agentic RAG pipeline."""

    def __init__(self) -> None:
        self.router = RouterAgent()
        self.retriever = RetrievalAgent()
        self.lineage = LineageAgent()
        self.trust = TrustAgent()
        self.synthesizer = SynthesisAgent()

    async def run(
        self,
        query: str,
        top_k: int = 5,
        domain: Optional[str] = None,
        asset_type: Optional[str] = None,
    ) -> SearchResponse:
        """Run the full RAG pipeline for a query."""
        state: ContextState = {
            "query": query,
            "route": None,
            "context": [],
            "answer": None,
            "citations": [],
            "confidence": 0.0
        }

        # 1. Routing
        state["route"] = await self.router.route_query(query)
        
        # 2. Retrieval (We always do some basic retrieval)
        state["context"] = await self.retriever.retrieve(
            query,
            top_k=top_k,
            domain=domain,
            asset_type=asset_type,
        )

        # 3. Specific Agent Actions based on route
        if state["route"] == QueryRoute.LINEAGE:
            # If lineage is requested, optionally expand context by getting lineage for top result
            if state["context"]:
                top_asset = state["context"][0]
                lineage_graph = await self.lineage.get_lineage(top_asset.asset_id)
                logger.info(f"Retrieved lineage with {len(lineage_graph.nodes)} nodes")
                # In a real setup, we'd inject lineage info into the context string
                
        elif state["route"] == QueryRoute.GOVERNANCE:
            if state["context"]:
                top_asset = state["context"][0]
                trust_score = await self.trust.get_trust_score(top_asset.asset_id)
                if trust_score:
                    # Inject trust info into context
                    top_asset.trust_score = trust_score
                    top_asset.description += f"\nTrust Score: {trust_score.score} ({trust_score.label.value})"

        # 4. Synthesis
        if state["context"]:
            synthesis = await self.synthesizer.synthesize(query, state["context"])
            state["answer"] = synthesis.answer
            state["citations"] = synthesis.citations
            state["confidence"] = synthesis.confidence
        else:
            state["answer"] = "I couldn't find any relevant data assets to answer your query."
            state["confidence"] = 0.0

        return SearchResponse(
            query=query,
            results=state["context"],
            total=len(state["context"]),
            answer=state["answer"],
            citations=state["citations"],
            confidence=state["confidence"]
        )
