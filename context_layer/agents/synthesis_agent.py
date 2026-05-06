"""
Synthesis Agent — Generates final answer from retrieved context.
"""

from __future__ import annotations

import logging
from typing import List

from pydantic import BaseModel, Field

from providers.llm import get_llm_provider
from models.search import SearchResult

logger = logging.getLogger(__name__)

class SynthesisResult(BaseModel):
    """The synthesized output from the agent."""
    answer: str = Field(description="The final synthesized answer to the user query")
    citations: List[str] = Field(description="List of asset names used to answer")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")

class SynthesisAgent:
    """Agent responsible for synthesizing a response from context."""

    def __init__(self) -> None:
        self.llm = get_llm_provider()

    async def synthesize(self, query: str, context: List[SearchResult]) -> SynthesisResult:
        """Synthesize a natural language answer from the context."""
        
        context_str = "\n\n".join([
            f"Asset: {c.asset_name}\nType: {c.asset_type}\nDesc: {c.description}\nSnippet: {c.snippet}"
            for c in context
        ])
        
        prompt = (
            f"User Query: {query}\n\n"
            f"Context:\n{context_str}\n\n"
            "Using ONLY the context provided, answer the user query. "
            "If the context doesn't contain the answer, say so explicitly. "
            "Do not hallucinate."
        )
        
        system_prompt = "You are an expert data assistant. Answer queries clearly and accurately based on context."
        
        try:
            result = await self.llm.generate_structured(prompt, SynthesisResult, system_prompt=system_prompt)
            return result
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return SynthesisResult(
                answer="Failed to synthesize an answer due to an internal error.",
                citations=[],
                confidence=0.0
            )
