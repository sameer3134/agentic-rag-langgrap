---
description: Auto-detect current branch, scan for planning files, research codebase, and write an implementation plan without human intervention
model: opus
complexity: advanced
priority: critical
tags:
  - planning
  - workflow
depends_on: []
chains_to:
  - general/pr-implement
skip_if: []
version: 2.0.0
---

## Graphify Context
> Key architectural communities: LangGraph Agent Loop, Tool Infrastructure, Multi-Tenant Identity, RAG Tools & Vector DB.
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# PR Plan Create

You are tasked with producing a complete, self-contained implementation plan for the PR on the current branch. **No human input is required or requested at any point.** When a decision cannot be fully resolved from the codebase or spec, apply the conservative default (see rules below), document it in the plan's `## Assumptions` section, and continue.

## Step 1: Auto-detect the PR

- Run `git branch --show-current`
- **Discover the PR map CSV:**
  ```bash
  grep -rl "Branch_Name" --include="*.csv" \
    --exclude-dir=node_modules --exclude-dir=.git \
    --exclude-dir=venv --exclude-dir=.venv \
    . 2>/dev/null | head -1
  ```
  If not found: write `PLAN_BLOCKED: no PR map CSV found` and exit.
- Read the discovered CSV; find the row where `Branch_Name` matches the current branch exactly
- If no match: write `PLAN_BLOCKED: branch not in PR map CSV` and exit
- Extract: `PR_ID`, `Story`, `Tasks_Covered`, `Branch_Name`, `PR_Title`, `Depends_On`

Derive the plan filename: strip leading repo prefix (`feat/`, `auth/`, `labdx/`, `odc/`, `s11/`), uppercase the story segment, replace `/` with `-`.
Examples: `feat/s01/user-auth` → `S01-user-auth.md`, `auth/s04/csrf-middleware` → `S04-csrf-middleware.md`

## Step 2: Discover all planning files

Run these scans to locate files by content — not by path:

```bash
# Tasks CSV (has Task_ID column)
grep -rl "Task_ID" --include="*.csv" \
  --exclude-dir=node_modules --exclude-dir=.git \
  --exclude-dir=venv --exclude-dir=.venv \
  . 2>/dev/null | head -1

# PRD / spec (has story or requirements sections)
grep -rl "## Stories\|## Requirements\|## Goals\|## Overview" --include="*.md" \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.claude \
  . 2>/dev/null | head -1

# Architecture reference
grep -rl "3-layer\|ABC interface\|layer model\|service layer" --include="*.md" \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.claude \
  . 2>/dev/null | head -1

# Issues / lessons learned log
grep -rl "Known Issues\|ISSUE-\|Prevention rule\|Root cause" --include="*.md" \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.claude \
  . 2>/dev/null | head -1

# Progress / status file
grep -rl "## Done\|## In progress\|Status as of\|## Milestone" --include="*.md" \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.claude \
  . 2>/dev/null | head -1

# Domain glossary
grep -rl "## Auth\|## Authorisation\|Domain Glossary\|canonical definition" --include="*.md" \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.claude \
  . 2>/dev/null | head -1
```

Store results as: `TASKS_CSV`, `PRD_FILE`, `ARCH_FILE`, `ISSUES_FILE`, `PROGRESS_FILE`, `GLOSSARY_FILE`.
Missing files are skipped silently — not every repo has all of them.

## Step 3: Read all context

Read ALL discovered files completely before doing anything else:
- PR map CSV (found in Step 1)
- `TASKS_CSV` — rows matching `Tasks_Covered`
- `PRD_FILE` — authoritative spec
- `CLAUDE.md` — layer rules and conventions
- `ARCH_FILE` — canonical architecture patterns; mandatory before writing any backend code
- `PROGRESS_FILE` — what is already done
- `ISSUES_FILE` — known issues to avoid
- `GLOSSARY_FILE` — domain glossary

