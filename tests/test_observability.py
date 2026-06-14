"""Unit tests for observability.py.

Run with: pytest tests/test_observability.py -v
No OPENAI_API_KEY or live Phoenix server required — all external calls mocked.
"""
from __future__ import annotations

import importlib
import os
import sys
from unittest.mock import MagicMock, patch, call

import pytest


def _fresh_observability():
    """Return a freshly reloaded observability module with _initialized reset.

    Injects mock stubs for 'phoenix' and 'openinference.instrumentation.langchain'
    into sys.modules before reloading so the module-level imports succeed without
    requiring the actual packages or their transitive dependencies (e.g. pandas).
    """
    # Build fresh mocks so each test gets an independent set of objects
    mock_px_module = MagicMock()
    mock_instr_module = MagicMock()
    mock_instr_cls = MagicMock()
    mock_instr_module.LangChainInstrumentor = mock_instr_cls

    # Inject before reload so the top-level imports in observability.py resolve
    sys.modules["phoenix"] = mock_px_module
    sys.modules.setdefault("openinference", MagicMock())
    sys.modules.setdefault("openinference.instrumentation", MagicMock())
    sys.modules["openinference.instrumentation.langchain"] = mock_instr_module

    import observability
    importlib.reload(observability)
    return observability


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_px():
    mock_px = MagicMock()
    mock_session = MagicMock()
    mock_px.active_session.return_value = mock_session
    return mock_px


def _make_mock_instrumentor_cls():
    mock_cls = MagicMock()
    mock_instance = MagicMock()
    mock_cls.return_value = mock_instance
    return mock_cls


# ---------------------------------------------------------------------------
# First-call behaviour
# ---------------------------------------------------------------------------

class TestSetupObservabilityFirstCall:
    def test_setup_called_once_launches_phoenix(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))
        monkeypatch.setenv("PHOENIX_PORT", "6006")

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()

        mock_px.launch_app.assert_called_once()

    def test_notebook_environment_streamlit(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()

        _, kwargs = mock_px.launch_app.call_args
        assert kwargs.get("notebook_environment") == "streamlit"

    def test_phoenix_port_default(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))
        monkeypatch.delenv("PHOENIX_PORT", raising=False)

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()

        _, kwargs = mock_px.launch_app.call_args
        assert kwargs.get("port") == 6006

    def test_phoenix_port_override(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))
        monkeypatch.setenv("PHOENIX_PORT", "7777")

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()

        _, kwargs = mock_px.launch_app.call_args
        assert kwargs.get("port") == 7777

    def test_instruments_langchain_once(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()

        mock_instr_cls.return_value.instrument.assert_called_once()


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

class TestSetupObservabilityIdempotency:
    def test_double_call_does_not_relaunch_phoenix(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()
            obs.setup_observability()

        assert mock_px.launch_app.call_count == 1

    def test_double_call_does_not_instrument_twice(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()
            obs.setup_observability()

        assert mock_instr_cls.return_value.instrument.call_count == 1

    def test_triple_call_launch_count_still_one(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PHOENIX_TRACE_DIR", str(tmp_path / "traces"))

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()
            obs.setup_observability()
            obs.setup_observability()

        assert mock_px.launch_app.call_count == 1


# ---------------------------------------------------------------------------
# Directory creation and env var propagation
# ---------------------------------------------------------------------------

class TestSetupObservabilityDirAndEnv:
    def test_trace_dir_created_if_absent(self, tmp_path, monkeypatch):
        trace_dir = str(tmp_path / "new_traces_dir")
        assert not os.path.isdir(trace_dir)
        monkeypatch.setenv("PHOENIX_TRACE_DIR", trace_dir)

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()

        assert os.path.isdir(trace_dir)

    def test_phoenix_working_dir_env_set(self, tmp_path, monkeypatch):
        trace_dir = str(tmp_path / "traces")
        monkeypatch.setenv("PHOENIX_TRACE_DIR", trace_dir)

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            obs.setup_observability()

        assert os.environ.get("PHOENIX_WORKING_DIR") == trace_dir

    def test_trace_dir_already_exists_does_not_raise(self, tmp_path, monkeypatch):
        trace_dir = str(tmp_path / "existing_traces")
        os.makedirs(trace_dir)
        monkeypatch.setenv("PHOENIX_TRACE_DIR", trace_dir)

        mock_px = _make_mock_px()
        mock_instr_cls = _make_mock_instrumentor_cls()

        obs = _fresh_observability()
        with patch.object(obs, "px", mock_px), \
             patch.object(obs, "LangChainInstrumentor", mock_instr_cls):
            # Should not raise even though directory already exists
            obs.setup_observability()
