---
chain_name: "Migration Lifecycle"
chain_id: migration-workflow
model: sonnet
type: workflow-chain
estimated_steps: 6
---

# Workflow: Migration Lifecycle

> Activate with: `/claude-code-bootstrap chain=migration-workflow`

## When to Use
Use this workflow when upgrading or replacing a framework, language runtime, third-party library, or database. It ensures the existing surface is understood before any code is touched, applies the migration systematically, and verifies correctness before shipping.

## Chain Overview
[research_codebase] → [general/code-migrate OR backend/code-migrate OR frontend/code-migrate] → [backend/db-migrate (if needed)] → [backend/test-harness] → [review/validate_plan] → [deploy-checklist]

## Steps

### Step 1: Research Codebase
- **Template**: `research_codebase.md`
- **Purpose**: Catalog every call site, dependency, and integration point that the migration will affect, producing a full blast-radius map before a single line changes.
- **Input**: Migration goal (e.g., "upgrade from React 17 to 19", "move from MySQL 5.7 to PostgreSQL 15"), repo root path.
- **Output**: Scoped codebase map — affected files, import counts, deprecated API usages, coupled services, and estimated change volume.
- **Hand-off note**: Attach the full affected-file list, deprecated symbol inventory, and estimated PR size to Step 2.

### Step 2: Code Migration
- **Template**: `general/code-migrate.md` (cross-cutting or language-level) OR `backend/code-migrate.md` (server/API layer) OR `frontend/code-migrate.md` (UI layer)
- **Purpose**: Execute the migration transforms — update imports, replace deprecated APIs, adjust config files, and resolve breaking changes surfaced in Step 1.
- **Input**: Affected-file list and deprecated symbol inventory from Step 1, migration guide or changelog for the target version.
- **Output**: Transformed codebase on branch `{{BRANCH_PREFIX}}migrate/<migration-slug>` with all targeted files updated and build passing.
- **Hand-off note**: List of all changed files, any manual intervention points that could not be automated, and whether a schema change is required to Step 3.

### Step 3: Database Migration (conditional)
- **Template**: `backend/db-migrate.md`
- **Purpose**: Author, validate, and dry-run all schema migrations required by the migration (new columns, dropped tables, index changes, type casts).
- **Input**: Schema delta identified in Step 2, `{{RDS_ENDPOINT}}`, `{{MIGRATION_NAMING_CONVENTION}}`, current migration history.
- **Output**: Versioned migration files committed to the branch; `migrate up` and `migrate down` both execute without error on a copy of staging data.
- **Hand-off note**: Migration file paths, estimated migration duration, and rollback script to Step 4.
- **Skip condition**: Skip this step entirely if the migration involves no database schema changes.

### Step 4: Test Harness
- **Template**: `backend/test-harness.md`
- **Purpose**: Run the existing test suite against the migrated codebase and fill any gaps where migration-related behavior is not yet covered.
- **Input**: Changed file list from Step 2, migration files from Step 3 (if applicable), existing test suite.
- **Output**: Full test suite green against the migrated code; new tests covering any migration-specific paths (e.g., data type coercions, API response shape changes).
- **Hand-off note**: Test results, coverage delta, and any tests disabled or skipped during migration to Step 5.

### Step 5: Validate Plan
- **Template**: `review/validate_plan.md`
- **Purpose**: Verify that all migration goals are achieved, no previously passing tests have regressed, and the migration is reversible.
- **Input**: Original migration goal, changed-file list, test results from Step 4, db migration rollback script from Step 3.
- **Output**: Validation report — migration completeness score, regression count, rollback viability assessment.
- **Hand-off note**: Validation report and any outstanding manual steps to Step 6.

### Step 6: Deploy Checklist
- **Template**: `deploy-checklist.md`
- **Purpose**: Sequence the deployment safely — especially critical for migrations that require coordinated schema changes, feature-flag gating, or dual-write periods.
- **Input**: Validation report from Step 5, db migration rollback script, infra vars (`{{CLOUD_REGION}}`, `{{ECS_CLUSTER}}`, `{{RDS_ENDPOINT}}`), `{{DEPLOY_STRATEGY}}`, `{{ROLLBACK_STRATEGY}}`.
- **Output**: Ordered deployment runbook including pre-deploy checks, migration execution order, smoke-test gate, and rollback trigger conditions.
- **Hand-off note**: None — workflow complete after deployment runbook is signed off and migration is live.

## Decision Points
- **Step 2 template choice**: Use `general/code-migrate.md` for language upgrades or cross-layer changes. Use `backend/code-migrate.md` for changes confined to API/service code. Use `frontend/code-migrate.md` for changes confined to UI code. Use both backend and frontend variants (run in parallel) for full-stack migrations.
- **Step 3 skip**: Skip `backend/db-migrate.md` if no schema changes are needed (pure code migration).
- **Step 4 → Step 5**: If more than 5% of tests fail after migration, pause and resolve before proceeding to validation.
- **Step 6 deploy strategy**: If `{{DEPLOY_STRATEGY}}` is `blue-green`, the db migration must be backward-compatible with the old code during the cutover window. Document any incompatibilities explicitly.

## Success Criteria
- Build and all tests pass on the migrated branch with zero regressions.
- All deprecated symbols identified in Step 1 have been replaced or explicitly deferred with tracked tech-debt tickets.
- Database migrations (if applicable) run successfully in both directions on staging data.
- Validation report shows migration completeness at 100% of scoped files.
- Deploy checklist signed off with rollback plan confirmed viable.
