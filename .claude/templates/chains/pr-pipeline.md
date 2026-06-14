---
chain_name: PR Implementation Pipeline
chain_id: pr-pipeline
model: sonnet
type: workflow-chain
estimated_steps: 6
---

# Workflow: PR Implementation Pipeline

> Activate with: `/pr-pipeline [PR-N PR-M ...] [--base <branch>] [PR-N:base=<branch> ...]`
>
> Examples:
> - `/pr-pipeline` — all READY PRs, base from `.claude/pr-default-base`
> - `/pr-pipeline PR-1 PR-2 --base main` — override DEFAULT_BASE for all tiers
> - `/pr-pipeline PR-2:base=feat/s01/user-auth PR-3:base=feat/s01/user-auth` — per-PR base override

## When to Use
Use this workflow to fully automate PR implementation — plan, implement, review, and raise draft PRs — with zero human intervention after invocation.

## NO CONFIRMATION RULE
**Never ask the user to confirm, verify, or approve anything during this pipeline.** This applies to:
- Branch names, PR IDs, slugs, file paths — if it is derivable from the plan, CSV, or git state, use it directly
- Discovered file paths — trust `grep -rl` results and proceed
- Ambiguous decisions — apply the conservative default (nullable=yes, ondelete=RESTRICT, VARCHAR(255)) and log it in `## Assumptions`
- Worktree paths — derive from prefix + slug and proceed
- Base branch — resolve from BASE_OVERRIDES, then `--base` flag, then `.claude/pr-default-base`, fallback `main`; never ask
- **Tier transitions — after each Workflow completes, immediately proceed to Step 4 without pausing, printing a summary, or waiting for user input. The pipeline is a continuous loop, not a checkpoint sequence.**

Any agent that pauses to confirm a value that is already present in the plan, CSV, or git output is violating this rule. Any pause between tiers is a violation.

## Execution model

| Phase | Mode |
|---|---|
| Step 1: discover files, classify PRs, compute tiers | Sequential in this session |
| Step 2 (per tier): create worktrees for that tier | Sequential in this session |
| Step 3 (per tier): plan + implement + review + raise | **Parallel via Workflow tool — wait for completion before next tier** |

Tiers are computed from the `Depends_On` column. Tier 0 = no dependencies (or all deps already merged). Tier 1 = depends only on Tier 0 PRs. And so on. Each tier's Workflow must complete — including the Raise stage that pushes branches to remote — before the next tier's worktrees are created.

## Chain Overview
[discover + tier-compute] → **for each tier:**
  [make-worktrees for tier N] → [Workflow(plan + implement + review + raise × tier-N PRs)] → wait → repeat

---

## Step 1: Discover planning files and find ready PRs

**Discover the PR map CSV and all supporting files:**
```bash
# PR map (has Branch_Name column)
grep -rl "Branch_Name" --include="*.csv" \
  --exclude-dir=node_modules --exclude-dir=.git \
  --exclude-dir=venv --exclude-dir=.venv \
  . 2>/dev/null | head -1

# Tasks CSV (has Task_ID column)
grep -rl "Task_ID" --include="*.csv" \
  --exclude-dir=node_modules --exclude-dir=.git \
  --exclude-dir=venv --exclude-dir=.venv \
  . 2>/dev/null | head -1

# PRD / spec
grep -rl "## Stories\|## Requirements\|## Goals\|## Overview" --include="*.md" \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.claude \
  . 2>/dev/null | head -1

# Architecture reference
grep -rl "3-layer\|ABC interface\|layer model\|service layer" --include="*.md" \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.claude \
  . 2>/dev/null | head -1

# Issues / lessons learned
grep -rl "Known Issues\|ISSUE-\|Prevention rule\|Root cause" --include="*.md" \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.claude \
  . 2>/dev/null | head -1

# Progress / status
grep -rl "## Done\|## In progress\|Status as of\|## Milestone" --include="*.md" \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.claude \
  . 2>/dev/null | head -1

# Domain glossary
grep -rl "Domain Glossary\|canonical definition\|\[inferred" --include="*.md" \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.claude \
  . 2>/dev/null | head -1
```

