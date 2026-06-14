---
chain_name: "Full Security Audit"
chain_id: security-workflow
model: sonnet
type: workflow-chain
estimated_steps: 7
---

# Workflow: Full Security Audit

> Activate with: `/claude-code-bootstrap chain=security-workflow`

## When to Use
Use this workflow to perform a comprehensive security review across the entire stack — application code, infrastructure, cloud configuration, dependencies, and compliance posture. Run it before major releases, after security incidents, or on a scheduled cadence.

## Chain Overview
[review/security-scan] → [backend/security-scan] → [frontend/security-scan] → [cloud/security-scan] → [review/compliance-check] → [review/deps-audit] → [cloud/deploy-checklist]

## Steps

### Step 1: Security Scan (Orchestration)
- **Template**: `review/security-scan.md`
- **Purpose**: Establish the audit scope, assign severity thresholds, and run a top-level triage pass to identify the highest-risk areas before domain-specific scans begin.
- **Input**: Repo root path, previous audit report (if any), known sensitive data classifications, `{{ERROR_CODE_PREFIX}}` for internal error mapping.
- **Output**: Audit scope document — risk tiers, priority scan order, known exclusions, and severity-to-action matrix.
- **Hand-off note**: Pass the audit scope document and risk-tier assignments to Steps 2, 3, and 4 (these can run in parallel).

### Step 2: Backend Security Scan
- **Template**: `backend/security-scan.md`
- **Purpose**: Inspect server-side code for injection vulnerabilities, authentication/authorization flaws, insecure deserialization, secret leakage, and unsafe configurations.
- **Input**: Audit scope from Step 1, backend source directories, `{{SECRETS_MANAGER_PREFIX}}` for verifying secrets are not hardcoded.
- **Output**: Backend findings report — vulnerability list with severity, file location, line number, and recommended remediation.
- **Hand-off note**: Backend findings report (CRITICAL/HIGH items flagged) to Step 5.

### Step 3: Frontend Security Scan
- **Template**: `frontend/security-scan.md`
- **Purpose**: Inspect client-side code for XSS vectors, insecure storage of tokens, CSP violations, third-party script risks, and exposed API keys.
- **Input**: Audit scope from Step 1, frontend source directories, `{{CDN_URL}}` for CSP header validation.
- **Output**: Frontend findings report — vulnerability list with severity, component location, and recommended remediation.
- **Hand-off note**: Frontend findings report (CRITICAL/HIGH items flagged) to Step 5.

### Step 4: Cloud Security Scan
- **Template**: `cloud/security-scan.md`
- **Purpose**: Audit cloud infrastructure configuration — IAM policies, network exposure, S3 bucket permissions, security groups, encryption at rest and in transit, and logging coverage.
- **Input**: Audit scope from Step 1, infra vars (`{{CLOUD_REGION}}`, `{{VPC_ID}}`, `{{ECS_CLUSTER}}`, `{{S3_BUCKET_ARTIFACTS}}`, `{{RDS_ENDPOINT}}`), `{{PAGERDUTY_SERVICE_ID}}`.
- **Output**: Cloud findings report — misconfiguration list with severity, resource ARN/ID, and remediation steps.
- **Hand-off note**: Cloud findings report (CRITICAL/HIGH items flagged) to Step 5.

### Step 5: Compliance Check
- **Template**: `review/compliance-check.md`
- **Purpose**: Map all findings from Steps 2, 3, and 4 against applicable regulatory frameworks (GDPR, SOC 2, PCI-DSS, HIPAA, etc.) and flag non-compliant controls.
- **Input**: Backend, frontend, and cloud findings reports, current compliance framework targets, `{{INTERNAL_DOCS_URL}}` for control documentation.
- **Output**: Compliance gap report — control ID, status (compliant/non-compliant/in-progress), finding reference, and remediation owner.
- **Hand-off note**: Compliance gap report and full consolidated finding list to Step 6.

### Step 6: Dependency Audit
- **Template**: `review/deps-audit.md`
- **Purpose**: Scan all direct and transitive dependencies for known CVEs, license violations, and abandoned packages.
- **Input**: Package manifests (package.json, requirements.txt, go.mod, etc.), consolidated finding list from Step 5, CVE severity threshold.
- **Output**: Dependency audit report — CVE list with CVSS score, affected package, fix version, and license compliance status.
- **Hand-off note**: Full audit bundle (findings + compliance gaps + dependency report) and `{{ALERT_EMAIL}}` for critical notifications to Step 7.

### Step 7: Cloud Deploy Checklist (Security Hardening)
- **Template**: `cloud/deploy-checklist.md`
- **Purpose**: Translate all findings into a prioritized remediation plan with deployment gates — ensuring CRITICAL findings are resolved before any release and HIGH findings have accepted-risk sign-off.
- **Input**: Full audit bundle from Step 6, `{{MONITORING_DASHBOARD_URL}}`, `{{ONCALL_RUNBOOK_URL}}`, `{{DEPLOY_STRATEGY}}`, `{{ALERT_EMAIL}}`, `{{PAGERDUTY_SERVICE_ID}}`.
- **Output**: Signed-off security remediation checklist with item owners, target dates, and deployment gate status.
- **Hand-off note**: None — workflow complete when all CRITICAL items are resolved and checklist is signed off.

## Decision Points
- **Steps 2, 3, 4 parallelism**: These three scans are independent and should run concurrently to reduce total audit time. All three feed into Step 5.
- **Step 5 → escalation**: If any CRITICAL compliance control is non-compliant, escalate immediately to `{{ONCALL_RUNBOOK_URL}}` and notify `{{SLACK_CHANNEL}}` before continuing to Step 6.
- **Step 7 gate**: Do not mark the workflow complete if any CRITICAL finding remains unresolved. HIGH findings require explicit accepted-risk documentation from an authorized owner.
- **Recurrence**: For scheduled audits, compare the Step 7 checklist against the previous run to track remediation velocity.

## Success Criteria
- Zero unresolved CRITICAL findings across backend, frontend, cloud, and dependency reports.
- All HIGH findings either remediated or documented with accepted-risk sign-off.
- Compliance gap report shows no newly introduced non-compliant controls vs. the previous audit.
- Dependency audit shows no CVSS 9.0+ CVEs in direct dependencies.
- Security remediation checklist fully signed off by authorized owners.
