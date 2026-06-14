---
description: Implement the current PR's plan from thoughts/shared/plans/ task by task with verification
model: deepseek/deepseek-v4-pro
complexity: advanced
priority: critical
tags:
  - planning
  - workflow
depends_on:
  - general/pr-plan-create
chains_to:
  - general/pr-review
skip_if: []
version: 1.0.0
---

## Graphify Context
> Key architectural communities: LangGraph Agent Loop, Tool Infrastructure, Multi-Tenant Identity, RAG Tools & Vector DB.
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# PR Implement

You are tasked with implementing the current PR's approved plan file exactly as written. Do not add features, refactor beyond what the plan specifies, or introduce abstractions not present in the plan.

## Getting Started

1. Run `git branch --show-current` to identify the current branch
2. Derive the plan filename using the same rule as `/pr-plan-create`:
   - `feat/s01/user-auth` → `S01-user-auth.md`
   - `auth/s04/csrf-middleware` → `S04-csrf-middleware.md`
3. Check if `thoughts/shared/plans/{filename}` exists
   - If not found, scan `thoughts/shared/plans/` for any file referencing this branch
   - If still not found, respond with:
     ```
     No plan found for branch '<branch>'.
     Run /pr-plan-create first to research and write the implementation plan.
     ```
4. Read the plan completely — including all column decisions, FK decisions, constraints, known limitations, and acceptance criteria — before writing a single line of code
5. Read `CLAUDE.md` if not already in context — layer rules are binding

## Implementation Philosophy

Implement each task in the plan's stated order — ordering exists for a reason (migration dependencies, FK ordering, layer separation). If you believe the order is wrong, stop and flag it rather than reordering silently.

After each task, run only the task's **fast acceptance criteria** from the plan — targeted unit tests (`pytest tests/test_specific.py`), grep checks, and migration smoke runs (`make migrate`). Do not run the full test suite after each task. If a fast criterion fails, fix it before moving to the next task.

If the plan specifies code that contradicts CLAUDE.md conventions, follow CLAUDE.md — it is the authoritative layer contract. Log the conflict in a `## Implementation Notes` section at the bottom of the plan file and continue.

Do not spawn sub-agents.

After each task emit one line only:
```
✓ {Task_ID} — {Task_Name} ({N} files written, fast criteria passed)
```

## Verification Approach

After **all** tasks are implemented, run the full suite once:

```bash
make migrate && make lint && make test-cov
```

If any check fails: fix it before marking implementation complete. Do not proceed to `/pr-review` with failing checks — a failing check is not a blocker to report, it is a bug to fix.

## If You Get Stuck

- **Plan vs codebase mismatch:** Read the actual file, follow CLAUDE.md as the tiebreaker, and log the discrepancy in the plan's `## Implementation Notes` section. Continue without stopping.
- **Migration risk:** If a migration would conflict with a prior one, apply `checkfirst=True` and `RESTRICT` semantics, log the assumption, and continue.
- **Acceptance criterion unclear:** Interpret the criterion as literally as possible, run the closest verifiable command, and log the interpretation in `## Implementation Notes`. Do not skip.

## Important notes:
- Do not commit during implementation — commits happen after `/pr-review` via `/commit`
- The plan's known limitations section is not optional — each limitation's invariant must be verifiable before the task is marked complete
- If a task's implementation would violate a known limitation's stated invariant, apply the most conservative interpretation that satisfies the invariant, log it in `## Implementation Notes`, and continue
