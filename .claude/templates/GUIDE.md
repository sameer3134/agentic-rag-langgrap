# Claude Templates — Developer Guide

> Stack: **FastAPI · React · Next.js · PostgreSQL**
> Run `/claude-code-bootstrap` to hydrate these templates into active commands for your project.

---

## How It Works

```
templates/        ← Universal templates (placeholders like {{BE_FRAMEWORK}})
commands/
  init.md         ← Entry point — always present, run this first
  backend/        ← Populated by /claude-code-bootstrap
  frontend/
  cloud/
  general/
  review/
  chains/
```

**Setup order — always run in this sequence:**

```
1. /graphify    → builds graphify-out/GRAPH_REPORT.md + graph.json (importance scores, communities)
2. /claude-code-bootstrap        → reads Graphify output, hydrates all templates with real importance scores + project values
```

`/claude-code-bootstrap` requires Graphify output to inject node importance into every template's `{{GRAPH_IMPORTANCE_LOGIC}}` slot. Running `/claude-code-bootstrap` first leaves those as placeholders.

**`/claude-code-bootstrap` generates these files:**

| File | Purpose |
|---|---|
| `CLAUDE.md` | Project context loaded every session — stack, paths, commands |
| `.claudeignore` | Stops Claude reading node_modules, dist, .venv, .env, etc. |

**Graphify generates these files (persist across sessions):**

| File | Purpose |
|---|---|
| `graphify-out/GRAPH_REPORT.md` | Plain-language knowledge graph — node importance, communities, cross-file relationships |
| `graphify-out/graph.json` | Persistent graph for precise node/edge lookups |

`/general:onboard` and `/general:research_codebase` read `GRAPH_REPORT.md` automatically — no re-crawling needed.

**Invocation syntax after `/claude-code-bootstrap`:**
```
/claude-code-bootstrap                        → always works (flat, pre-exists)
/backend:api-scaffold        → after /claude-code-bootstrap
/chains:bugfix-workflow      → after /claude-code-bootstrap
/general:create_plan         → after /claude-code-bootstrap
/review:pr-enhance           → after /claude-code-bootstrap
```

---

## Quick Reference

### When to use what

| Situation | Use |
|---|---|
| Starting a new feature | `chains/feature-workflow` |
| Investigating a bug | `general/debug` or `general/smart-debug` |
| Writing a PR | `review/pr-enhance` + `review/validate_plan` |
| Setting up tests | `backend/test-harness` + `frontend/ui-testing` |
| Security audit | `chains/security-workflow` |
| New team member joining | `chains/onboarding-workflow` |
| Migrating code/DB | `chains/migration-workflow` |
| Reviewing a colleague's PR | `review/multi-agent-review` |

---

## Backend/ — FastAPI, PostgreSQL, Python

| File | What it does | When to use |
|---|---|---|
| `api-scaffold` | Generates routers, Pydantic models, auth middleware, OpenAPI docs | Building a new API endpoint from scratch |
| `api-mock` | Creates a mock FastAPI server mimicking real endpoints | Frontend needs API before backend is ready |
| `config-validate` | Validates `.env`, Pydantic `Settings`, secrets handling | Before deploy or when env bugs appear |
| `data-validation` | Builds Pydantic validation layer — cross-field rules, async validators | Adding complex input validation |
| `db-migrate` | Generates Alembic migrations — zero-downtime, reversible, data backfills | Any DB schema change |
| `debug-trace` | VS Code debugger configs, structured logging, request tracing middleware | Setting up a debugging session |
| `doc-generate` | OpenAPI enhancement, SDK docs, Postman collections | After building an API |
| `error-trace` | Sentry setup, error grouping, circuit breakers, retry strategies | Adding error monitoring |
| `security-scan` | OWASP scan — SQL injection, broken auth, hardcoded secrets, JWT issues | Before any release |
| `test-harness` | Full pytest suite — fixtures, unit/integration/e2e, async FastAPI tests | Setting up or expanding tests |
| `code-migrate` | Language/API/DB migrations — Python 2→3, REST→GraphQL, DB swaps | Migrating existing backend code |

---

## Frontend/ — Next.js, React, TypeScript, Tailwind

| File | What it does | When to use |
|---|---|---|
| `component-scaffold` | Full React component — TypeScript, Tailwind, Zustand, test file, Storybook | Building any new UI component |
| `state-management` | Zustand store design, TanStack Query for API caching, optimistic updates | Designing state architecture |
| `form-validation` | Zod schemas, FastAPI error mapping, multi-step forms, file uploads | Building any form |
| `ui-testing` | Jest + RTL — component→integration→E2E pyramid, visual regression | Setting up frontend tests |
| `test-harness` | Frontend test suite config, async/loading states, mock strategies | Expanding test coverage |
| `accessibility-audit` | WCAG audit — axe-core, keyboard nav, ARIA, screen reader testing | Before any public-facing release |
| `performance-audit` | Core Web Vitals, bundle analysis, lazy loading, memory leaks, Lighthouse | Investigating page slowness |
| `responsive-design` | Breakpoints, fluid typography, dark mode, touch targets, print styles | Making pages responsive |
| `design-system` | Token system, atomic components, theme switching, Storybook docs | Building a shared component library |
| `security-scan` | XSS, CSRF, DOM injection, CSP headers, sanitization | Before any public-facing release |
| `code-migrate` | App Router migration, React class→hooks, deprecated API updates | Upgrading Next.js or React |

---

## Cloud/ — Docker, GitHub Actions, K8s, Monitoring

