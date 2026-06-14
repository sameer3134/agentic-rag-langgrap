## Summary

This PR replaces the stub `eval.py` with a complete, standalone command-line evaluation script that measures CRAG pipeline quality against a synthetic golden dataset. On first run it generates approximately 50 Q&A pairs from the ingested Chroma corpus using Ragas `TestsetGenerator` and saves them to `data/golden_dataset.json`; subsequent runs load the saved file to preserve metric trend interpretability. It then invokes the compiled CRAG graph for each question, collects the retrieved context and generated answer, runs Ragas `evaluate()` across four metrics, and prints a pass/fail table to stdout.

## Changes

- `eval.py` — stub (~7 lines) replaced with full implementation (~271 lines): threshold constants, `load_or_generate_golden_dataset()`, `run_pipeline_on_dataset()`, `run_evaluation()`, `print_results_table()`, and `main()` entry point
- `tests/test_eval.py` — new file with 11 unit tests covering threshold constants guard and pass/fail table logic (no `OPENAI_API_KEY` required)
- `thoughts/shared/plans/PR6-ragas-eval.md` — planning artifact documenting architecture decisions, task breakdown, and acceptance criteria
- `thoughts/shared/reviews/ragas-eval-review.md` — review artifact with PASS verdict

## Tasks covered

| Task | What it builds |
|------|----------------|
| T1 | Named threshold constants at module level (`THRESHOLD_FAITHFULNESS=0.85`, `THRESHOLD_CONTEXT_RECALL=0.80`, `THRESHOLD_ANSWER_RELEVANCY=0.80`, `THRESHOLD_CONTEXT_PRECISION=0.75`) and `print_results_table()` pure function |
| T2 | `load_or_generate_golden_dataset()` — Ragas `TestsetGenerator` integration with JSON persistence; loads on subsequent runs without regenerating |
| T3 | `run_pipeline_on_dataset()` — iterates dataset, invokes compiled CRAG graph, extracts passing context docs filtered by `GRADE_THRESHOLD`, collects rows |
| T4 | `run_evaluation()` — wraps Ragas `evaluate()` call with four metrics (Faithfulness, Context Recall, Answer Relevancy, Context Precision) |
| T5 | `main()` entry point with `load_dotenv()`, orchestration, and exit-0 contract even on metric failures or empty Chroma |
| T6 | Unit tests: `TestThresholdConstants` (5 tests) and `TestPrintResultsTable` (6 tests) — all pass without API key |

## Test plan

- [ ] `pytest tests/test_eval.py -v` exits with code 0 (11 tests pass, no `OPENAI_API_KEY` required)
- [ ] `python -c "import eval; print(eval.THRESHOLD_FAITHFULNESS)"` prints `0.85`
- [ ] `python eval.py` runs end-to-end when a populated Chroma store and `OPENAI_API_KEY` exist
- [ ] On first run: `data/golden_dataset.json` is created; on subsequent runs: file is loaded without regeneration
- [ ] Script exits with code 0 even when all metrics FAIL (`echo $?` returns `0`)
- [ ] Script exits with code 0 when Chroma is empty (prints error message, does not crash)
- [ ] All automated checks pass: `pytest tests/ -v`

## Review notes

Review verdict: PASS

No outstanding findings.

---
Plan: `thoughts/shared/plans/PR6-ragas-eval.md`
Review: `thoughts/shared/reviews/ragas-eval-review.md`