Store as: `PR_MAP`, `TASKS_CSV`, `PRD_FILE`, `ARCH_FILE`, `ISSUES_FILE`, `PROGRESS_FILE`, `GLOSSARY_FILE`.
If `PR_MAP` is not found: stop and tell the user no PR map CSV was found.

**Parse invocation arguments:**
- Collect bare `PR-N` tokens → requested PR IDs
- Collect `PR-N:base=<branch>` tokens → store in `BASE_OVERRIDES` map (e.g. `{"PR-2": "feat/s01/user-auth"}`)
- Collect `--base <branch>` flag → store as `GLOBAL_BASE_OVERRIDE` (applies to any PR without a per-PR override)
- Normalise every PR ID to `PR-{N}` form: `"15"` → `"PR-15"`

**Classify PRs from the PR map:**
```bash
git branch -r --merged origin/main 2>/dev/null | sed 's|.*origin/||' | tr -d ' ' | sort
git branch --list | sed 's/[* ]*//' | sort
```
- If arguments provided: filter to those PR IDs (warn and skip non-READY ones)
- If no arguments: use all READY PRs
- If no READY PRs remain: print the status table and stop

**Build a full PR_ID → Branch_Name lookup** from the entire PR map CSV (all rows, not just READY):
Store as `BRANCH_MAP`. This is needed in Step 2 to resolve dependency branches.

**Compute dependency tiers** across the READY PRs:
- **Tier 0**: READY PRs whose `Depends_On` is empty, or whose dependency's branch is already merged into `DEFAULT_BASE`
  (check: `git branch -r --merged origin/<DEFAULT_BASE> | grep <dep-branch>`)
- **Tier 1**: READY PRs whose `Depends_On` points to a Tier 0 PR
- **Tier N**: READY PRs whose `Depends_On` points to a Tier N-1 PR
- If a READY PR's `Depends_On` points to a non-READY PR that is not merged: mark it BLOCKED, exclude from all tiers, log it

Print the tier table:
```
Tier 0 (run now):   PR-1
Tier 1 (after PR-1 raises): PR-2, PR-3
Tier 2 (after PR-2, PR-3 raise): PR-4, PR-5
Blocked (dep not READY or merged): PR-6 — depends on PR-X (DRAFT)
```

Continue immediately to Step 2.

---

## Step 2: Create Worktrees for the Current Tier

This step runs once per tier. On the first pass it processes Tier 0. After each Workflow completes it re-runs for the next tier (see Step 4).

Resolve `DEFAULT_BASE` in priority order:
1. `GLOBAL_BASE_OVERRIDE` (from `--base` flag) if set
2. Contents of `.claude/pr-default-base` if the file exists
3. Fallback: `main`

**Resolve the skills directory** — single source of truth for all stage logic:
```bash
echo "$(pwd)/.claude/commands/general"
```
Store as `SKILLS_DIR`.

For each PR in the current tier:
- Derive `Slug` = last path segment of `Branch_Name`
- Read prefix from `.claude/worktree-prefix`; fallback = first 3 chars of repo dir name (lowercased)
- Set `WORKTREE_PATH` = `<parent of repo root>/<prefix>-<Slug>`
- If `WORKTREE_PATH` already exists: record it, skip creation

**Resolve `FROM_BRANCH` and `BASE`** for each PR:

Base resolution priority (highest to lowest):
1. `BASE_OVERRIDES[PR-N]` — per-PR override from invocation args (e.g. `PR-2:base=feat/s01/user-auth`)
2. `GLOBAL_BASE_OVERRIDE` — `--base` flag value
3. Auto-derived from dep branch (Tier 1+ only, see below)
4. `DEFAULT_BASE`

```bash
# Tier 0 PRs: no dependency
FROM_BRANCH=""
BASE = BASE_OVERRIDES[PR-N] ?? GLOBAL_BASE_OVERRIDE ?? DEFAULT_BASE

# Tier 1+ PRs: dependency branch must be on remote (pushed by the previous tier's Raise stage)
DEP_BRANCH=$(lookup Branch_Name for Depends_On PR_ID in BRANCH_MAP)
git fetch origin ${DEP_BRANCH} 2>/dev/null
git show-ref --verify --quiet refs/remotes/origin/${DEP_BRANCH} \
  && echo "dep-available" || echo "dep-missing"
```

