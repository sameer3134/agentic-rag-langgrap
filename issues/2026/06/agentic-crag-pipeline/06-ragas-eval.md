# feat: Ragas evaluation script and golden dataset

> Issue #6 | Branch `feat/ragas-eval` | Type AFK
> Depends on: #2, #3
> Source PRD: PRD-agentic-crag-pipeline.md

## What to build

Implement `eval.py` — a standalone command-line script that measures the quality of the CRAG pipeline against a synthetic golden dataset. On first run it generates ~50 Q&A pairs from the ingested corpus using Ragas `TestsetGenerator` and saves them to `data/golden_dataset.json`. On subsequent runs it loads the saved dataset. It then invokes the CRAG graph for each question, collects retrieved context and generated answers, runs Ragas evaluation across four metrics, and prints a pass/fail table. Include unit tests for the pass/fail table logic and threshold constant values.

## Resolved decisions

**Golden dataset generation:**
- Use `ragas.testset.TestsetGenerator` with the ingested `Document` objects loaded from Chroma
- Generate exactly 50 Q&A pairs
- Save to `data/golden_dataset.json` after first generation
- On subsequent runs: load from `data/golden_dataset.json` — do NOT regenerate (regenerating changes the evaluation target, making metric trends uninterpretable)
- `TestsetGenerator` uses `OPENAI_API_KEY` (same key as the rest of the pipeline)

**Pipeline invocation per question:**
- For each question in the dataset, invoke the compiled CRAG graph with the initial state
- Capture from final state: `retrieved_docs` (filtered passing docs), `final_answer`
- Build a Ragas `EvaluationDataset` row: `{ "question": q, "answer": final_answer, "contexts": [doc.page_content for doc in passing_docs], "ground_truth": dataset_answer }`

**Metrics and thresholds:**
```
Faithfulness          threshold >= 0.85
Context Recall        threshold >= 0.80
Answer Relevancy      threshold >= 0.80
Context Precision     threshold >= 0.75
```

**Pass/fail table output format (printed to stdout):**
```
┌──────────────────────┬────────┬───────────┬────────┐
│ Metric               │ Score  │ Threshold │ Result │
├──────────────────────┼────────┼───────────┼────────┤
│ Faithfulness         │ 0.88   │ 0.85      │ PASS   │
│ Context Recall       │ 0.76   │ 0.80      │ FAIL   │
│ Answer Relevancy     │ 0.82   │ 0.80      │ PASS   │
│ Context Precision    │ 0.79   │ 0.75      │ PASS   │
└──────────────────────┴────────┴───────────┴────────┘
Overall: 3/4 metrics passing
```
Use `rich` or plain string formatting — either is acceptable.

**Script entry point:** `python eval.py` — no subcommands needed. `load_dotenv()` at top of script.

**Threshold constants:** Define thresholds as named constants at the top of `eval.py` (not magic numbers inline) so they are easy to locate and adjust.

**Questions that return "not found":** If the pipeline returns a "not found" `final_answer` for a question, record it with empty `contexts` and the refusal string as `answer`. Ragas will score it low — this is correct behavior, not a bug.

## Acceptance criteria

- [ ] `python eval.py` runs end-to-end without error when a populated Chroma store exists
- [ ] `data/golden_dataset.json` is created on first run and loaded (not regenerated) on subsequent runs
- [ ] The pass/fail table is printed with all four metrics, their scores, thresholds, and PASS/FAIL status
- [ ] A metric scoring above its threshold is marked PASS; below is marked FAIL
- [ ] Threshold constants match the spec values: Faithfulness=0.85, Context Recall=0.80, Answer Relevancy=0.80, Context Precision=0.75 (verified by unit test reading the constants directly)
- [ ] Unit test: given a mock `EvalResults` dict with one score above and one below threshold, the pass/fail table output correctly marks each
- [ ] Unit test: threshold constants equal their specified values (guards against accidental edits)
- [ ] Script exits with code 0 even when metrics fail (it reports, does not gate)

## Out of scope

- CI/CD integration or automated eval gating — manual on-demand script only
- Streamlit UI for running eval — CLI only
- Regenerating the golden dataset on every run — dataset is generated once and reused
- Metrics beyond the four specified (e.g. Answer Correctness, Noise Sensitivity)
