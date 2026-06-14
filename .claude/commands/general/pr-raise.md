---
description: Generate PR body from review output and open a draft pull request via gh CLI
model: deepseek/deepseek-v4-flash
---

## Graphify Context
> Key architectural communities: Git Workflow, PR Management, Planning Infrastructure.
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Raise Draft PR

You are tasked with generating a clean pull request body and opening a draft PR on GitHub. This step is **optional** — if the gh CLI is not installed or not authenticated, skip gracefully and tell the user how to run it later.

## Steps to follow:

1. **Check GitHub availability first:**
   ```bash
   gh auth status 2>&1
   ```
   - If the command fails or gh is not found, respond with:
     ```
     GitHub CLI (gh) is not connected in this session.
     Skipping PR creation — run /pr-raise again once gh is authenticated.
     To authenticate: gh auth login
     ```
     Stop. Do not treat this as an error.

2. **Auto-detect the current PR:**
   - Run `git branch --show-current`
   - Discover the PR map CSV:
     ```bash
     grep -rl "Branch_Name" --include="*.csv" \
       --exclude-dir=node_modules --exclude-dir=.git \
       --exclude-dir=venv --exclude-dir=.venv \
       . 2>/dev/null | head -1
     ```
     If not found: stop and tell the user no PR map CSV was found.
   - Read the discovered CSV — find the row where `Branch_Name` matches the current branch
   - Extract `PR_ID`, `PR_Title`, `Story`, `Branch_Name`, `Depends_On`
   - If not found: stop and tell the user the current branch is not in the PR map CSV

3. **Determine the base branch:**
   - Read `.claude/pr-default-base` if it exists → use that value
   - If the file does not exist: default to `main`
   - No user input required

4. **Collect supporting context:**
   - Read the review file: `thoughts/shared/reviews/{branch-slug}-review.md` — note the verdict and any critical/important findings
   - Read the plan file: `thoughts/shared/plans/{Story}-{slug}.md` — extract the "What This PR Does" summary and task list
   - Run `git diff origin/main...HEAD --stat` for the changed-files list

5. **Write the PR body to a file:**
   Write to `thoughts/shared/prs/{PR_ID}-{slug}.md`:

   ```markdown
   ## Summary

   [2–3 sentences from the plan's "What This PR Does" section — plain English]

   ## Changes

   [Bullet list derived from git diff --stat: one line per changed file with a brief purpose]

   ## Tasks covered

   | Task | What it builds |
   |------|---------------|
   | {Task_ID} | {plain-English description from plan} |

   ## Test plan

   - [ ] [Acceptance criterion from the plan — specific and verifiable]
   - [ ] [Acceptance criterion]
   - [ ] All automated checks pass: `make test-cov && make lint`

   ## Review notes

   Review verdict: {PASS / NEEDS_WORK / FAIL from review file}

   [If NEEDS_WORK: list the important findings that were addressed since the review]
   [If PASS: "No outstanding findings."]

   ---
   🤖 Plan: `thoughts/shared/plans/{filename}`
   🔍 Review: `thoughts/shared/reviews/{slug}-review.md`
   ```

6. **Call the permanent script:**
   ```bash
   bash .claude/scripts/raise-pr.sh \
     --branch <Branch_Name> \
     --base <base-branch> \
     --title "<PR_ID>: <PR_Title>" \
     --body-file thoughts/shared/prs/<PR_ID>-<slug>.md \
     --pr-id <PR_ID>
   ```
   - If the script exits with code 2 (gh unavailable/unauthenticated): print the skip message and stop cleanly — do not report an error.
   - If the script exits with code 1: report the error and stop.

7. **Update the CSV and report:**
   - Update the discovered PR map CSV: set `Status` to `REVIEW` for this PR
   - Print:
     ```
     ✓ Draft PR open: <PR_URL>

     docs/planning/new_git.csv — Status updated to REVIEW for <PR_ID>

     Next:
       • Address any reviewer comments, then: gh pr ready
       • Run /find-ready-prs to see what PRs are now unblocked
     ```

## Important notes:
- Do not open the PR if the review verdict was FAIL — stop and say: "Review verdict is FAIL. Fix the critical findings and re-run /pr-review before raising a PR."
- If verdict is NEEDS_WORK: proceed automatically but add a note in the PR body's review notes section — "Proceeding despite NEEDS_WORK — important findings may remain unresolved; reviewer should check."
- The PR body file is written before calling the script so the user can inspect or edit it first
- This command is safely re-runnable — if the PR already exists, `gh pr create` will exit with an error; catch it and print the existing PR URL instead
