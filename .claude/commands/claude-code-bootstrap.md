---
description: Initialize project by reading templates/ and hydrating commands/ with project-specific values
complexity: advanced
priority: critical
tags: [scaffold, config, planning, ci]
version: 1.0.0
---

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Self-Hydrating Project Initializer

You are the Architect Agent responsible for bootstrapping a new project by reading Universal Templates and hydrating them with project-specific values.

## Purpose
Read template files from `.claude/templates/`, resolve all `{{PLACEHOLDER}}` tokens with actual project values, and write the hydrated commands to `.claude/commands/`.

## Recommended Order

```
/graphify          # Run first — generates graphify-out/GRAPH_REPORT.md + graph.json
/claude-code-bootstrap              # Run second — reads Graphify output to inject importance scores
```

`/claude-code-bootstrap` requires Graphify output to fully populate `{{GRAPH_IMPORTANCE_LOGIC}}` in every template. If you run `/claude-code-bootstrap` without Graphify, importance scores are left as placeholders and Core Node detection is skipped.

## Invocation Modes

```
/claude-code-bootstrap                          # Full auto-detect + interactive
/claude-code-bootstrap chain=feature-workflow   # Generate a workflow playbook only
```

## Process

### Step 0: Profile & Chain Resolution (if flags provided)

**If `chain=` flag is set:**
1. Read `.claude/templates/chains/<chain-id>.md`
2. Generate a `WORKFLOW.md` at project root listing each step, its template, and hand-off notes
3. Continue with normal hydration so the workflow's templates are available

---

### Step 0.5: New Repo Detection

Before running full detection, check whether this is a new or empty repository.

