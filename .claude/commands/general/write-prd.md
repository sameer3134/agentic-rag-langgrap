---
name: write-prd
description: Turn the grilling log and conversation context into a detailed PRD written to a local file. Use when user wants to create a PRD from the current context.
---

This skill produces a PRD. Do NOT interview the user — just synthesize what is already known.

If a grilling log `thoughts/grilling-{slug}.md` exists, read it first and treat it as the authoritative source: the PRD must inherit every resolved Q&A and its rationale. Fall back to conversation context only when no log exists.

Write **in detail** — every section gives concrete reasoning, not one-liners. When a decision traces back to a grilling-log answer, carry that reasoning into the PRD.

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already.

2. Sketch out the major modules you will need to build or modify to complete the implementation. Actively look for opportunities to extract deep modules that can be tested in isolation.

A deep module (as opposed to a shallow module) is one which encapsulates a lot of functionality in a simple, testable interface which rarely changes.

Check with the user that these modules match their expectations. Check with the user which modules they want tests written for.

3. Write the PRD to a local file `PRD-{slug}.md` using the template below. This local file is the only output and the source of truth for `/prd-to-issues`. Do NOT create a GitHub issue.

4. Once `PRD-{slug}.md` is written, confirm with the user that it captured everything from the grilling log.

<prd-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories. Each user story should be in the format of:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Dependencies & Sequencing

A description of the natural build order: which capabilities/modules must exist before others, and why. This seeds the dependency graph that `/prd-to-issues` turns into independently-shippable slices and the `depends_on` column of the CSV.

## Out of Scope

A description of the things that are out of scope for this PRD.

## Further Notes

Any further notes about the feature.

</prd-template>