| File | What it does | When to use |
|---|---|---|
| `docker-optimize` | Multi-stage builds, layer caching, image size, non-root user, Compose | Optimizing Docker images |
| `deploy-checklist` | Pre-deploy checklist — env vars, DB migration status, rollback plan | Before every production deploy |
| `monitor-setup` | Prometheus + Grafana — metrics, alerts, SLI dashboards, log aggregation | Setting up observability |
| `error-trace` | PagerDuty/Slack alerting, error budgets, Grafana error dashboard | Cloud-side error monitoring |
| `debug-trace` | OpenTelemetry, Jaeger tracing, container remote debug, prod safe-debug | Debugging distributed systems |
| `test-harness` | GitHub Actions CI — matrix builds, parallel jobs, coverage gates | Setting up CI pipelines |
| `k8s-manifest` | K8s Deployments, Services, Ingress, HPA, security contexts, Helm | Deploying to Kubernetes |
| `security-scan` | Checkov IaC scan, Trivy container CVEs, K8s Pod Security Standards | Auditing infrastructure |

---

## Review/ — Code Quality Gates

| File | What it does | When to use |
|---|---|---|
| `pr-enhance` | Generates PR description — summary, risk level, test plan, rollback steps | Before opening any PR |
| `validate_plan` | Checks built code against original plan's success criteria | After implementing a plan |
| `deps-audit` | CVE scan on `requirements.txt` + `package.json`, license checks | Weekly or before release |
| `security-scan` | Orchestrates all 3 domain scans → unified executive report | Full security audit |
| `multi-agent-review` | Parallel specialist reviewers — security, architecture, performance | Deep code review |
| `ai-review` | AI/ML-specific review — reproducibility, data leakage, prompt injection | If using AI features |
| `compliance-check` | GDPR, HIPAA, SOC2 audit — PII handling, encryption, audit logs | Compliance milestone |

---

## General/ — Planning, Git, Debug, Docs

| File | What it does | When to use |
|---|---|---|
| `create_plan` | Interactive implementation planning — researches codebase, asks questions, writes phased plan | Starting any non-trivial task |
| `implement_plan` | Executes a plan file phase by phase, checks success criteria | After `create_plan` is approved |
| `iterate_plan` | Refines an existing plan based on feedback | When plan needs adjustment |
| `onboard` | Gets Claude context-loaded on your project | Start of every new session |
| `research_codebase` | Deep-dives codebase and writes a historical reference document | Understanding unfamiliar code |
| `debug` | Reads logs, git history, DB state → finds root cause | Investigating any bug |
| `smart-debug` | Spawns parallel specialist agents to attack a bug from multiple angles | Complex or elusive bugs |
| `error-analysis` | Clusters error patterns across logs, identifies root causes | Analyzing production errors |
| `debug-trace` | Performance profiling, debug configs per env, IDE integration | Setting up debug environment |
| `issue` | Reads a GitHub issue, finds the code, implements a fix, writes tests | Fixing GitHub issues |
| `commit` | Groups changes, drafts commit message, asks confirmation | After completing work |
| `describe_pr` | PR description following your repo template | Opening a PR |
| `create_handoff` | Writes a handoff doc so next session picks up exactly here | End of a long session |
| `code-explain` | Explains any code — flow diagrams, step-by-step, decisions, analogies | Understanding unfamiliar code |
| `code-migrate` | Planning/rollback/automation layer for migrations | Orchestrating any migration |
| `deps-upgrade` | Plans safe dependency upgrades, detects breaking changes | Upgrading packages |
| `refactor-clean` | SOLID principles, removes duplication, improves naming | Code cleanup |
| `tech-debt` | Identifies, categorizes, and prioritizes tech debt | Tech debt sprint planning |
| `doc-generate` | Architecture diagrams, ADRs, code docs, user guides | Writing documentation |
| `linear` | Full Linear ticket lifecycle — create, update, link PRs | Ticket management |
| `test-harness` | Shared test fixtures and cross-domain test orchestration | Shared test infrastructure |

---

## Chains/ — Full Workflow Playbooks

Chains wire multiple templates into an ordered workflow. Run `/claude-code-bootstrap chain=<id>` to generate a `WORKFLOW.md` playbook.

| Chain | Steps | Use when |
|---|---|---|
| `feature-workflow` | onboard → research → plan → implement → test → validate → PR → deploy | Building any new feature |
| `bugfix-workflow` | debug → smart-debug → fix → test → validate → PR | Fixing a bug end-to-end |
| `migration-workflow` | research → migrate → db-migrate → test → validate → deploy | Any code or DB migration |
| `security-workflow` | backend scan → frontend scan → cloud scan → compliance → deps → deploy | Full security audit |
| `onboarding-workflow` | onboard → research codebase → plan first task | New dev or new session |

---

## Graphify Integration

Every template contains:
```
## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> If this module is a 'Core Node', apply 2x stricter linting and testing rules.
```

When Graphify analyses your project graph, it injects importance scores here. Core Nodes (high-centrality files) get automatically flagged for stricter standards.

---

## Placeholder Reference

All `{{TOKENS}}` are filled by `/claude-code-bootstrap`. Key ones for this stack:

| Token | Value after hydration |
|---|---|
| `{{BE_FRAMEWORK}}` | FastAPI |
| `{{FE_FRAMEWORK}}` | Next.js 14 (React 18) |
| `{{DB_TYPE}}` | PostgreSQL |
| `{{BE_TEST_COMMAND}}` | `pytest tests/ -v --cov=app` |
| `{{FE_TEST_COMMAND}}` | `npm test -- --coverage` |
| `{{BE_MIGRATE_COMMAND}}` | `alembic upgrade head` |
| `{{BE_PATH_API}}` | `backend/app/api/` |
| `{{FE_PATH_COMPONENTS}}` | `frontend/src/components/` |
| `{{CLOUD_CI_TOOL}}` | GitHub Actions |
