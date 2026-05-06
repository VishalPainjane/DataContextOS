"""
LangSmith Tracer — Configures and wraps LangSmith for observability.
"""

import os
import logging
from typing import Any, Callable
from functools import wraps

from config import settings

logger = logging.getLogger(__name__)

def init_langsmith():
    """Initialize LangSmith tracing if enabled."""
    if settings.tracer == "langsmith":
        if not settings.langsmith_api_key:
            logger.warning("LangSmith API key is missing. Tracing will not be recorded.")
            return

        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
        logger.info(f"LangSmith tracing enabled for project: {settings.langsmith_project}")

def trace_agent(name: str | None = None) -> Callable:
    """Decorator to trace specific agent methods."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # If using LangChain/LangGraph under the hood, the context is picked up automatically
            # Otherwise we'd manually wrap it in a LangSmith run here.
            # For simplicity in this implementation, we assume auto-tracing is set.
            return await func(*args, **kwargs)
        return wrapper
    return decorator
