# feat: CRAG LangGraph nodes, routing, and assembly

> Issue #3 | Branch `feat/crag-graph` | Type AFK
> Depends on: #1, #2
> Source PRD: PRD-agentic-crag-pipeline.md

## What to build

Implement the full CRAG state machine in three files: `graph/state.py` (already seeded in #1 — extend if needed), `graph/nodes.py` (all five node functions), and `graph/graph.py` (graph assembly, routing function, and compilation). The compiled graph accepts a query string, routes it through retrieval → grading → conditional reformulation or generation, and returns a final answer or a structured "not found" response. Include unit tests for the routing function and the `not_found` node output format.

## Resolved decisions

**State shape** (defined in `graph/state.py` from #1):
```python
CRAGState:
  query: str
  reformulated_query: str | None
  retrieved_docs: list[Document]
  grade_results: list[GradeResult]
  final_answer: str | None
  iteration_count: int

GradeResult:
  doc_id: str
  score: float          # 0.0–1.0
  relevant: bool        # score >= 0.7
  reason: str
```

**Node: `retrieve`**
- Active query = `state["reformulated_query"]` if set, else `state["query"]`
- Run Chroma similarity search, top-5
- Return `{"retrieved_docs": <list of Documents>}`

**Node: `grade_documents`**
- For each doc in `retrieved_docs`, call `gpt-4o-mini` via `.with_structured_output()` with Pydantic model `GradeOutput(relevant: bool, score: float, reason: str)`
- Set `relevant = score >= 0.7`
- Return `{"grade_results": <list of GradeResult>}`

**Node: `reformulate_query`**
- Build prompt with original `query` and the `reason` from the highest-scoring failed `GradeResult`
- Call `gpt-4o-mini` for a single reformulated query string
- Increment `iteration_count` by 1
- Return `{"reformulated_query": <new query>, "iteration_count": state["iteration_count"] + 1}`

**Node: `generate`**
- Filter `retrieved_docs` to those whose matching `GradeResult.score >= 0.7`
- Pass filtered docs as context to `gpt-4o`
- Return `{"final_answer": <generated answer>}`

**Node: `not_found`**
- Find the `GradeResult` with the highest `score` across all `grade_results`
- Return:
  ```python
  {"final_answer": f"I couldn't find relevant information in the knowledge base. (Best relevance score: {best.score:.2f} — reason: '{best.reason}')"}
  ```

**Routing function** (pure — no LLM calls):
```python
def route_after_grading(state: CRAGState) -> str:
    passing = [r for r in state["grade_results"] if r["score"] >= 0.7]
    if passing:
        return "generate"
    if state["iteration_count"] < 2:
        return "reformulate_query"
    return "not_found"
```

**Graph wiring:**
- Entry point: `retrieve`
- Edges: `retrieve → grade_documents`
- Conditional edge: `grade_documents` → `route_after_grading` → `generate` | `reformulate_query` | `not_found`
- `reformulate_query → retrieve` (loop back)
- `generate → END`
- `not_found → END`

**LLM clients:**
- Grader/reformulator: `ChatOpenAI(model="gpt-4o-mini")`
- Generator: `ChatOpenAI(model="gpt-4o")`
- Both read `OPENAI_API_KEY` from env

**Graph invocation contract:**
```python
graph = build_graph()
result = graph.invoke({"query": "...", "reformulated_query": None, "retrieved_docs": [], "grade_results": [], "final_answer": None, "iteration_count": 0})
answer = result["final_answer"]
```

## Acceptance criteria

- [ ] `route_after_grading` returns `"generate"` when at least one `GradeResult` has `score >= 0.7`
- [ ] `route_after_grading` returns `"reformulate_query"` when all scores < 0.7 and `iteration_count` is 0 or 1
- [ ] `route_after_grading` returns `"not_found"` when all scores < 0.7 and `iteration_count` is 2
- [ ] `not_found` node builds the exact refusal string format: includes `"Best relevance score:"`, the score rounded to 2 decimal places, and the reason verbatim
- [ ] `generate` node only passes docs with `score >= 0.7` to the LLM (verified by mocking the LLM and inspecting the call args)
- [ ] `grade_documents` node produces one `GradeResult` per retrieved doc, with `relevant=True` iff `score >= 0.7`
- [ ] `build_graph()` returns a compiled LangGraph that can be invoked with the initial state dict without raising
- [ ] A full graph invocation with mocked LLMs and a mocked Chroma retriever completes without error and returns a non-None `final_answer`
- [ ] Reformulation loop does not execute more than 2 times (iteration_count never exceeds 2)

## Out of scope

- Arize Phoenix instrumentation — that is issue #4
- Streamlit UI — that is issue #5
- Web search fallback — explicitly out of scope for the entire project
