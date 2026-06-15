"""Arize Phoenix observability setup for the agentic CRAG pipeline.

Phoenix 5+ runs as a standalone server. This module connects to it via OTLP
and registers the LangChain instrumentor so every LLM call and LangGraph node
produces a named span visible at http://localhost:{PHOENIX_PORT}.

If Phoenix is not running or its packages are unavailable, observability is
silently skipped and the app continues normally.
"""
from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

load_dotenv()

_initialized: bool = False
logger = logging.getLogger(__name__)


def setup_observability() -> None:
    """Register Phoenix OTLP endpoint and LangChain instrumentor. Idempotent."""
    global _initialized
    if _initialized:
        return

    port: int = int(os.getenv("PHOENIX_PORT", "6006"))
    endpoint: str = f"http://localhost:{port}/v1/traces"

    try:
        from phoenix.otel import register
        from openinference.instrumentation.langchain import LangChainInstrumentor

        register(project_name="crag-pipeline", endpoint=endpoint)
        LangChainInstrumentor().instrument()
        logger.info("Phoenix observability connected at http://localhost:%d", port)
    except Exception as exc:
        logger.warning("Observability unavailable — skipping Phoenix setup: %s", exc)

    _initialized = True
