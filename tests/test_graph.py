"""Unit tests for graph/nodes.py and graph/graph.py.

Run with: pytest tests/test_graph.py -v
No OPENAI_API_KEY required — LLMs and retriever are mocked.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from graph.state import CRAGState, GradeResult
from graph.nodes import (
    grade_documents,
    not_found,
    generate,
    route_after_grading,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(**overrides) -> CRAGState:
    """Return a minimal valid CRAGState with sensible defaults."""
    base: CRAGState = {
        "query": "What is CRAG?",
        "reformulated_query": None,
        "retrieved_docs": [],
        "grade_results": [],
        "final_answer": None,
        "iteration_count": 0,
    }
    base.update(overrides)
    return base


def _make_doc(content: str = "some content", source: str = "doc.pdf") -> Document:
    return Document(page_content=content, metadata={"source": source})


def _make_grade(score: float, reason: str = "test reason", doc_id: str = "doc.pdf_0") -> GradeResult:
    return GradeResult(doc_id=doc_id, score=score, relevant=score >= 0.7, reason=reason)


# ---------------------------------------------------------------------------
# route_after_grading — pure function, no mocks needed
# ---------------------------------------------------------------------------

class TestRouteAfterGrading:
    def test_returns_generate_when_any_doc_passes(self):
        state = _make_state(
            grade_results=[_make_grade(0.8), _make_grade(0.3)],
            iteration_count=0,
        )
        assert route_after_grading(state) == "generate"

    def test_returns_generate_when_all_docs_pass(self):
        state = _make_state(
            grade_results=[_make_grade(0.9), _make_grade(0.75)],
            iteration_count=0,
        )
        assert route_after_grading(state) == "generate"

    def test_returns_generate_at_exact_threshold(self):
        state = _make_state(
            grade_results=[_make_grade(0.7)],
            iteration_count=0,
        )
        assert route_after_grading(state) == "generate"

    def test_returns_reformulate_when_no_pass_iter_0(self):
        state = _make_state(
            grade_results=[_make_grade(0.3), _make_grade(0.5)],
            iteration_count=0,
        )
        assert route_after_grading(state) == "reformulate_query"

    def test_returns_reformulate_when_no_pass_iter_1(self):
        state = _make_state(
            grade_results=[_make_grade(0.3)],
            iteration_count=1,
        )
        assert route_after_grading(state) == "reformulate_query"

    def test_returns_not_found_when_no_pass_iter_2(self):
        state = _make_state(
            grade_results=[_make_grade(0.3)],
            iteration_count=2,
        )
        assert route_after_grading(state) == "not_found"

    def test_returns_not_found_when_no_pass_iter_above_2(self):
        state = _make_state(
            grade_results=[_make_grade(0.1)],
            iteration_count=5,
        )
        assert route_after_grading(state) == "not_found"

    def test_below_threshold_does_not_trigger_generate(self):
        state = _make_state(
            grade_results=[_make_grade(0.69)],
            iteration_count=0,
        )
        assert route_after_grading(state) != "generate"


# ---------------------------------------------------------------------------
# not_found node
# ---------------------------------------------------------------------------

class TestNotFoundNode:
    def test_exact_refusal_string_format(self):
        state = _make_state(
            grade_results=[_make_grade(0.45, reason="off-topic content")],
        )
        result = not_found(state)
        answer = result["final_answer"]
        assert "Best relevance score:" in answer
        assert "0.45" in answer
        assert "off-topic content" in answer

    def test_score_rounded_to_2_decimals(self):
        state = _make_state(
            grade_results=[_make_grade(0.333333, reason="irrelevant")],
        )
        result = not_found(state)
        answer = result["final_answer"]
        assert "0.33" in answer

    def test_picks_highest_score_from_multiple_results(self):
        state = _make_state(
            grade_results=[
                _make_grade(0.3, reason="low relevance"),
                _make_grade(0.55, reason="best match"),
                _make_grade(0.2, reason="completely off"),
            ],
        )
        result = not_found(state)
        answer = result["final_answer"]
        assert "0.55" in answer
        assert "best match" in answer

    def test_reason_appears_verbatim(self):
        reason_text = "The document discusses unrelated financial topics"
        state = _make_state(
            grade_results=[_make_grade(0.4, reason=reason_text)],
        )
        result = not_found(state)
        assert reason_text in result["final_answer"]

    def test_returns_only_final_answer_key(self):
        state = _make_state(grade_results=[_make_grade(0.3)])
        result = not_found(state)
        assert list(result.keys()) == ["final_answer"]

    def test_empty_grade_results_does_not_raise(self):
        state = _make_state(grade_results=[])
        result = not_found(state)
        assert "final_answer" in result
        assert result["final_answer"] is not None


# ---------------------------------------------------------------------------
# grade_documents node
# ---------------------------------------------------------------------------

class TestGradeDocumentsNode:
    def _mock_grader_output(self, score: float, reason: str = "test"):
        """Return a mock GradeOutput-like object."""
        mock = MagicMock()
        mock.score = score
        mock.reason = reason
        mock.relevant = score >= 0.7
        return mock

    def test_produces_one_grade_per_doc(self):
        docs = [_make_doc("content A"), _make_doc("content B"), _make_doc("content C")]
        state = _make_state(retrieved_docs=docs)

        mock_grader = MagicMock()
        mock_grader.invoke.side_effect = [
            self._mock_grader_output(0.8),
            self._mock_grader_output(0.4),
            self._mock_grader_output(0.9),
        ]
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = grade_documents(state)

        assert len(result["grade_results"]) == 3

    def test_relevant_true_when_score_above_threshold(self):
        docs = [_make_doc()]
        state = _make_state(retrieved_docs=docs)

        mock_grader = MagicMock()
        mock_grader.invoke.return_value = self._mock_grader_output(score=0.85)
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = grade_documents(state)

        assert result["grade_results"][0]["relevant"] is True
        assert result["grade_results"][0]["score"] == 0.85

    def test_relevant_false_when_score_below_threshold(self):
        docs = [_make_doc()]
        state = _make_state(retrieved_docs=docs)

        mock_grader = MagicMock()
        mock_grader.invoke.return_value = self._mock_grader_output(score=0.5)
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = grade_documents(state)

        assert result["grade_results"][0]["relevant"] is False

    def test_relevant_computed_from_score_not_trusted_from_llm(self):
        """LLM returns relevant=True but score=0.3 — Python should set relevant=False."""
        docs = [_make_doc()]
        state = _make_state(retrieved_docs=docs)

        inconsistent_output = MagicMock()
        inconsistent_output.score = 0.3
        inconsistent_output.reason = "somewhat related"
        inconsistent_output.relevant = True  # LLM says True but score is 0.3

        mock_grader = MagicMock()
        mock_grader.invoke.return_value = inconsistent_output
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = grade_documents(state)

        # Python recomputes: 0.3 < 0.7 → relevant must be False
        assert result["grade_results"][0]["relevant"] is False

    def test_returns_only_grade_results_key(self):
        docs = [_make_doc()]
        state = _make_state(retrieved_docs=docs)

        mock_grader = MagicMock()
        mock_grader.invoke.return_value = self._mock_grader_output(0.6)
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = grade_documents(state)

        assert list(result.keys()) == ["grade_results"]


# ---------------------------------------------------------------------------
# generate node — filtering behaviour
# ---------------------------------------------------------------------------

class TestGenerateNode:
    def test_only_passing_docs_in_context(self):
        """Only docs with score >= 0.7 must appear in the LLM call."""
        doc_a = _make_doc("relevant content", "a.pdf")
        doc_b = _make_doc("irrelevant content", "b.pdf")
        state = _make_state(
            retrieved_docs=[doc_a, doc_b],
            grade_results=[
                _make_grade(0.85, doc_id="a.pdf_0"),
                _make_grade(0.30, doc_id="b.pdf_1"),
            ],
        )

        mock_response = MagicMock()
        mock_response.content = "Generated answer."
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response

        captured_prompt = {}

        def capture_invoke(prompt):
            captured_prompt["value"] = prompt
            return mock_response

        mock_llm.invoke.side_effect = capture_invoke

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = generate(state)

        # doc_a content must appear in the prompt; doc_b must not
        assert "relevant content" in captured_prompt["value"]
        assert "irrelevant content" not in captured_prompt["value"]
        assert result["final_answer"] == "Generated answer."

    def test_returns_only_final_answer_key(self):
        doc = _make_doc("content")
        state = _make_state(
            retrieved_docs=[doc],
            grade_results=[_make_grade(0.9)],
        )
        mock_response = MagicMock()
        mock_response.content = "answer"
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm):
            result = generate(state)

        assert list(result.keys()) == ["final_answer"]


# ---------------------------------------------------------------------------
# build_graph integration smoke test
# ---------------------------------------------------------------------------

class TestBuildGraph:
    def test_build_graph_returns_compilable_graph(self):
        """build_graph() must not raise and must return an invocable object."""
        from graph.graph import build_graph

        # Mock all LLM and retriever calls to avoid API calls
        mock_docs = [_make_doc("test content")]
        mock_grade_output = MagicMock()
        mock_grade_output.score = 0.9
        mock_grade_output.reason = "highly relevant"

        mock_grader = MagicMock()
        mock_grader.invoke.return_value = mock_grade_output

        mock_gen_response = MagicMock()
        mock_gen_response.content = "Test answer"

        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader
        mock_llm.invoke.return_value = mock_gen_response

        mock_vectorstore = MagicMock()
        mock_vectorstore.similarity_search.return_value = mock_docs

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm), \
             patch("graph.nodes._get_retriever", return_value=mock_vectorstore):
            graph = build_graph()
            result = graph.invoke({
                "query": "What is CRAG?",
                "reformulated_query": None,
                "retrieved_docs": [],
                "grade_results": [],
                "final_answer": None,
                "iteration_count": 0,
            })

        assert result is not None
        assert result.get("final_answer") is not None

    def test_iteration_count_never_exceeds_2(self):
        """Even with persistent low grades, iteration_count must stop at 2."""
        from graph.graph import build_graph

        # All docs fail grading — forces reformulation loop
        mock_docs = [_make_doc("irrelevant")]
        mock_grade_output = MagicMock()
        mock_grade_output.score = 0.1
        mock_grade_output.reason = "not relevant at all"

        mock_grader = MagicMock()
        mock_grader.invoke.return_value = mock_grade_output

        mock_reformulate_response = MagicMock()
        mock_reformulate_response.content = "reformulated query"

        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader
        mock_llm.invoke.return_value = mock_reformulate_response

        mock_vectorstore = MagicMock()
        mock_vectorstore.similarity_search.return_value = mock_docs

        with patch("graph.nodes.ChatOpenAI", return_value=mock_llm), \
             patch("graph.nodes._get_retriever", return_value=mock_vectorstore):
            graph = build_graph()
            result = graph.invoke({
                "query": "unanswerable question",
                "reformulated_query": None,
                "retrieved_docs": [],
                "grade_results": [],
                "final_answer": None,
                "iteration_count": 0,
            })

        assert result["iteration_count"] <= 2
        assert "Best relevance score:" in result["final_answer"]
