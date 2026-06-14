---
description: Identify unblocked PRs ready to implement by scanning for the PR map CSV and checking git branch state
model: deepseek/deepseek-v4-flash
---

## Graphify Context
> Key architectural communities: Planning Infrastructure, Git Workflow, PR Dependency Graph.
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Find Ready PRs

You are tasked with reading the PR dependency map and git state to identify which PRs can be started immediately, and which are blocked.

## Steps to follow:

1. **Discover the PR map CSV:**
   ```bash
   grep -rl "Branch_Name" --include="*.csv" \
     --exclude-dir=node_modules --exclude-dir=.git \
     --exclude-dir=venv --exclude-dir=.venv \
     . 2>/dev/null | head -1
   ```
   - If no file found: stop and tell the user no PR map CSV was found in this repo. They should create one with at minimum these columns: `PR_ID, Branch_Name, PR_Title, Depends_On, Parallel_Group, Status`
   - Store the result as `PR_MAP`

2. **Read the PR map:**
   - Read `PR_MAP` completely
   - Identify the column positions for: `PR_ID`, `Branch_Name`, `PR_Title`, `Depends_On`, `Parallel_Group`, `Status`
   - `Depends_On` is pipe-separated PR IDs (e.g. `PR-1|PR-2`), empty if no dependencies

3. **Collect git state:**
   ```bash
   git branch -r --merged origin/main 2>/dev/null | sed 's|.*origin/||' | tr -d ' ' | sort
   git branch --list | sed 's/[* ]*//' | sort
   git worktree list --porcelain
   ```

4. **Classify each PR** (first match wins):
   - **DONE**: CSV `Status` is `DONE`, or `Branch_Name` appears in the merged-into-main list
   - **REVIEW**: CSV `Status` is `REVIEW`
   - **IN_PROGRESS**: `Branch_Name` exists locally and is not merged
   - **READY**: Status is TODO, and `Depends_On` is empty OR every listed PR_ID is DONE
   - **BLOCKED**: Status is TODO, and at least one `Depends_On` PR is not DONE — name which

5. **Print the status table:**
   ```
   PR map: <PR_MAP>

   PR      STATUS         GROUP   BRANCH                              TITLE
   ──────  ─────────────  ──────  ──────────────────────────────────  ──────────────────────
   PR-1    ✅ READY        G1      feat/s01/user-auth                  Add user authentication
   PR-3    🚫 BLOCKED      G2      feat/s02/rbac                       RBAC model  ← needs PR-2
   PR-2    ✔  DONE         –       feat/s00/scaffold                   Initial scaffold
   ```

6. **Print the summary block:**
   ```
   Summary
   ───────────────────────────────────────────────────────────────────
     ✅  READY:        N  PR(s) — can be started now
     ⚙️   IN_PROGRESS:  N  PR(s) — already underway
     👁️   REVIEW:       N  PR(s) — awaiting review
     🚫  BLOCKED:      N  PR(s) — waiting on dependencies
     ✔   DONE:         N  PR(s) — merged

   Ready PRs by parallel group
   ───────────────────────────────────────────────────────────────────
     Group G1 — all can be parallelised:
       PR-1  feat/s01/user-auth

   Next steps
   ───────────────────────────────────────────────────────────────────
     /make-worktrees PR-1    set up worktrees for ready PRs
     /pr-pipeline PR-1       run full pipeline for these PRs
   ```

## Important notes:
- Git state is authoritative over CSV Status — a branch that exists locally is IN_PROGRESS regardless of what the CSV says
- A branch merged into origin/main is DONE regardless of CSV Status
- When listing BLOCKED PRs, always name the specific dependency that is not yet DONE