- **dep-available** (`origin/<DEP_BRANCH>` exists):
  `FROM_BRANCH = DEP_BRANCH`
  `BASE = BASE_OVERRIDES[PR-N] ?? GLOBAL_BASE_OVERRIDE ?? DEP_BRANCH`
  Worktree branches from the dependency's pushed tip.
- **dep-missing** (`origin/<DEP_BRANCH>` not found): this PR cannot run yet.
  **Do not create a worktree. Do not include it in this tier's args. Log:**
  `PR-N: DEFERRED — origin/<DEP_BRANCH> not on remote yet. Rerun after dependency's Raise pushes it.`

Create worktree only for dep-available and Tier 0 PRs:
```bash
bash .claude/scripts/make-worktrees.sh \
  --pr-id <PR-N> --branch <Branch_Name> --slug <Slug> \
  ${FROM_BRANCH:+--from-branch ${FROM_BRANCH}} --force
```

Build the Workflow args array for this tier's PRs:
```json
[
  {
    "prId": "PR-1",
    "worktreePath": "/abs/path/to/tdx-user-auth",
    "branch": "feat/s01/user-auth",
    "slug": "user-auth",
    "title": "Add user authentication",
    "base": "main",
    "skillsDir": "/abs/path/to/.claude/commands/general",
    "prMapCsv": "/abs/path/to/pr-map.csv",
    "tasksCsv": "/abs/path/to/tasks.csv",
    "prdFile": "/abs/path/to/project-doc.md",
    "archFile": "/abs/path/to/architecture.md",
    "issuesFile": "/abs/path/to/issues.md",
    "progressFile": "/abs/path/to/progress.md",
    "glossaryFile": "/abs/path/to/CONTEXT.md"
  }
]
```

Use absolute paths. Missing files are empty strings `""` — subagents skip them.

Continue immediately to Step 3.

---

## Step 3: Run Workflow for Current Tier

Invoke the **Workflow tool** with the following script and the args array from Step 2.
**Wait for this Workflow to complete before proceeding to Step 4** — the Raise stage pushes branches to remote, which is what makes the next tier's dep-available checks pass.

