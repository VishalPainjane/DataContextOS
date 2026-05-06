"""
Phoenix Tracer — Local observability and evaluation visualization using Arize Phoenix.
"""

import logging
from config import settings

logger = logging.getLogger(__name__)

def init_phoenix():
    """Initialize Phoenix tracing if enabled."""
    if settings.tracer == "phoenix":
        try:
            import phoenix as px
            from openinference.instrumentation.langchain import LangChainInstrumentor
            
            # Start Phoenix app and instrument
            session = px.launch_app()
            LangChainInstrumentor().instrument()
            
            logger.info(f"Phoenix tracer enabled. View dashboard at: {session.url}")
        except ImportError:
            logger.warning("Failed to initialize Phoenix. Ensure arize-phoenix is installed.")