**Signal: repo is new/empty if ALL of the following are true:**
- No framework config files exist (`package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, `pom.xml`, `Cargo.toml`, `composer.json`)
- No source directories exist (`src/`, `app/`, `lib/`, `backend/`, `frontend/`, `api/`, `server/`)
- No CI config exists (`.github/`, `.circleci/`, `.gitlab-ci.yml`)
- No Dockerfile or `docker-compose.yml`

**If repo is new/empty → stop immediately and tell the developer:**

```
⚠ This repo has no code yet.

Set up your project first:
  - Scaffold your framework (e.g. npm create vite, django-admin startproject, go mod init)
  - Add at least a basic directory structure and dependency file

Then re-run /claude-code-bootstrap — it will auto-detect your stack and generate
the full tailored command set.
```

Do not generate any commands, do not create CLAUDE.md, do not ask any questions. Exit.

**If the repo has existing source files → continue to Step 1 (auto-detect from codebase).**

---

### Step 1: Project Detection

Scan the repository to auto-detect:

```
Project Type:        (monorepo | backend-only | frontend-only | fullstack)
Backend Framework:   {{BE_FRAMEWORK}}      → e.g., FastAPI, Express, Django
Frontend Framework:  {{FE_FRAMEWORK}}       → e.g., React, Vue, Angular
Database:            {{DB_TYPE}}            → e.g., PostgreSQL, MongoDB
Language(s):         {{LANGUAGE}}           → e.g., Python, TypeScript, Go
Cloud Provider:      {{CLOUD_PROVIDER}}     → e.g., AWS, GCP, Azure
Container Tool:      {{CLOUD_CONTAINER_TOOL}} → e.g., Docker
Orchestrator:        {{CLOUD_ORCHESTRATOR}} → e.g., Kubernetes
CI/CD Tool:          {{CLOUD_CI_TOOL}}      → e.g., GitHub Actions
Ticket Tool:         {{TICKET_TOOL}}        → e.g., Linear, Jira
```

Derive `skip_if` conditions from detection results:
- No Dockerfile found → add `no_docker`
- No `k8s/` or `kubernetes/` → add `no_k8s`
- No frontend source detected → add `no_frontend`
- No backend source detected → add `no_backend`
- No database config found → add `no_db`
- No CI config found → add `no_ci`
- No cloud provider detected → add `no_cloud`
- No test files found → add `no_tests`

### Step 2: Path Discovery

Map the project's actual directory layout to path placeholders:

| Placeholder | How to detect | Example |
|---|---|---|
| `{{BE_PATH_API}}` | Look for `routes/`, `api/`, `src/api` | `src/api` |
| `{{BE_PATH_MODELS}}` | Look for `models/`, `app/models` | `app/models` |
| `{{BE_PATH_MIGRATIONS}}` | Look for `migrations/`, `alembic/` | `migrations/` |
| `{{BE_PATH_TESTS}}` | Look for `tests/`, `test/`, `spec/` | `tests/` |
| `{{BE_PATH_SRC}}` | Root source directory | `src/` |
| `{{BE_PATH_PIPELINES}}` | Look for `pipelines/`, `etl/` | `src/pipelines` |
| `{{BE_PATH_CONFIG}}` | Look for `config/`, `settings/` | `config/` |
| `{{FE_PATH_COMPONENTS}}` | Look for `components/`, `src/components` | `src/components` |
| `{{FE_PATH_PAGES}}` | Look for `pages/`, `src/pages`, `app/` | `src/pages` |
| `{{FE_PATH_SRC}}` | Frontend source root | `src/` |
| `{{FE_PATH_TESTS}}` | Look for `__tests__/`, `test/` | `__tests__/` |
| `{{PATH_TESTS}}` | Generic test directory | `tests/` |
| `{{PATH_SRC}}` | Generic source directory | `src/` |
| `{{CLOUD_PATH_DOCKERFILE}}` | Look for `Dockerfile` | `Dockerfile` |
| `{{CLOUD_PATH_COMPOSE}}` | Look for `docker-compose.yml` | `docker-compose.yml` |
| `{{CLOUD_PATH_K8S}}` | Look for `k8s/`, `kubernetes/` | `k8s/` |
| `{{CLOUD_PATH_CI}}` | Look for `.github/workflows/`, `.circleci/` | `.github/workflows/` |
| `{{CLOUD_PATH_IAC}}` | Look for `terraform/`, `infra/` | `terraform/` |

### Step 3: Command Discovery

Detect the actual commands by inspecting `package.json`, `Makefile`, `pyproject.toml`, `go.mod`, etc.:

| Placeholder | Detection Strategy |
|---|---|
| `{{BE_TEST_COMMAND}}` | `package.json` scripts.test, `Makefile` test target, `pytest` in pyproject |
| `{{BE_LINT_COMMAND}}` | `package.json` scripts.lint, `Makefile` lint target |
| `{{BE_BUILD_COMMAND}}` | `package.json` scripts.build, `Makefile` build target |
| `{{BE_START_COMMAND}}` | `package.json` scripts.start or scripts.dev |
| `{{BE_MIGRATE_COMMAND}}` | `Makefile` migrate target, `alembic` commands |
| `{{FE_TEST_COMMAND}}` | Frontend `package.json` scripts.test |
| `{{FE_LINT_COMMAND}}` | Frontend `package.json` scripts.lint |
| `{{FE_BUILD_COMMAND}}` | Frontend `package.json` scripts.build |
| `{{FE_START_COMMAND}}` | Frontend `package.json` scripts.dev or scripts.start |
| `{{TEST_COMMAND}}` | Fallback to whichever test command is found |
| `{{LINT_COMMAND}}` | Fallback to whichever lint command is found |
| `{{BUILD_COMMAND}}` | Fallback to whichever build command is found |
| `{{CHECK_COMMAND}}` | `Makefile` check target |
| `{{TYPECHECK_COMMAND}}` | `package.json` scripts.typecheck |
| `{{FORMAT_COMMAND}}` | `package.json` scripts.fmt or scripts.format |
| `{{SYNC_COMMAND}}` | Project-specific sync command if any |
| `{{CLOUD_BUILD_COMMAND}}` | `docker build` or equivalent |
| `{{CLOUD_DEPLOY_COMMAND}}` | `kubectl apply` or CI deploy step |

### Step 4: Category Filtering & Priority Sorting

**STRICT folder inclusion** — only process folders listed for the detected project type. Do NOT create commands or subdirectories for any folder not in the list.

| Project Type | Folders to Process |
|---|---|
| backend-only | `backend/`, `general/`, `review/`, `chains/` |
| frontend-only | `frontend/`, `general/`, `review/`, `chains/` |
| fullstack | `backend/`, `frontend/`, `general/`, `review/`, `chains/` |
| monorepo | `backend/`, `frontend/`, `cloud/`, `general/`, `review/`, `chains/` |

**Detection signals for project type — follow this decision tree in order:**

1. Check for monorepo first: if `packages/`, `apps/`, or `services/` directories exist containing multiple independent sub-projects → `monorepo`
2. Check for frontend framework: look for `next.config.*`, `vite.config.*`, `nuxt.config.*`, `svelte.config.*`, `remix.config.*`, `astro.config.*`, `angular.json`, OR a root `package.json` with React/Vue/Angular/Svelte/Next/Nuxt as a dependency
3. Check for a **separate** backend service: look for a dedicated backend directory (`backend/`, `api/`, `server/`) that has its OWN dependency file (`requirements.txt`, `pyproject.toml`, `go.mod`, `pom.xml`, `Cargo.toml`) OR a root-level `pyproject.toml` / `go.mod` / `pom.xml` with NO frontend config alongside it

**CRITICAL — frontend-only vs fullstack rule:**
- If frontend framework IS detected AND there is NO separate backend directory with its own dependency file → `frontend-only`
- This means: Next.js, Nuxt, SvelteKit, Remix, Astro apps with `app/api/` or `pages/api/` routes are **`frontend-only`** — those API routes are part of the frontend framework, not a separate backend
- Only classify as `fullstack` if there is a genuinely independent backend service that can run on its own (e.g., `backend/` folder with `requirements.txt`, a separate `api/` Go service, a Django app in a sibling directory)

| Signal | Project Type |
|---|---|
| Multiple packages/ or apps/ with mixed stacks | `monorepo` |
| Frontend config + separate backend dir with own deps | `fullstack` |
| Frontend config only (including Next.js/Nuxt/SvelteKit with API routes) | `frontend-only` |
| Server-side code only (Python/Go/Java/Node), no frontend config | `backend-only` |

**Cloud folder rule:**
- Include `cloud/` ONLY if at least one of these exists: `Dockerfile`, `docker-compose.yml`, `k8s/`, `kubernetes/`, `terraform/`, `.github/workflows/`, `.circleci/`
- If none exist → SKIP `cloud/` entirely, even for monorepo
- Override: if project type is `backend-only` or `frontend-only` and cloud infra IS detected → include `cloud/` in addition to the base set

`chains/` is always included — it provides runnable workflow commands (`/bugfix-workflow`, `/feature-workflow`, etc.) regardless of project type.

**Template filtering within folders:**
For each template file, read its frontmatter and:
1. Check `skip_if` — if any condition matches the project's `skip_if` set, exclude this template
2. Read `priority` — load `critical` and `high` templates first
3. Read `depends_on` — ensure dependencies are hydrated before dependents
4. Read `complexity` — warn user if `advanced` templates are loaded for a `basic` project setup

**Dependency ordering:**
Sort templates so `depends_on` references are always hydrated before the dependent template. Build a DAG from `depends_on` / `chains_to` relationships and process in topological order.

### Step 5: Hydration

For each template in the selected folders:

1. Read the template file from `.claude/templates/<category>/<name>.md`
2. Replace ALL `{{PLACEHOLDER}}` tokens with the detected values
3. Remove the `## Graphify Context` section (or leave it for Graphify to process later)
4. Write the hydrated file to `.claude/commands/<category>/<name>.md` — preserve the folder structure to avoid name collisions (e.g. `security-scan.md` exists in backend/, frontend/, cloud/, review/)

**Invocation after hydration:**
```
/backend:api-scaffold         → .claude/commands/backend/api-scaffold.md
/chains:bugfix-workflow       → .claude/commands/chains/bugfix-workflow.md
/general:create_plan          → .claude/commands/general/create_plan.md
/review:pr-enhance            → .claude/commands/review/pr-enhance.md
```

`init.md` itself stays flat at `.claude/commands/claude-code-bootstrap.md` so `/claude-code-bootstrap` always works before hydration.

### Step 6: Graphify Integration

Read `graphify-out/GRAPH_REPORT.md` and `graphify-out/graph.json` — these must exist before `/claude-code-bootstrap` runs.

For each template containing `{{GRAPH_IMPORTANCE_LOGIC}}`:
1. Look up the corresponding source file(s) in `graph.json` by matching file path to node labels
2. Extract the node's importance score and community classification
3. Replace `{{GRAPH_IMPORTANCE_LOGIC}}` with:
   ```
   > Node importance: {{SCORE}} | Community: {{COMMUNITY_LABEL}} | Classification: {{CORE|PERIPHERAL}}
   > If classification is 'Core Node': apply 2x stricter linting and testing rules.
   ```
4. If a file has no match in the graph (e.g. newly added), replace with:
   ```
   > Node importance: unscored — run /graphify --update to include this file
   ```

**If `graphify-out/GRAPH_REPORT.md` does not exist** — stop and warn:
```
⚠ Graphify output not found. Run /graphify before /claude-code-bootstrap to enable importance scoring.
Continuing without importance scores — {{GRAPH_IMPORTANCE_LOGIC}} will be left as placeholders.
```

### Step 7: .claudeignore Generation

Check if `.claudeignore` exists at project root:

**If it does NOT exist** — create it:
```
# Dependencies
node_modules/
.pnp/
.pnp.js

# Build outputs
dist/
build/
.next/
out/
__pycache__/
*.pyc
*.pyo
.eggs/
*.egg-info/
htmlcov/
.coverage

# Virtual environments
.venv/
venv/
env/

# IDE & OS
.idea/
.vscode/
*.DS_Store
Thumbs.db

# Logs & temp
*.log
logs/
tmp/
temp/

# Test artifacts
.pytest_cache/
coverage/
.nyc_output/

# Secrets
.env
.env.*
*.pem
*.key
```

**If it already exists** — leave it untouched. Never overwrite a developer's custom `.claudeignore`.

### Step 8: CLAUDE.md Sync

Check if `CLAUDE.md` exists in the project root:

**If it does NOT exist** — create it:
```markdown
# Project Context

## Stack
- Backend: {{BE_FRAMEWORK}} ({{BE_LANGUAGE}})
- Frontend: {{FE_FRAMEWORK}}
- Database: {{DB_TYPE}}
- CI/CD: {{CLOUD_CI_TOOL}}

## Key Paths
- API routes: `{{BE_PATH_API}}`
- Models: `{{BE_PATH_MODELS}}`
- Migrations: `{{BE_PATH_MIGRATIONS}}`
- Backend tests: `{{BE_PATH_TESTS}}`
- Components: `{{FE_PATH_COMPONENTS}}`
- Pages: `{{FE_PATH_PAGES}}`

## Commands
- Test (backend): `{{BE_TEST_COMMAND}}`
- Test (frontend): `{{FE_TEST_COMMAND}}`
- Lint: `{{LINT_COMMAND}}`
- Typecheck: `{{TYPECHECK_COMMAND}}`
- Migrate: `{{BE_MIGRATE_COMMAND}}`
- Dev server: `{{FE_START_COMMAND}}`

## Claude Commands
Run `/claude-code-bootstrap` to regenerate commands. After init, use `/backend:api-scaffold`, `/chains:bugfix-workflow`, etc.
```

**If it already exists** — read it first, then only update the sections above if the detected values differ. Preserve any custom sections the developer has added below the generated blocks. Never overwrite content that isn't part of the auto-generated sections.

### Graphify Note

If `graphify-out/GRAPH_REPORT.md` exists, mention it to the developer:
```
Graphify output detected at graphify-out/GRAPH_REPORT.md.
/general:onboard and /general:research_codebase will read it automatically for richer context.
```

If it does not exist, suggest running `/graphify` after `/claude-code-bootstrap` to generate the knowledge graph — it replaces basic directory crawling with a full node/edge graph including community detection and importance scores.

### Step 9: Verification

After hydration, verify:
- [ ] No remaining `{{...}}` placeholders in `.claude/commands/`
- [ ] All commands are valid markdown with proper frontmatter
- [ ] Template category matches project capabilities
- [ ] Commands reference paths that actually exist in the project
- [ ] `CLAUDE.md` exists at project root with correct values
- [ ] `.claudeignore` exists at project root
- [ ] If `graphify-out/GRAPH_REPORT.md` exists, confirm it was detected and noted

### Step 10: Cleanup

Only run this step if Step 9 verification passed with zero failures.

1. Delete the entire `.claude/templates/` directory — it is no longer needed; the hydrated commands in `.claude/commands/` are the live artifacts.

   ```bash
   rm -rf .claude/templates
   ```

2. Confirm deletion succeeded and report to the developer:

   ```
   ✓ .claude/templates/ removed — hydrated commands are in .claude/commands/
   ```

3. If re-initialization is ever needed (e.g., you add Docker, switch frameworks), run:

   ```bash
   npx claude-bootstrap --templates-only
   /claude-code-bootstrap
   ```

**If verification failed:** do NOT delete templates. Leave them in place so the developer can inspect and re-run `/claude-code-bootstrap --force` after fixing the issues.

## Placeholder Registry

### Backend Placeholders
| Key | Description |
|---|---|
| `{{BE_FRAMEWORK}}` | Backend framework (FastAPI, Express, Django, etc.) |
| `{{BE_LANGUAGE}}` | Backend primary language |
| `{{BE_RUNTIME}}` | Runtime environment (Node.js, Deno, Bun) |
| `{{BE_TEST_FRAMEWORK}}` | Test framework name (pytest, Jest, JUnit) |
| `{{BE_TEST_COMMAND}}` | Command to run backend tests |
| `{{BE_LINT_COMMAND}}` | Command to run backend linter |
| `{{BE_BUILD_COMMAND}}` | Command to build backend |
| `{{BE_START_COMMAND}}` | Command to start backend server |
| `{{BE_MIGRATE_COMMAND}}` | Command to run DB migrations |
| `{{BE_PIPELINE_COMMAND}}` | Command to run data pipelines |
| `{{BE_PIPELINE_FRAMEWORK}}` | Pipeline framework (Airflow, Beam, Spark) |
| `{{BE_MIGRATION_TOOL}}` | Migration tool (Alembic, Flyway) |
| `{{BE_MOCK_TOOL}}` | API mocking tool |
| `{{BE_AI_FRAMEWORK}}` | AI framework (LangChain, LangGraph) |
| `{{BE_MODULE}}` | Backend module name |
| `{{BE_PATH_API}}` | Path to API routes |
| `{{BE_PATH_MODELS}}` | Path to data models |
| `{{BE_PATH_MIGRATIONS}}` | Path to migrations |
| `{{BE_PATH_TESTS}}` | Path to backend tests |
| `{{BE_PATH_SRC}}` | Backend source root |
| `{{BE_PATH_PIPELINES}}` | Path to data pipelines |
| `{{BE_PATH_DAGS}}` | Path to DAG definitions |
| `{{BE_PATH_CONFIG}}` | Path to backend config |
| `{{BE_PATH_MOCKS}}` | Path to mock files |
| `{{BE_PATH_ROUTES}}` | Path to route definitions |
| `{{BE_PATH_SCHEMAS}}` | Path to schema definitions |

### Frontend Placeholders
| Key | Description |
|---|---|
| `{{FE_FRAMEWORK}}` | Frontend framework (React, Vue, Angular) |
| `{{FE_LANGUAGE}}` | Frontend language (TypeScript, JavaScript) |
| `{{FE_RUNTIME}}` | Frontend runtime |
| `{{FE_STYLE_SYSTEM}}` | Styling approach (Tailwind, CSS Modules) |
| `{{FE_STATE_MANAGER}}` | State management (Redux, Zustand, Pinia) |
| `{{FE_TEST_FRAMEWORK}}` | Frontend test framework |
| `{{FE_TEST_COMMAND}}` | Command to run frontend tests |
| `{{FE_LINT_COMMAND}}` | Frontend lint command |
| `{{FE_BUILD_COMMAND}}` | Frontend build command |
| `{{FE_START_COMMAND}}` | Frontend dev server command |
| `{{FE_BUNDLER}}` | Build tool (Vite, Webpack, esbuild) |
| `{{FE_A11Y_TOOL}}` | Accessibility testing tool |
| `{{FE_RUNNER}}` | Package runner (npx, yarn, pnpm) |
| `{{FE_BROWSER}}` | Target browser |
| `{{FE_MODULE}}` | Frontend module name |
| `{{FE_PATH_COMPONENTS}}` | Path to components |
| `{{FE_PATH_PAGES}}` | Path to pages |
| `{{FE_PATH_STYLES}}` | Path to styles |
| `{{FE_PATH_HOOKS}}` | Path to hooks |
| `{{FE_PATH_UTILS}}` | Path to utilities |
| `{{FE_PATH_SRC}}` | Frontend source root |
| `{{FE_PATH_TESTS}}` | Frontend test directory |
| `{{FE_PATH_ASSETS}}` | Path to static assets |

### Cloud Placeholders
| Key | Description |
|---|---|
| `{{CLOUD_PROVIDER}}` | Cloud provider (AWS, GCP, Azure) |
| `{{CLOUD_CONTAINER_TOOL}}` | Container runtime (Docker, Podman) |
| `{{CLOUD_ORCHESTRATOR}}` | Orchestrator (Kubernetes) |
| `{{CLOUD_IAC_TOOL}}` | Infrastructure as Code tool |
| `{{CLOUD_CI_TOOL}}` | CI/CD platform |
| `{{CLOUD_CD_TOOL}}` | CD tool (ArgoCD, Flux) |
| `{{CLOUD_MONITORING_TOOL}}` | Monitoring platform (Prometheus, Datadog) |
| `{{CLOUD_ERROR_TRACKER}}` | Error tracking (Sentry, Rollbar) |
| `{{CLOUD_LOG_STACK}}` | Log aggregation stack |
| `{{CLOUD_TRACING_TOOL}}` | Distributed tracing tool |
| `{{CLOUD_ALERTING_TOOL}}` | Alerting platform |
| `{{CLOUD_INGRESS}}` | Ingress controller / reverse proxy |
| `{{CLOUD_BASE_IMAGE}}` | Container base image |
| `{{CLOUD_REGISTRY}}` | Container registry |
| `{{CLOUD_K8S_SERVICE}}` | Managed K8s service |
| `{{CLOUD_OBJECT_STORAGE}}` | Object storage service |
| `{{CLOUD_DB_SERVICE}}` | Managed DB service |
| `{{CLOUD_SERVERLESS}}` | Serverless platform |
| `{{CLOUD_MESSAGING}}` | Message queue service |
| `{{CLOUD_DNS}}` | DNS service |
| `{{CLOUD_LOAD_BALANCER}}` | Load balancer |
| `{{CLOUD_NETWORK}}` | Virtual network |
| `{{CLOUD_IAM}}` | Identity & access management |
| `{{CLOUD_PACKAGE_MANAGER}}` | K8s package manager (Helm) |
| `{{CLOUD_BUILD_COMMAND}}` | Container build command |
| `{{CLOUD_RUN_COMMAND}}` | Container run command |
| `{{CLOUD_PUSH_COMMAND}}` | Registry push command |
| `{{CLOUD_DEPLOY_COMMAND}}` | Deployment command |
| `{{CLOUD_STATUS_COMMAND}}` | Status check command |
| `{{CLOUD_HELM_COMMAND}}` | Helm command |
| `{{CLOUD_IAC_COMMAND}}` | IaC command |
| `{{CLOUD_PATH_DOCKERFILE}}` | Path to Dockerfile |
| `{{CLOUD_PATH_COMPOSE}}` | Path to compose file |
| `{{CLOUD_PATH_K8S}}` | Path to K8s manifests |
| `{{CLOUD_PATH_CI}}` | Path to CI config |
| `{{CLOUD_PATH_IAC}}` | Path to IaC files |
| `{{CLOUD_PATH_MONITORING}}` | Path to monitoring config |
| `{{CLOUD_PATH_DEPLOY}}` | Path to deploy scripts |
| `{{CLOUD_PATH_HELM}}` | Path to Helm charts |
| `{{CLOUD_PATH_LOGS}}` | Path to log config |
| `{{CLOUD_PATH_CONFIG}}` | Path to cloud config |

### General Placeholders
| Key | Description |
|---|---|
| `{{LANGUAGE}}` | Primary project language |
| `{{DB_TYPE}}` | Database technology |
| `{{TEST_COMMAND}}` | Generic test command |
| `{{LINT_COMMAND}}` | Generic lint command |
| `{{BUILD_COMMAND}}` | Generic build command |
| `{{CHECK_COMMAND}}` | Generic check/verify command |
| `{{TYPECHECK_COMMAND}}` | Type checking command |
| `{{FORMAT_COMMAND}}` | Code formatting command |
| `{{MIGRATE_COMMAND}}` | Migration command |
| `{{SYNC_COMMAND}}` | Project sync command |
| `{{TICKET_TOOL}}` | Ticket management tool |
| `{{TICKET_CLI_COMMAND}}` | Ticket CLI command |
| `{{TICKET_ID}}` | Ticket ID format |
| `{{MONITORING_TOOL}}` | Error/performance monitoring |
| `{{TEST_FRAMEWORK}}` | Test framework name |
| `{{MIGRATION_TOOL}}` | DB migration tool name |
| `{{NOTES_TOOL}}` | Note-taking tool |
| `{{AI_MODEL}}` | AI model reference |
| `{{AI_FRAMEWORK}}` | AI framework |
| `{{NAMING_CONVENTION}}` | Code naming convention |
| `{{FILE_NAMING_CONVENTION}}` | File naming convention |
| `{{PROJECT_NAME}}` | Project name |
| `{{USER_NAME}}` | User/developer name |
| `{{PATH_TESTS}}` | Generic test path |
| `{{PATH_SRC}}` | Generic source path |
| `{{PATH_PLANS}}` | Planning documents path |
| `{{PATH_RESEARCH}}` | Research documents path |
| `{{PATH_TICKETS}}` | Ticket files path |
| `{{PATH_THOUGHTS}}` | Thoughts/notes directory |
| `{{PATH_CONFIG}}` | Config directory |
| `{{PATH_WUI}}` | Web UI module path |
| `{{PATH_DAEMON}}` | Daemon/service module path |
| `{{GRAPH_IMPORTANCE_LOGIC}}` | Graphify node importance score |

## Example Usage

```
/claude-code-bootstrap
```

The initializer will:
1. Scan the project structure
2. Auto-detect all values
3. Present detected values for confirmation
4. Hydrate all applicable templates
5. Report results with any unresolved placeholders
