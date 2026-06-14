---
description: Create git worktrees for one or more PRs by scanning for the PR map CSV and calling make-worktrees.sh
model: deepseek/deepseek-v4-flash
---

## Graphify Context
> Key architectural communities: Git Workflow, PR Management, Planning Infrastructure.
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Make Worktrees

You are tasked with creating a separate git worktree for each requested PR so they can be implemented in parallel. Shared resources are symlinked from the main repo via `.claude/worktree-symlinks`.

> **Design principle:** `.claude/scripts/make-worktrees.sh` is the permanent parameterised script.
> This command only looks up data from the CSV and passes it as arguments — no script generation,
> one Bash call per PR.

## Steps to follow:

1. **Parse the PR arguments:**
   - Normalise every value to `PR-{N}` form: `"15"` → `"PR-15"`, `"PR-16,"` → `"PR-16"`
   - If no arguments provided:
     ```
     Usage: /make-worktrees PR-N PR-M ...
     Run /find-ready-prs first to see which PRs are unblocked.
     ```
     Stop.

2. **Discover the PR map CSV:**
   ```bash
   grep -rl "Branch_Name" --include="*.csv" \
     --exclude-dir=node_modules --exclude-dir=.git \
     --exclude-dir=venv --exclude-dir=.venv \
     . 2>/dev/null | head -1
   ```
   If not found: stop and tell the user no PR map CSV was found.

3. **Look up each PR in the CSV:**
   - Read the discovered CSV
   - For each requested PR ID, extract `Branch_Name`, `PR_Title`, `Status`
   - If a PR ID is not in the CSV: warn and skip it
   - If `Status` is `DONE`: warn and skip it
   - Derive `Slug` = last path segment of `Branch_Name`:
     - `feat/s01/user-auth` → `user-auth`
     - `auth/s04/csrf-middleware` → `csrf-middleware`

4. **Call the permanent script once per PR, sequentially:**
   ```bash
   bash .claude/scripts/make-worktrees.sh \
     --pr-id <PR-N> \
     --branch <Branch_Name> \
     --slug <Slug> \
     --force
   ```
   Wait for each to finish. The script reads `.claude/worktree-prefix` and `.claude/worktree-symlinks` automatically.

5. **Print the summary:**
   ```
   Worktrees created
   ──────────────────────────────────────────────────────────────────
   PR     Branch                      Directory
   PR-15  feat/s01/user-auth          ../tdx-user-auth
   PR-16  feat/s01/session-mgmt       ../tdx-session-mgmt

   Next step in each worktree:
     cd ../tdx-user-auth    then run /pr-plan-create
     cd ../tdx-session-mgmt then run /pr-plan-create

   To run all in parallel: open each directory in a separate terminal tab.
   ```

6. **Print the cleanup reference:**
   ```
   When a PR is merged:
     git worktree remove ../tdx-user-auth
     git branch -d feat/s01/user-auth
   ```

## Important notes:
- `--force` is always passed so this command is safely re-runnable
- If `.claude/scripts/make-worktrees.sh` is missing, stop and inform the user
