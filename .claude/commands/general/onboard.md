---
model: claude-sonnet-4-0
complexity: intermediate
priority: high
tags: ["docs", "planning"]
depends_on: []
chains_to: ["general/research_codebase"]
skip_if: []
version: 1.0.0

---

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Onboard

You are given the following context:
$ARGUMENTS

## Instructions

"AI models are geniuses who start from scratch on every task." - Noam Brown

Your job is to "onboard" yourself to the current task.

## Step 1: Load cached context first

Before exploring anything, check for Graphify output and CLAUDE.md:

- **`graphify-out/GRAPH_REPORT.md`** — read it fully if present. This is a knowledge graph report with node importance, community clusters, and cross-file relationships. It tells you the architecture without crawling a single file. Skip any exploration it already covers.
- **`graphify-out/graph.json`** — available for precise node/edge lookups if you need to trace specific relationships.
- **`CLAUDE.md`** at project root — read if present. Contains stack, commands, and key paths in compact form.

If none of these exist, proceed to full exploration. Suggest running `/graphify` then `/claude-code-bootstrap` after the session to generate them for future use.

## Step 2: Explore what the cache doesn't cover

Do this by:

- Using ultrathink
- Exploring only the parts of the codebase not already covered by `.claude/context/codebase.md`
- Making use of any MCP tools at your disposal for planning and research
- Asking me questions if needed
- Using subagents for dividing work and separation of concerns

The goal is to get you fully prepared to start working on the task.

Take as long as you need to get yourself ready. Overdoing it is better than underdoing it.

Record everything in a .claude/tasks/[TASK_ID]/onboarding.md file. This file will be used to onboard you to the task in a new session if needed, so make sure it's comprehensive.
