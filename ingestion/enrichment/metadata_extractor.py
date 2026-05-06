"""
Metadata Extractor — Uses Pydantic AI to extract structured metadata from raw text.
"""

from __future__ import annotations

import logging
from typing import Optional

from pydantic_ai import Agent

from models.data_asset import DataAsset, AssetType, SensitivityLevel
from providers.llm import get_llm_provider

logger = logging.getLogger(__name__)

# Basic Pydantic AI Agent for extracting DataAsset details from raw text
metadata_agent = Agent(
    'gemini-2.0-flash', # Ideally this should be configurable or use our provider logic
    result_type=DataAsset,
    system_prompt=(
        "You are an expert data steward. Your job is to extract structured metadata "
        "about a data asset from the provided text documentation. "
        "Only extract information that is explicitly stated. Do not guess or hallucinate. "
        "If a field is not mentioned, leave it null/empty. "
        "Make sure to identify the correct AssetType."
    )
)

class MetadataExtractor:
    """Enrich raw descriptions into structured DataAsset objects."""

    async def extract_from_text(self, text: str) -> Optional[DataAsset]:
        """Run the AI agent to parse raw text into a DataAsset."""
        try:
            # Pydantic AI takes care of LLM routing and parsing into the result_type
            result = await metadata_agent.run(text)
            return result.data
        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
            return None
