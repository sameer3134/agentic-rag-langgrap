"""Unit tests for app.py.

Run with: pytest tests/test_app.py -v
No OPENAI_API_KEY or live Phoenix server required.
"""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestAppErrorHandling:
    def test_graph_exception_displays_st_error(self, tmp_path, monkeypatch):
        """If the CRAG graph raises, app.py must call st.error and not crash."""
        monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
        monkeypatch.setenv("PHOENIX_PORT", "6006")
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))
        # Provide a dummy API key so langchain_openai imports don't fail
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Stub out the phoenix package entirely before anything imports it —
        # arize-phoenix requires pandas which may not be installed in CI.
        phoenix_stub = MagicMock()
        monkeypatch.setitem(sys.modules, "phoenix", phoenix_stub)
        # Also stub sub-modules that phoenix's __init__ imports transitively
        for sub in (
            "phoenix.inferences",
            "phoenix.inferences.fixtures",
            "openinference",
            "openinference.instrumentation",
            "openinference.instrumentation.langchain",
        ):
            monkeypatch.setitem(sys.modules, sub, MagicMock())

        mock_graph = MagicMock()
        mock_graph.invoke.side_effect = RuntimeError("LLM call failed")

        mock_vectorstore = MagicMock()

        with patch("graph.graph.build_graph", return_value=mock_graph), \
             patch("observability.setup_observability"), \
             patch("langchain_openai.OpenAIEmbeddings", return_value=MagicMock()), \
             patch("langchain_community.vectorstores.Chroma", return_value=mock_vectorstore):
            from streamlit.testing.v1 import AppTest
            at = AppTest.from_file("app.py", default_timeout=10)
            at.run()
            # Simulate user submitting a query
            at.chat_input[0].set_value("What is CRAG?").run()

        # st.error should be called with the exception message
        assert any("LLM call failed" in str(e.value) for e in at.error)
