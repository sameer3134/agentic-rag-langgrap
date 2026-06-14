---
description: Multi-agent review of current PR covering correctness, security, and layer compliance
model: opus
complexity: intermediate
priority: high
tags:
  - review
  - workflow
  - planning
depends_on:
  - general/pr-implement
chains_to: []
skip_if: []
version: 1.0.0
---

## Graphify Context
> Key architectural communities: LangGraph Agent Loop, Tool Infrastructure, Multi-Tenant Identity, RAG Tools & Vector DB.
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# PR Review

[Extended thinking: Read the plan before spawning review agents. The plan defines what was intended — use it as ground truth when judging whether the implementation is correct, not just whether the code is internally consistent.]

## Review Process

1. **Auto-detect the current PR:**
   - Run `git branch --show-current`, find it in `docs/planning/new_git.csv`
   - Derive the plan filename and read `thoughts/shared/plans/{filename}` completely
   - If no plan file exists, warn: "No plan found — review will check against CLAUDE.md conventions only, not against an approved plan."

2. **Collect the diff:**
   ```bash
   git diff origin/main...HEAD --stat
   git diff origin/main...HEAD
   ```

3. **Spawn three review agents in parallel:**

### 1. Correctness & Test Quality Review

Use the Agent tool with `subagent_type: "code-reviewer"`.

Examine:
- Whether each task's acceptance criteria from the plan are actually satisfied by the implementation
- Test quality: enum completeness via set comparison (not `assert MyEnum.X == "X"` tautologies), column defaults via `col.default.arg` (not unflushed SA object field access), FK ondelete asserted directly from `col.foreign_keys`, nullable asserted explicitly
- Known limitations: each one must have its stated invariant verifiable and its enforcement present
- Logic bugs, off-by-one errors, unhandled edge cases

Prompt: `Review the following diff for correctness and test quality against the plan. Flag any acceptance criterion not satisfied, any test that is a tautology, and any plan limitation missing its stated invariant or enforcement mechanism. Diff: $ARGUMENTS`

### 2. Security Review

Use the Agent tool with `subagent_type: "security-auditor"`.

Examine:
- Auth enforcement: are all new endpoints protected? Is the auth/permission check applied consistently?
- Injection risks: raw SQL, unparameterised queries, user-controlled format strings
- PII handling: are columns marked PII in the plan handled with the stated retention policy in code?
- FK cascade rules: would a CASCADE unexpectedly delete or expose data after a parent deletion?
- SSRF and input validation on any new file download or URL fetch paths

Prompt: `Security review this diff. Focus on missing auth enforcement on new endpoints, injection vectors, PII handling for columns flagged as PII in the plan, unsafe FK cascade behaviour, and any new external HTTP calls without SSRF mitigation. Diff: $ARGUMENTS`

### 3. Architecture & Layer Compliance Review

Use the Agent tool with `subagent_type: "architect-reviewer"`.

Examine:
- Layer violations: business logic in models, FastAPI imports in services, DB queries in controllers
- Migration order: ENUMs created before tables that use them, self-referential FKs added after `create_table` via separate `op.create_foreign_key`, `downgrade()` as exact reverse
- CLAUDE.md rules: enum member names UPPERCASE, `from __future__ import annotations` at top of every file, import order (stdlib → third-party → `app.*`), `get_settings()` not called at module level
- Scope creep: does the implementation match what the plan described, or were features added silently?

Prompt: `Review this diff for architectural layer compliance and CLAUDE.md rule violations. Check migration ordering, enum naming, import structure, and whether the implementation matches the plan's stated scope without silent additions. Diff: $ARGUMENTS`

## Consolidated Review Output

Write findings to `thoughts/shared/reviews/{branch-slug}-review.md`.

### 1. Critical — must fix before merging
Issues that risk data loss, security vulnerabilities, broken migrations, or incorrect acceptance criteria.

### 2. Important — should fix
Layer violations, missing test cases, plan deviations, unclear limitations.

### 3. Minor — consider fixing
Style, naming conventions, redundant code, comment quality.

### 4. Positive findings
Patterns done well — worth repeating in future PRs.

### Verdict

```
Verdict: PASS / NEEDS_WORK / FAIL

PASS       — No critical or important issues. Safe to open a PR.
NEEDS_WORK — Important issues found. Fix before opening a PR.
FAIL       — Critical issues found. Do not open a PR until resolved.
```

After writing the review file, print the verdict and the path:

```
Review written: thoughts/shared/reviews/{branch-slug}-review.md
Verdict: [PASS / NEEDS_WORK / FAIL]

If PASS:        run /commit then /describe_pr to open the PR
If NEEDS_WORK:  fix the important findings, then re-run /pr-review
If FAIL:        fix the critical findings, then re-run /pr-review
```

Target for review: $ARGUMENTS