```javascript
export const meta = {
  name: 'pr-full-pipeline',
  description: 'Plan, implement, review, and raise draft PRs for multiple worktrees in parallel',
  phases: [
    { title: 'Plan',      detail: 'Follow pr-plan-create skill in worktree' },
    { title: 'Implement', detail: 'Follow pr-implement skill in worktree' },
    { title: 'Review',    detail: 'Follow pr-review skill: correctness, security, layer compliance' },
    { title: 'Raise',     detail: 'Follow pr-raise skill: generate PR body and open draft PR' },
  ],
}

// args = array of PR objects with pre-resolved absolute file paths and skillsDir

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    verdict:        { type: 'string', enum: ['PASS', 'NEEDS_WORK', 'FAIL'] },
    criticalCount:  { type: 'number' },
    importantCount: { type: 'number' },
    reviewFilePath: { type: 'string' },
  },
  required: ['verdict', 'reviewFilePath'],
}

const RAISE_SCHEMA = {
  type: 'object',
  properties: {
    prUrl:   { type: 'string' },
    skipped: { type: 'boolean' },
    reason:  { type: 'string' },
  },
  required: [],
}

const results = await pipeline(
  args,

  // ── Stage 1: Plan ─────────────────────────────────────────
  (pr) => agent(
    `Read the file at ${pr.skillsDir}/pr-plan-create.md and follow its instructions exactly.

    Runtime context for this run — use these values directly, skip all discovery grep commands in the skill:
    - Working directory: ${pr.worktreePath} — run all bash commands as: bash -c "cd ${pr.worktreePath} && <command>"
    - PR_ID: ${pr.prId}
    - Branch: ${pr.branch}
    - PR map CSV:    ${pr.prMapCsv}
    - Tasks CSV:     ${pr.tasksCsv}
    - PRD/spec:      ${pr.prdFile}
    - CLAUDE.md:     ${pr.worktreePath}/CLAUDE.md
    - Architecture:  ${pr.archFile}
    - Progress:      ${pr.progressFile}
    - Issues:        ${pr.issuesFile}
    - Glossary:      ${pr.glossaryFile}
    - Plan output:   ${pr.worktreePath}/thoughts/shared/plans/

    NEVER ask for confirmation. Apply conservative defaults and log every automated decision in ## Assumptions.
    Return the absolute path to the written plan file.`,
    { label: `plan:${pr.prId}`, phase: 'Plan', model: 'sonnet' }
  ),

  // ── Stage 2: Implement ────────────────────────────────────
  (planPath, pr) => agent(
    `Read the file at ${pr.skillsDir}/pr-implement.md and follow its instructions exactly.

    Runtime context for this run:
    - Working directory: ${pr.worktreePath} — run all bash commands as: bash -c "cd ${pr.worktreePath} && <command>"
    - Plan file: ${planPath}
    - CLAUDE.md: ${pr.worktreePath}/CLAUDE.md

    NEVER ask for confirmation. Implement each task in plan order, run acceptance criteria after each task, fix failures before proceeding.
    Return a summary of tasks completed and checks passed.`,
    { label: `implement:${pr.prId}`, phase: 'Implement', model: 'haiku' }
  ),

  // ── Stage 3: Review ───────────────────────────────────────
  (_, pr) => agent(
    `Read the file at ${pr.skillsDir}/pr-review.md and follow its instructions exactly.

    Runtime context for this run:
    - Working directory: ${pr.worktreePath} — run all bash commands as: bash -c "cd ${pr.worktreePath} && <command>"
    - Branch: ${pr.branch}
    - Plan file: ${pr.worktreePath}/thoughts/shared/plans/ (match branch ${pr.branch})
    - Review output: ${pr.worktreePath}/thoughts/shared/reviews/${pr.slug}-review.md
    - PR map CSV: ${pr.prMapCsv}

    NEVER ask for confirmation.
    Return verdict (PASS / NEEDS_WORK / FAIL) and the absolute review file path as structured output.`,
    { label: `review:${pr.prId}`, phase: 'Review', schema: REVIEW_SCHEMA, model: 'sonnet' }
  ),

  // ── Stage 4: Raise draft PR ───────────────────────────────
  (review, pr) => {
    if (review && review.verdict === 'FAIL') {
      log(`${pr.prId}: skipping raise — FAIL (${review.criticalCount} critical findings)`)
      return Promise.resolve({ skipped: true, reason: `FAIL — ${review.criticalCount} critical findings` })
    }
    return agent(
      `Read the file at ${pr.skillsDir}/pr-raise.md and follow its instructions exactly.

      Runtime context for this run:
      - Working directory: ${pr.worktreePath} — run all bash commands as: bash -c "cd ${pr.worktreePath} && <command>"
      - Branch: ${pr.branch}
      - Base: ${pr.base}
      - PR_ID: ${pr.prId}
      - Title: ${pr.title}
      - Review file: ${review ? review.reviewFilePath : ''}
      - Review verdict: ${review ? review.verdict : 'N/A'}
      - PR map CSV: ${pr.prMapCsv}
      - PR body output: ${pr.worktreePath}/thoughts/shared/prs/${pr.prId}-${pr.slug}.md

      NEVER ask for confirmation. All values are pre-resolved — use them directly.
      Return the PR URL, or { skipped: true, reason: "..." } if gh is unavailable.`,
      { label: `raise:${pr.prId}`, phase: 'Raise', schema: RAISE_SCHEMA, model: 'haiku' }
    )
  }
)

return results
```

---

## Step 4: Tier Checkpoint — pause for manual intervention

After each Workflow completes, **stop and print the tier summary before doing anything else**.

### 4a. Print the tier summary

```
──────────────────────────────────────────────────────────────────
Tier <N> complete

  PR-1  base: main  ✓ plan  ✓ impl  ✓ PASS  ✓ https://github.com/.../pull/42
  PR-2  base: main  ✓ plan  ✓ impl  ✗ FAIL  ✗ skipped — 2 critical findings

Pushed to remote:  PR-1 ✓   PR-2 ✗ (raise skipped)
Next tier:         Tier 1 — PR-3, PR-4  (both depend on PR-1)
Deferred:          PR-5 — depends on PR-2 (raise skipped, branch not on remote)
──────────────────────────────────────────────────────────────────
Proceed to Tier 1? You can:
  • Press Enter (or say "yes") to proceed with defaults
  • Override a base branch:   PR-3:base=feat/some-branch
  • Skip a PR in next tier:   skip=PR-4
  • Override base for all:    --base=<branch>
  • Stop here:                stop
```

