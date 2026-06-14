---
chain_name: "Full Feature Lifecycle"
chain_id: feature-workflow
model: sonnet
type: workflow-chain
estimated_steps: 8
---

# Workflow: Full Feature Lifecycle

> Activate with: `/claude-code-bootstrap chain=feature-workflow`

## When to Use
Use this workflow when adding a net-new feature to the codebase, from initial scoping through deployment. It covers context loading, planning, implementation, testing, review, and release readiness.

## Chain Overview
[onboard] → [research_codebase] → [create_plan] → [implement_plan] → [backend/test-harness] → [review/validate_plan] → [review/pr-enhance] → [deploy-checklist]

## Steps

### Step 1: Onboard
- **Template**: `onboard.md`
- **Purpose**: Load agent or developer context about the repository, stack, team conventions, and open tickets so subsequent steps operate with full awareness.
- **Input**: Repo root path, any relevant Linear/Jira ticket ID or feature brief.
- **Output**: Populated context summary covering tech stack, directory structure, key contacts, and coding standards.
- **Hand-off note**: Pass the context summary and ticket ID to Step 2.

### Step 2: Research Codebase
- **Template**: `research_codebase.md`
- **Purpose**: Deep-dive into the existing codebase to understand the modules, patterns, and boundaries that the new feature will touch.
- **Input**: Context summary from Step 1, feature description, list of suspected files/domains.
- **Output**: Codebase map scoped to the feature area — entry points, data models, service boundaries, existing tests.
- **Hand-off note**: Attach the scoped codebase map and any identified risks to Step 3.

### Step 3: Create Plan
- **Template**: `create_plan.md`
- **Purpose**: Produce a detailed, reviewable implementation plan with tasks, file targets, API contracts, and acceptance criteria.
- **Input**: Feature brief, codebase map from Step 2, team conventions from Step 1.
- **Output**: `thoughts/shared/plans/<feature-slug>.md` — a structured plan with ordered tasks and success criteria.
- **Hand-off note**: Share the plan file path and the list of files to be created or modified.

### Step 4: Implement Plan
- **Template**: `implement_plan.md`
- **Purpose**: Execute the approved plan task-by-task, writing production code, migrations, and inline documentation.
- **Input**: Plan file from Step 3, codebase map, editor context.
- **Output**: Working implementation committed to a feature branch matching `{{BRANCH_PREFIX}}<feature-slug>`.
- **Hand-off note**: List all changed files and any deviations from the plan for Step 5.

### Step 5: Test Harness
- **Template**: `backend/test-harness.md`
- **Purpose**: Generate or expand the test suite covering the new feature — unit, integration, and contract tests.
- **Input**: Changed file list from Step 4, plan acceptance criteria, existing test patterns.
- **Output**: Passing test suite with coverage report; all new paths exercised.
- **Hand-off note**: Pass test results, coverage delta, and any skipped scenarios to Step 6.

### Step 6: Validate Plan
- **Template**: `review/validate_plan.md`
- **Purpose**: Cross-check the implementation against the original plan, verify every acceptance criterion is met, and document any gaps.
- **Input**: Plan file from Step 3, implementation diff from Step 4, test results from Step 5.
- **Output**: Validation report — PASS/FAIL per criterion, list of remaining gaps.
- **Hand-off note**: Attach the validation report to Step 7; surface any blocking gaps for remediation before proceeding.

### Step 7: PR Enhance
- **Template**: `review/pr-enhance.md`
- **Purpose**: Polish the pull request — improve description, add context, flag risky changes, suggest reviewer assignments, and confirm the PR template is complete.
- **Input**: Feature branch diff, validation report from Step 6, `{{PR_TEMPLATE_PATH}}`.
- **Output**: Fully populated PR ready for human review, with reviewer list and labels applied.
- **Hand-off note**: PR URL and any open review comments to Step 8.

### Step 8: Deploy Checklist
- **Template**: `deploy-checklist.md`
- **Purpose**: Walk through all pre-deployment gates — environment config, feature flags, migration order, rollback plan, and monitoring readiness.
- **Input**: PR from Step 7, infra variables (`{{CLOUD_REGION}}`, `{{ECS_CLUSTER}}`), deploy strategy `{{DEPLOY_STRATEGY}}`.
- **Output**: Signed-off deployment checklist; runbook link `{{ONCALL_RUNBOOK_URL}}` updated if required.
- **Hand-off note**: None — workflow complete after checklist sign-off.

## Decision Points
- **Step 4 → Step 5**: If the feature is purely frontend, swap `backend/test-harness.md` for `frontend/test-harness.md`.
- **Step 6 → Step 7**: If the validation report contains blocking gaps, loop back to Step 4 (implement) before continuing to PR.
- **Step 8**: If `{{DEPLOY_STRATEGY}}` is `canary`, confirm canary thresholds and automated rollback triggers before marking complete.

## Success Criteria
- All plan acceptance criteria marked PASS in the Step 6 validation report.
- Test coverage has not regressed below the project baseline.
- PR is approved by at least `{{REVIEW_REQUIRED_COUNT}}` reviewers and all CI checks are green.
- Deploy checklist is fully signed off with no outstanding action items.
