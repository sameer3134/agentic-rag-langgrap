# PR Review: chore/project-scaffold (PR1)

**Branch:** `chore/project-scaffold`
**Plan:** `thoughts/shared/plans/PR1-project-scaffold.md`
**Reviewed:** 2026-06-14

---

## 1. Critical — must fix before merging

None found.

---

## 2. Important — should fix

### 2.1 Scope creep: `.claude/` tooling committed on this branch

The latest commit (`82800cf chore: add make-worktrees.sh script and worktree config`) adds 81 files to `.claude/` (commands, templates, settings, scripts). This directory is entirely absent from the PR1 plan's Task Table (T1–T6). The plan's stated scope is: directory structure, `.gitignore`, `.env.example`, `requirements.txt`, state schema, and module stubs.

The `.claude/` content was added as a separate commit on this branch rather than on its own scaffold/tooling branch. This makes the PR diff ~38,700 lines larger than the plan's expected scope and couples unrelated changes.

**Recommendation:** Extract the `.claude/` commit into its own branch/PR, or document the deviation explicitly in the plan. If the intent is to include it, update the plan's Task Table.

### 2.2 Plan-defined source files are untracked/unstaged

`git status` shows the following as `??` (untracked):

```
?? .env.example
?? app.py
?? eval.py
?? graph/
?? ingest.py
?? observability.py
?? requirements.txt
```

Only `.gitignore` modification and `data/uploads/.gitkeep` are staged (`A`/`M`). The core deliverables of T3–T6 are not yet committed. The import smoke-test passes because the files exist on disk, but a reviewer checking out the branch tip would not get these files.

**Recommendation:** Stage and commit all T3–T6 files in a commit on this branch before the PR is opened.

### 2.3 Extra `.gitignore` entries not in the plan

The `.gitignore` contains three entries absent from the plan:

```
node_modules/
package.json
package-lock.json
```

This is a Python-only project (no Node.js dependency anywhere in the stack). These entries suggest copy-paste from a JavaScript template. They are harmless but indicate undocumented scope addition.

**Recommendation:** Remove or document these entries. If they are intentional (e.g., the Streamlit UI will later use Node tooling), add an assumption to the plan.

---

## 3. Minor — consider fixing

### 3.1 `.claude/settings.local.json` allows `Bash(*)`

`settings.local.json` grants `Bash(*)` (unrestricted shell execution). This is a development convenience file but if committed to the repo it grants any future agent running on this project unconditional bash access. The file is not gitignored.

**Recommendation:** Either gitignore `settings.local.json` (it is "local" by convention) or tighten the permission to specific commands.

### 3.2 Plan documents `data/uploads/` gitignore rule but implementation uses `data/uploads/*`

The plan's T2 Implementation section shows `data/uploads/` in the gitignore block. The actual implementation uses `data/uploads/*` + `!data/uploads/.gitkeep` (documented in the plan's Implementation Notes section). This is the correct approach and passes the acceptance criteria, but the plan body has an inconsistency between the "Implementation" block and the "Implementation Notes" section.

Minor documentation inconsistency only — no code fix needed.

---

## 4. Positive findings

### 4.1 State schema is correct and fully verifiable

`graph/state.py` satisfies every acceptance criterion:
- `from graph.state import GradeResult, CRAGState` succeeds.
- `GradeResult` has exactly `{doc_id, score, relevant, reason}`.
- `CRAGState` has exactly `{query, reformulated_query, retrieved_docs, grade_results, final_answer, iteration_count}`.
- `reformulated_query` and `final_answer` are `str | None` (verified via `typing.get_type_hints()`).
- `from __future__ import annotations` is present; only `typing` is imported; no external deps.

### 4.2 Import smoke-test passes

```
python -c "import app, ingest, observability, eval; from graph import state, nodes, graph"
```
Exits with code 0. All six stub modules are importable with no dependencies installed beyond the stdlib.

### 4.3 `.env` is properly gitignored

Creating `.env` and running `git status` confirms the file does not appear. The `.gitignore` rule is correct.

### 4.4 `data/uploads/.gitkeep` is tracked correctly

`git ls-files data/` returns `data/uploads/.gitkeep`. The `data/uploads/*` + `!data/uploads/.gitkeep` pattern is the correct git idiom for this requirement.

### 4.5 `requirements.txt` matches plan exactly

All 11 packages present with the specified version pins (10 pinned + `python-dotenv` unpinned). Matches the plan's T4 Implementation block line for line.

### 4.6 `.env.example` is complete and safe

All four required keys are present (`OPENAI_API_KEY`, `CHROMA_PERSIST_DIR`, `PHOENIX_PORT`, `PHOENIX_TRACE_DIR`). Placeholder values only — no real credentials.

### 4.7 TypedDict annotation strategy is well-documented

The plan's Assumptions 7–8 and Implementation Notes §T5 document why `bare list` is used instead of `list[Document]` and why `get_type_hints()` is needed instead of `__annotations__` direct access. This level of documentation prevents future confusion.

---

## Verdict

```
Verdict: NEEDS_WORK

Important issues found:
  2.1 — .claude/ tooling (81 files, ~38 K lines) committed on this branch without plan coverage
  2.2 — Core T3–T6 deliverables (app.py, requirements.txt, graph/, etc.) are untracked/unstaged
  2.3 — Extra JS-ecosystem .gitignore entries not in plan

Fix before opening a PR:
  1. Commit all plan-defined source files (T3–T6) in a dedicated commit on this branch.
  2. Either extract the .claude/ commit to its own branch/PR or update the plan to cover it.
  3. Remove node_modules/, package.json, package-lock.json from .gitignore or add them as an assumption.
```

Review written: `thoughts/shared/reviews/project-scaffold-review.md`