**Wait for the user to respond. Do not proceed until a response is received.**

### 4b. Parse the user's response

Accept free-form input — extract intent:
- `yes` / empty / Enter → proceed with defaults
- `stop` / `no` → go to Step 5 (final summary), do not run further tiers
- `PR-N:base=<branch>` → store in BASE_OVERRIDES for the next tier only
- `skip=PR-N` → remove PR-N from the next tier's args
- `--base=<branch>` → store as GLOBAL_BASE_OVERRIDE for all remaining tiers

Multiple overrides can appear in one response: `PR-3:base=main skip=PR-4`.

### 4c. Advance

1. **Identify the next tier** from the tier table. If none remain, or user said stop, go to Step 5.

2. **Verify pushes** for the completed tier:
   ```bash
   git fetch origin
   git show-ref --verify --quiet refs/remotes/origin/<branch> \
     && echo "pushed" || echo "not pushed"
   ```
   Branches not pushed (FAIL or gh-unavailable) cannot unblock dependents — mark those DEFERRED.

3. **Re-run Step 2** for the next tier with the resolved BASE_OVERRIDES.

4. **Re-run Step 3** for the next tier.

5. Return to Step 4 when that Workflow completes.

---

## Step 5: Final Summary (printed once, after all tiers complete)

Only printed when no further tiers remain. This is the only user-facing output after Step 1's tier table.

```
Pipeline complete
──────────────────────────────────────────────────────────────────
Tier 0:
  PR-1  base: main                ✓ plan  ✓ impl  ✓ PASS  ✓ https://github.com/.../pull/42

Tier 1:
  PR-2  base: feat/s01/user-auth  ✓ plan  ✓ impl  ✓ PASS  ✓ https://github.com/.../pull/43
  PR-3  base: feat/s01/user-auth  ✓ plan  ✓ impl  ✗ FAIL  ✗ skipped (fix → re-run /pr-raise)

Deferred (raise skipped): PR-4 — depends on PR-3 (raise skipped, branch not pushed)
Blocked (dep not READY):  PR-6 — depends on PR-X (DRAFT)
```

---

## Decision Points
- Step 1: Non-READY PR IDs in args → warn and skip, do not stop
- Step 1: PR whose `Depends_On` points to a non-READY, non-merged PR → BLOCKED, excluded from all tiers
- Step 1: `PR-N:base=<branch>` in args → stored in BASE_OVERRIDES, used in Step 2 at highest priority
- Step 1: `--base <branch>` in args → stored as GLOBAL_BASE_OVERRIDE, used when no per-PR override exists
- Step 2: Worktree already exists → skip creation, use existing path
- Step 2: Tier 0 → `FROM_BRANCH = ""`, `BASE = BASE_OVERRIDES[PR-N] ?? GLOBAL_BASE_OVERRIDE ?? DEFAULT_BASE`
- Step 2: Tier N, dep on remote → `FROM_BRANCH = dep`, `BASE = BASE_OVERRIDES[PR-N] ?? GLOBAL_BASE_OVERRIDE ?? dep`
- Step 2: Tier N, dep NOT on remote → DEFERRED — skip this PR, do not create worktree
- Step 4: Workflow returns → print tier summary, **pause and wait for user response** before proceeding
- Step 4: User says "stop" or no further tiers → go to Step 5
- Step 4: User provides `PR-N:base=<branch>` → applies to next tier only, overrides dep-resolved base
- Step 4: User provides `skip=PR-N` → removes that PR from the next tier's args
- Step 4: User provides `--base=<branch>` → applies to all remaining tiers as GLOBAL_BASE_OVERRIDE
- Step 4: Previous tier had FAIL/skipped raise → branch not pushed; dependents deferred
- Step 5: Only reached when no tiers remain — this is the only summary printed
- Stage 1: Plan file already exists → skip writing, return existing path
- Stage 4: FAIL verdict → skip raise; branch not pushed; dependents deferred
- Stage 4: gh unavailable → skip raise; branch not pushed; dependents deferred

## Success Criteria
Pipeline runs all tiers to completion without pausing. Final output is printed once at Step 5.