## Step 4: Spawn parallel research agents

Spawn in parallel:

- **codebase-locator**: Find all files relevant to `Tasks_Covered`. Focus on existing models, mixins, patterns in service/model/API layers. Return file list with purpose annotations.
- **codebase-analyzer**: For each file found: how are models structured, what migration patterns exist (ENUM ordering, FK ordering, index naming), what conventions are used? Return file:line references.
- **codebase-pattern-finder**: Find the most similar already-implemented features. Return concrete code excerpts to model after.
- **thoughts-locator**: Find existing research or decision documents relevant to this PR's domain.

Wait for all agents, then read every file they identified.

## Step 5: Resolve unknowns — no questions asked

For every decision the spec or codebase does not fully answer, apply the **conservative default** and record it in the plan's `## Assumptions` section:

| Situation | Conservative default |
|---|---|
| Nullable unclear | Nullable — won't break inserts; tighten later |
| FK ondelete unclear | `RESTRICT` — prevents accidental data loss |
| String length not specified | `VARCHAR(255)` |
| Index unclear | Add it — redundant index is cheaper than a missing one |
| Enum values not exhaustive | Add a `# TODO: verify completeness` comment |
| New domain term, no spec definition | Infer from usage; add to glossary with `[inferred]` tag |
| Domain term conflicts with glossary | Keep existing definition; note conflict in Assumptions |
| ADR criteria met (hard-to-reverse + surprising + real trade-off) | Write ADR at `docs/adr/` or nearest `adr/` directory; reference it in the plan |

## Step 6: Update the domain glossary

For every new domain term this PR introduces:
- Add it to `GLOSSARY_FILE` with a one-sentence definition derived from the spec and codebase
- Tag inferred definitions: `[inferred — verify]`
- For conflicts with existing entries: keep the existing definition, add a `<!-- conflict: <description> -->` comment

Do not pause. Write and continue.

## Step 7: Write the plan

Save to the nearest `thoughts/shared/plans/{filename}` directory, or create `thoughts/shared/plans/` at the repo root if none exists.

**Required sections:**

### `## What This PR Does`
2–4 sentences: what is built, why it exists, how it fits the system.

### `## Assumptions`
Every automated decision made in Step 5:
```
| # | Decision | Default applied | Reason | Revisit when |
|---|----------|----------------|--------|--------------|
```
If no assumptions: `No unresolved decisions — all choices are fully specified.`

### `## Task Table`
| Task ID | What it builds | Files |

### `## Architecture Constraints`
Hard rules from CLAUDE.md/ARCH_FILE that apply. Each with the consequence if violated.

### `## {Task_ID} — {Task_Name}` (one section per task)

Each includes: column decisions table, FK decisions table, constraints table, layer compliance checklist, known limitations, full implementation code, verifiable acceptance criteria.

### `## Migration`
Full migration with ENUM-before-table ordering, `checkfirst=True`, exact-reverse `downgrade()`.

### `## Test quality rules`
Enum completeness via set comparison, column defaults via `col.default.arg`, FK ondelete from `col.foreign_keys`, nullable asserted explicitly.

### `## Automated verification`
```bash
make migrate
make test-cov
make lint
```

### `## Manual verification`
Specific checks with exact steps and expected outputs.

## Step 8: Print summary and stop

```
Plan written: thoughts/shared/plans/{filename}

PR_ID:    {PR_ID}
Branch:   {Branch_Name}
Tasks:    {Tasks_Covered}

Planning files used:
  PR map:       <path>
  Tasks:        <path or "not found">
  PRD:          <path or "not found">
  Architecture: <path or "not found">
  Issues:       <path or "not found">
  Progress:     <path or "not found">
  Glossary:     <path or "not found">

Assumptions logged: N
Glossary updated:   N new terms
ADRs written:       <filenames or "none">

Ready for: /pr-implement
```

Then stop. Do not ask for feedback or offer to iterate.
