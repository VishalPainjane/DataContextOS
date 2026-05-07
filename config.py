"""
DataContextOS Configuration — Pydantic Settings with dual-mode support.

Loads from .env file and environment variables. Supports both
production (paid APIs) and free-tier (local/free services) modes.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RunMode(str, Enum):
    """Deployment mode — controls which providers are used."""
    PROD = "prod"
    FREE = "free"


class Settings(BaseSettings):
    """
    Central configuration for DataContextOS.
    
    All settings can be overridden via environment variables prefixed with DCOS_
    or via a .env file in the project root.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Core ──────────────────────────────────────────────────────
    mode: RunMode = Field(default=RunMode.FREE, alias="DCOS_MODE")
    debug: bool = Field(default=False, alias="DCOS_DEBUG")

    # ── LLM Provider ─────────────────────────────────────────────
    llm_provider: Literal["anthropic", "openai", "gemini", "ollama"] = Field(
        default="gemini", alias="DCOS_LLM_PROVIDER"
    )
    llm_model: str = Field(default="gemini-2.0-flash", alias="DCOS_LLM_MODEL")
    llm_fallback_provider: Literal["anthropic", "openai", "gemini", "ollama", "none"] = Field(
        default="ollama", alias="DCOS_LLM_FALLBACK_PROVIDER"
    )
    llm_fallback_model: str = Field(default="llama3", alias="DCOS_LLM_FALLBACK_MODEL")
    llm_temperature: float = Field(default=0.1, alias="DCOS_LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=4096, alias="DCOS_LLM_MAX_TOKENS")

    # API Keys
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    ollama_base_url: str = Field(
        default="http://localhost:11434", alias="OLLAMA_BASE_URL"
    )

    # ── Embedding Provider ───────────────────────────────────────
    embedding_provider: Literal["openai", "huggingface"] = Field(
        default="huggingface", alias="DCOS_EMBEDDING_PROVIDER"
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2", alias="DCOS_EMBEDDING_MODEL"
    )

    # ── Vector Store ─────────────────────────────────────────────
    vector_store: Literal["pgvector", "chroma"] = Field(
        default="chroma", alias="DCOS_VECTOR_STORE"
    )
    chroma_path: str = Field(default="./data/chroma_db", alias="DCOS_CHROMA_PATH")

    # ── Database ─────────────────────────────────────────────────
    database: Literal["postgresql", "sqlite"] = Field(
        default="sqlite", alias="DCOS_DATABASE"
    )
    sqlite_path: str = Field(
        default="./data/datacontextos.db", alias="DCOS_SQLITE_PATH"
    )
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/datacontextos",
        alias="DATABASE_URL",
    )

    # ── Reranker ─────────────────────────────────────────────────
    reranker: Literal["cohere", "cross-encoder", "none"] = Field(
        default="cross-encoder", alias="DCOS_RERANKER"
    )
    reranker_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        alias="DCOS_RERANKER_MODEL",
    )
    cohere_api_key: str = Field(default="", alias="COHERE_API_KEY")

    # ── Tracing / Observability ──────────────────────────────────
    tracer: Literal["langsmith", "phoenix", "console", "none"] = Field(
        default="console", alias="DCOS_TRACER"
    )
    langsmith_api_key: str = Field(default="", alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(
        default="datacontextos", alias="LANGSMITH_PROJECT"
    )

    # ── Server ───────────────────────────────────────────────────
    api_host: str = Field(default="0.0.0.0", alias="DCOS_API_HOST")
    api_port: int = Field(default=8000, alias="DCOS_API_PORT")
    mcp_host: str = Field(default="0.0.0.0", alias="DCOS_MCP_HOST")
    mcp_port: int = Field(default=8001, alias="DCOS_MCP_PORT")

    # ── Trust Score ──────────────────────────────────────────────
    trust_trusted_threshold: float = Field(
        default=0.8, alias="DCOS_TRUST_TRUSTED_THRESHOLD"
    )
    trust_review_threshold: float = Field(
        default=0.6, alias="DCOS_TRUST_REVIEW_THRESHOLD"
    )
    trust_caution_threshold: float = Field(
        default=0.4, alias="DCOS_TRUST_CAUTION_THRESHOLD"
    )

    # ── Computed Properties ──────────────────────────────────────

    @computed_field  # type: ignore[prop-decorator]
    @property
    def effective_database_url(self) -> str:
        """Returns the correct database URL based on mode."""
        if self.database == "sqlite":
            path = Path(self.sqlite_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite+aiosqlite:///{path.resolve()}"
        return self.database_url

    @computed_field  # type: ignore[prop-decorator]
    @property
    def embedding_dimensions(self) -> int:
        """Returns embedding dimensions based on the chosen model."""
        dims_map = {
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return dims_map.get(self.embedding_model, 384)

    def is_free_mode(self) -> bool:
        """Check if running in free (zero-cost) mode."""
        return self.mode == RunMode.FREE

    def validate_api_keys(self) -> list[str]:
        """Return list of warnings for missing API keys based on current providers."""
        warnings: list[str] = []
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            warnings.append("ANTHROPIC_API_KEY is required for Anthropic LLM provider")
        if self.llm_provider == "openai" and not self.openai_api_key:
            warnings.append("OPENAI_API_KEY is required for OpenAI LLM provider")
        if self.llm_provider == "gemini" and not self.google_api_key:
            warnings.append("GOOGLE_API_KEY is required for Gemini LLM provider")
        if self.embedding_provider == "openai" and not self.openai_api_key:
            warnings.append("OPENAI_API_KEY is required for OpenAI embeddings")
        if self.reranker == "cohere" and not self.cohere_api_key:
            warnings.append("COHERE_API_KEY is required for Cohere reranker")
        if self.tracer == "langsmith" and not self.langsmith_api_key:
            warnings.append("LANGSMITH_API_KEY is required for LangSmith tracing")
        return warnings


def get_settings() -> Settings:
    """
    Factory function to create a Settings instance.
    Caches internally to avoid re-reading .env on every call.
    """
    return Settings()  # type: ignore[call-arg]


# Module-level singleton for convenience
settings = get_settings()
