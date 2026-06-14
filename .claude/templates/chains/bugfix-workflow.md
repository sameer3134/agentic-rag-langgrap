---
chain_name: "Bug Fix Lifecycle"
chain_id: bugfix-workflow
model: sonnet
type: workflow-chain
estimated_steps: 6
---

# Workflow: Bug Fix Lifecycle

> Activate with: `/claude-code-bootstrap chain=bugfix-workflow`

## When to Use
Use this workflow when a defect has been reported or discovered and needs to be investigated, root-caused, fixed, verified, and shipped. Covers triage through PR merge.

## Chain Overview
[debug] → [smart-debug] → [(fix inline)] → [backend/test-harness OR frontend/test-harness] → [review/validate_plan] → [review/pr-enhance]

## Steps

### Step 1: Debug
- **Template**: `debug.md`
- **Purpose**: Gather initial signals — logs, error traces, reproduction steps — to frame the defect clearly before deep investigation.
- **Input**: Bug report or ticket ID, error messages, environment details (staging/production), relevant log output.
- **Output**: Structured defect brief: symptom, reproduction steps, suspected component, severity label.
- **Hand-off note**: Pass the defect brief and any stack traces to Step 2.

### Step 2: Smart Debug
- **Template**: `smart-debug.md`
- **Purpose**: Run a multi-angle investigation using specialized sub-agents to isolate the root cause across logs, git history, database state, and code paths.
- **Input**: Defect brief from Step 1, repo path, access to `{{MONITORING_DASHBOARD_URL}}` and `{{RDS_ENDPOINT}}` if applicable.
- **Output**: Root-cause analysis document: confirmed cause, affected code location(s), blast radius, and recommended fix approach.
- **Hand-off note**: Root-cause doc, file paths of broken code, and fix approach to Step 3.

### Step 3: Fix (Inline)
- **Template**: *(direct implementation — no dedicated template)*
- **Purpose**: Apply the minimal, targeted fix confirmed by the root-cause analysis. Avoid scope creep; document any discovered tech debt separately.
- **Input**: Root-cause doc from Step 2, affected file list.
- **Output**: Fix committed to branch `{{BRANCH_PREFIX}}fix/<bug-slug>` using commit format `{{COMMIT_FORMAT}}`.
- **Hand-off note**: Diff of the fix, list of changed files, and the specific scenario that triggered the bug to Step 4.

### Step 4: Test Harness
- **Template**: `backend/test-harness.md` (backend defect) OR `frontend/test-harness.md` (UI/browser defect)
- **Purpose**: Write a regression test that would have caught this bug, plus verify the fix does not break adjacent behavior.
- **Input**: Fix diff from Step 3, reproduction steps, existing test suite location.
- **Output**: New regression test(s) passing; full test suite green; coverage report showing the defective path is now exercised.
- **Hand-off note**: Test results, regression test file paths, and any edge cases left untested to Step 5.

### Step 5: Validate Plan
- **Template**: `review/validate_plan.md`
- **Purpose**: Confirm the fix resolves the original defect, the regression test is meaningful, and no new issues were introduced.
- **Input**: Original bug report, fix diff from Step 3, test results from Step 4, root-cause doc from Step 2.
- **Output**: Validation report — defect resolved (yes/no), regression covered (yes/no), side-effect risk assessment.
- **Hand-off note**: Validation report and any residual risk notes to Step 6.

### Step 6: PR Enhance
- **Template**: `review/pr-enhance.md`
- **Purpose**: Finalize the pull request with a clear description linking the fix to the original report, highlight the regression test, and assign appropriate reviewers.
- **Input**: Fix branch diff, validation report from Step 5, `{{PR_TEMPLATE_PATH}}`, `{{DEFAULT_REVIEWER}}`.
- **Output**: Merged-ready PR with populated description, linked issue, labels (e.g., `bug`, `regression-test`), and reviewer assignments.
- **Hand-off note**: None — workflow complete once PR is approved and CI is green.

## Decision Points
- **Step 1 → Step 2**: If the bug is trivially obvious from Step 1 (typo, config error), skip Step 2 and proceed directly to Step 3.
- **Step 4 template choice**: Use `backend/test-harness.md` for API, service, or data-layer bugs. Use `frontend/test-harness.md` for rendering, event-handling, or browser-specific bugs. Use both if the defect spans layers.
- **Step 5 → fix loop**: If the validation report shows the defect is not fully resolved, return to Step 3 and re-apply the fix before re-running Steps 4 and 5.
- **Post-Step 6**: If severity is P0/P1, trigger the oncall runbook at `{{ONCALL_RUNBOOK_URL}}` and notify `{{SLACK_CHANNEL}}` after merge.

## Success Criteria
- Original defect reproduction steps no longer reproduce the bug on the fix branch.
- At least one regression test specifically targeting the defect is present and passing.
- Full test suite is green with no new failures.
- Validation report shows PASS for both defect resolution and regression coverage.
- PR approved by `{{REVIEW_REQUIRED_COUNT}}` reviewer(s) with CI green.
