"""Arize Phoenix observability setup — best-effort, never blocks the app."""
from __future__ import annotations

import os


def setup_observability() -> None:
    try:
        import phoenix as px
        from openinference.instrumentation.langchain import LangChainInstrumentor

        px.launch_app(port=int(os.getenv("PHOENIX_PORT", "6006")))
        LangChainInstrumentor().instrument()
    except Exception:
        pass
