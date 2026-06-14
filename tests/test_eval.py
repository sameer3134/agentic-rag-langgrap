"""Unit tests for eval.py.

Run with: pytest tests/test_eval.py -v
No OPENAI_API_KEY required.
"""
from __future__ import annotations

import sys

import pytest


# ---------------------------------------------------------------------------
# Threshold constant guard tests
# ---------------------------------------------------------------------------

class TestThresholdConstants:
    """Guards the four threshold constants against accidental edits."""

    def _get_eval_module(self):
        # Fresh import each time to avoid stale module state
        if "eval" in sys.modules:
            return sys.modules["eval"]
        import eval as ev
        return ev

    def test_faithfulness_threshold(self):
        ev = self._get_eval_module()
        assert ev.THRESHOLD_FAITHFULNESS == 0.85, (
            f"THRESHOLD_FAITHFULNESS must be 0.85, got {ev.THRESHOLD_FAITHFULNESS}"
        )

    def test_context_recall_threshold(self):
        ev = self._get_eval_module()
        assert ev.THRESHOLD_CONTEXT_RECALL == 0.80, (
            f"THRESHOLD_CONTEXT_RECALL must be 0.80, got {ev.THRESHOLD_CONTEXT_RECALL}"
        )

    def test_answer_relevancy_threshold(self):
        ev = self._get_eval_module()
        assert ev.THRESHOLD_ANSWER_RELEVANCY == 0.80, (
            f"THRESHOLD_ANSWER_RELEVANCY must be 0.80, got {ev.THRESHOLD_ANSWER_RELEVANCY}"
        )

    def test_context_precision_threshold(self):
        ev = self._get_eval_module()
        assert ev.THRESHOLD_CONTEXT_PRECISION == 0.75, (
            f"THRESHOLD_CONTEXT_PRECISION must be 0.75, got {ev.THRESHOLD_CONTEXT_PRECISION}"
        )

    def test_thresholds_dict_matches_constants(self):
        """THRESHOLDS dict values must equal the named constants."""
        ev = self._get_eval_module()
        assert ev.THRESHOLDS["Faithfulness"] == ev.THRESHOLD_FAITHFULNESS
        assert ev.THRESHOLDS["Context Recall"] == ev.THRESHOLD_CONTEXT_RECALL
        assert ev.THRESHOLDS["Answer Relevancy"] == ev.THRESHOLD_ANSWER_RELEVANCY
        assert ev.THRESHOLDS["Context Precision"] == ev.THRESHOLD_CONTEXT_PRECISION


# ---------------------------------------------------------------------------
# Pass/fail table tests
# ---------------------------------------------------------------------------

class TestPrintResultsTable:
    """Verifies pass/fail classification and output format."""

    def _get_print_fn(self):
        if "eval" in sys.modules:
            return sys.modules["eval"].print_results_table
        import eval as ev
        return ev.print_results_table

    def test_above_threshold_is_pass(self, capsys):
        fn = self._get_print_fn()
        scores = {
            "Faithfulness": 0.90,      # > 0.85 -> PASS
            "Context Recall": 0.85,    # > 0.80 -> PASS
            "Answer Relevancy": 0.85,  # > 0.80 -> PASS
            "Context Precision": 0.80, # > 0.75 -> PASS
        }
        fn(scores)
        captured = capsys.readouterr().out
        assert "PASS" in captured
        assert "FAIL" not in captured

    def test_below_threshold_is_fail(self, capsys):
        fn = self._get_print_fn()
        scores = {
            "Faithfulness": 0.80,      # < 0.85 -> FAIL
            "Context Recall": 0.75,    # < 0.80 -> FAIL
            "Answer Relevancy": 0.75,  # < 0.80 -> FAIL
            "Context Precision": 0.70, # < 0.75 -> FAIL
        }
        fn(scores)
        captured = capsys.readouterr().out
        assert "FAIL" in captured
        assert "PASS" not in captured

    def test_mixed_pass_and_fail(self, capsys):
        fn = self._get_print_fn()
        scores = {
            "Faithfulness": 0.88,      # > 0.85 -> PASS
            "Context Recall": 0.76,    # < 0.80 -> FAIL
            "Answer Relevancy": 0.82,  # > 0.80 -> PASS
            "Context Precision": 0.79, # > 0.75 -> PASS
        }
        fn(scores)
        captured = capsys.readouterr().out
        assert "PASS" in captured
        assert "FAIL" in captured
        assert "3/4 metrics passing" in captured

    def test_exact_threshold_is_pass(self, capsys):
        """Score equal to threshold must be PASS (>= not >)."""
        fn = self._get_print_fn()
        scores = {
            "Faithfulness": 0.85,
            "Context Recall": 0.80,
            "Answer Relevancy": 0.80,
            "Context Precision": 0.75,
        }
        fn(scores)
        captured = capsys.readouterr().out
        assert "FAIL" not in captured
        assert "4/4 metrics passing" in captured

    def test_all_four_metrics_appear(self, capsys):
        fn = self._get_print_fn()
        scores = {k: 0.90 for k in ["Faithfulness", "Context Recall", "Answer Relevancy", "Context Precision"]}
        fn(scores)
        captured = capsys.readouterr().out
        assert "Faithfulness" in captured
        assert "Context Recall" in captured
        assert "Answer Relevancy" in captured
        assert "Context Precision" in captured

    def test_overall_line_present(self, capsys):
        fn = self._get_print_fn()
        scores = {k: 0.90 for k in ["Faithfulness", "Context Recall", "Answer Relevancy", "Context Precision"]}
        fn(scores)
        captured = capsys.readouterr().out
        assert "Overall:" in captured
