"""Arize Phoenix observability setup for the agentic CRAG pipeline.

Call setup_observability() once at Streamlit app startup.
After this call, every LangGraph node execution, LLM call, and
Chroma retriever call is captured as a named OpenTelemetry span
in the Phoenix UI at http://localhost:{PHOENIX_PORT}.
"""
from __future__ import annotations

import os

import phoenix as px
from dotenv import load_dotenv
from openinference.instrumentation.langchain import LangChainInstrumentor

load_dotenv()

_initialized: bool = False


def setup_observability() -> None:
    """Launch Phoenix in-process and register LangChain instrumentor. Idempotent.

    Reads:
        PHOENIX_PORT      — Phoenix UI port (default: 6006)
        PHOENIX_TRACE_DIR — trace storage directory (default: ./phoenix_traces)

    After this call:
        - px.active_session() returns a non-None session
        - All LangChain LLM, retriever, and LangGraph node calls produce spans
        - Traces are persisted to PHOENIX_TRACE_DIR across sessions
    """
    global _initialized
    if _initialized:
        return

    port: int = int(os.getenv("PHOENIX_PORT", "6006"))
    trace_dir: str = os.getenv("PHOENIX_TRACE_DIR", "./phoenix_traces")

    # Ensure trace storage directory exists before Phoenix reads it
    os.makedirs(trace_dir, exist_ok=True)

    # Phoenix reads PHOENIX_WORKING_DIR at launch_app() time
    os.environ["PHOENIX_WORKING_DIR"] = trace_dir

    px.launch_app(port=port, notebook_environment="streamlit")
    LangChainInstrumentor().instrument()

    _initialized = True
