---
chain_name: "Developer & Agent Onboarding"
chain_id: onboarding-workflow
model: sonnet
type: workflow-chain
estimated_steps: 5
---

# Workflow: Developer & Agent Onboarding

> Activate with: `/claude-code-bootstrap chain=onboarding-workflow`

## When to Use
Use this workflow when a new developer joins the team or when a fresh agent session needs to be fully context-loaded on the codebase before starting productive work. It builds layered understanding from high-level orientation down to hands-on first-task planning.

## Chain Overview
[onboard] → [research_codebase] → [research_codebase_generic] → [create_plan (first task)] → [general/code-explain (unfamiliar areas)]

## Steps

### Step 1: Onboard
- **Template**: `onboard.md`
- **Purpose**: Orient the new developer or agent with team structure, tooling, access requirements, communication norms, and the repository layout at a high level.
- **Input**: New member's role, start date, any assigned onboarding ticket or first task description, `{{SLACK_CHANNEL}}`, `{{INTERNAL_DOCS_URL}}`, `{{REPO_URL}}`.
- **Output**: Onboarding summary — team contacts, key tools and access checklist, repo structure overview, communication channels, and links to essential documentation.
- **Hand-off note**: Onboarding summary, assigned first-task description, and any ticket ID to Step 2.

### Step 2: Research Codebase
- **Template**: `research_codebase.md`
- **Purpose**: Produce a structured, historical record of the codebase as it currently exists — architecture decisions, major modules, data flow, and known pain points — stored in the `thoughts/` directory for future reference.
- **Input**: Repo root path, onboarding summary from Step 1, first-task description to scope the deepest research areas.
- **Output**: `thoughts/shared/codebase-map.md` — authoritative codebase snapshot covering architecture, key files, service boundaries, and tech stack details.
- **Hand-off note**: Path to codebase map and the list of modules most relevant to the first task to Step 3.

### Step 3: Research Codebase (Generic / Parallel)
- **Template**: `research_codebase_generic.md`
- **Purpose**: Complement Step 2 with a broader, parallel multi-agent sweep that surfaces patterns, conventions, and domain-specific details that a single-agent pass might miss.
- **Input**: Codebase map from Step 2, module list, repo root path.
- **Output**: Supplementary research notes covering coding conventions, recurring patterns, anti-patterns, and any undocumented tribal knowledge found in comments or commit history.
- **Hand-off note**: Combined codebase knowledge (Steps 2 + 3 outputs) and first-task description to Step 4.

### Step 4: Create Plan (First Task)
- **Template**: `create_plan.md`
- **Purpose**: Convert the first assigned task into a concrete, reviewable implementation plan so the new member can hit the ground running with clear direction and defined success criteria.
- **Input**: First-task description or ticket ID, combined codebase knowledge from Steps 2 and 3, team conventions (`{{BRANCH_PREFIX}}`, `{{COMMIT_FORMAT}}`, `{{PR_SIZE_LIMIT}}`, `{{REVIEW_REQUIRED_COUNT}}`).
- **Output**: `thoughts/shared/plans/<first-task-slug>.md` — ordered task list, file targets, acceptance criteria, and definition of done.
- **Hand-off note**: Plan file path and a list of any modules the new member is not yet familiar with to Step 5.

### Step 5: Code Explain (Unfamiliar Areas)
- **Template**: `general/code-explain.md`
- **Purpose**: Walk through the specific files, functions, or subsystems that the new member needs to understand in order to execute the first-task plan — providing annotated explanations, data-flow diagrams, and "why it was built this way" context.
- **Input**: List of unfamiliar modules from Step 4, codebase map from Step 2, plan file from Step 4.
- **Output**: Annotated explanations for each flagged area — function-by-function walkthroughs, interaction diagrams, and pointers to related tests and documentation.
- **Hand-off note**: None — workflow complete. The new member/agent now has full context and a ready-to-execute first-task plan.

## Decision Points
- **Step 3 necessity**: If the codebase is small (under ~20k lines) and Step 2 produced comprehensive coverage, Step 3 can be abbreviated to a focused convention-check rather than a full parallel sweep.
- **Step 4 scope**: If no first task has been assigned yet, replace Step 4 with a general `create_plan.md` pass that proposes 2–3 good starter tasks based on the open issue tracker and codebase health signals.
- **Step 5 depth**: Focus `general/code-explain.md` only on modules the new member explicitly flags as unfamiliar. Do not re-explain modules already well understood; use the time for the highest-uncertainty areas.
- **Agent vs. human**: For agent onboarding, Steps 1–3 are the critical load; Steps 4–5 are task-execution prep. For human onboarding, Step 1 carries additional weight (access provisioning, HR tasks) and Step 5 should include pairing session recommendations.

## Success Criteria
- New member or agent can accurately describe the system architecture, data flow, and key modules without referencing external documentation.
- `thoughts/shared/codebase-map.md` is committed and reflects the current state of the repo.
- First-task implementation plan is approved by `{{DEFAULT_REVIEWER}}` or a senior team member.
- New member can locate, run, and interpret the test suite without assistance.
- All flagged unfamiliar areas from Step 4 have been addressed in Step 5 explanations.
