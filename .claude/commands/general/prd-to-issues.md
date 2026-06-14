---
name: prd-to-issues
description: Break a PRD into independently-shippable vertical slices, then write a CSV mapping (issue/pr/branch/title/depends_on) and a folder of self-sufficient local issue specs. Use when user wants to convert a plan into issues, create implementation tickets, or break down work into issues.
---

# PRD to Issues

Break a PRD into independently-shippable work items using vertical slices (tracer bullets). The output is a CSV mapping plus one self-sufficient local issue spec per slice — no GitHub.

## Process

### 1. Gather context

Read `PRD-{slug}.md` — it is the authoritative source. Derive `{slug}` from the PRD filename. If no PRD file exists, work from whatever is already in the conversation context.

### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of the code.

### 3. Draft vertical slices

Break the plan into **tracer bullet** issues. Each issue is a thin vertical slice that cuts through ALL integration layers end-to-end, NOT a horizontal slice of one layer.

Slices may be 'HITL' or 'AFK'. HITL slices require human interaction, such as an architectural decision or a design review. AFK slices can be implemented and merged without human interaction. Prefer AFK over HITL where possible.

<vertical-slice-rules>
- Each slice delivers a narrow but COMPLETE path through every layer (schema, API, UI, tests)
- A completed slice is demoable or verifiable on its own
- Prefer many thin slices over few thick ones
</vertical-slice-rules>

### 4. Quiz the user

Derive a short branch name for each slice now (so it can be shown in the quiz):

```
branch = {prefix}/{kebab-slug}
prefix ∈ feat | fix | docs | chore | refactor   (by the nature of the slice)
kebab-slug = a 2–4 word relevant name, lowercase-hyphen   e.g. feat/contract-models
```

Present the proposed breakdown as a numbered list. For each slice, show:

- **Title**: short descriptive name (becomes the PR title)
- **Branch**: the derived branch name
- **Type**: HITL / AFK
- **Blocked by**: which other slices (if any) must complete first
- **User stories covered**: which user stories this addresses (if the source material has them)

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the dependency relationships correct?
- Should any slices be merged or split further?
- Are the correct slices marked as HITL and AFK?

Iterate until the user approves the breakdown.

### 5. Write the outputs

Assign each approved slice a sequential `issue_number` starting at 1, in dependency order
(blockers first), so earlier numbers can be referenced as dependencies. In this flow
`issue_number` and `pr_number` are the same value (one slice → one PR). Then write two outputs.

#### 5a. The CSV mapping — `{slug}.csv`

Write `{slug}.csv` at the working root with exactly this header and one row per slice:

```csv
issue_number,pr_number,branch,pr_title,depends_on,type,status
1,1,docs/adr-decisions,"docs: locked decisions",,HITL,
2,2,feat/service-skeleton,"feat: bootable skeleton",1,AFK,
4,4,feat/schema-daos,"feat: schema + DAOs","1,2",AFK,
```

Column rules:
- `issue_number`, `pr_number` — the same sequential number for the slice.
- `branch` — the branch name derived in step 4.
- `pr_title` — the slice title. Quote it (CSV) since it usually contains a space/colon.
- `depends_on` — comma-separated `issue_number`s of the slices that must merge first; empty if
  none. Quote the cell when it contains more than one number (e.g. `"1,2"`).
- `type` — `HITL` or `AFK`.
- `status` — leave blank (means "todo"); it is set to `done`/`merged` later, downstream.

#### 5b. The local issue specs — `issues/{YYYY}/{MM}/{slug}/{NN}-{branch-slug}.md`

For each slice, write one self-sufficient spec file inside a year/month/slug folder:
- `YYYY` = current year (e.g. `2026`).
- `MM` = current month zero-padded (e.g. `06`).
- `slug` = the PRD slug derived in step 1 (e.g. `account-service`).
- `NN` = `issue_number` zero-padded to 2 digits (`01`, `02`, …).
- `branch-slug` = the last path segment of `branch` (`feat/schema-daos` → `schema-daos`).

Create the full directory tree (`issues/{YYYY}/{MM}/{slug}/`) before writing the files.

These specs must be **self-sufficient**: pull every decision the implementer needs from
`PRD-{slug}.md` so that no further questions are required downstream. Use this template:

<issue-template>
# {pr_title}

> Issue #{issue_number} | Branch `{branch}` | Type {HITL|AFK}
> Depends on: {#n, #m | None — can start immediately}
> Source PRD: PRD-{slug}.md

## What to build

A concise description of this vertical slice. Describe the end-to-end behavior, not
layer-by-layer implementation.

## Resolved decisions

Every decision this slice needs, lifted from `PRD-{slug}.md` so the implementer asks nothing —
interface/contract, data shapes, edge cases, error behavior, etc.

## Acceptance criteria

- [ ] Specific, verifiable check (not "it works")
- [ ] ...

## Out of scope

What this slice deliberately does NOT do (and which slice it is deferred to, if any).

</issue-template>

There is no GitHub step: the CSV and the `issues/` files are the only outputs.
