# CloudGuard GRC — Comprehensive Security & Architecture Audit Findings

**Document Version:** 2.0.0  
**Audit Date:** October 06, 2026  
**Auditor:** CloudGuard GRC Security & Quality Assurance Team  
**Scope:** Full repository codebase (`apps/api/`, `apps/web/`, `docker-compose.yml`, migrations, Dockerfiles, config, and dependencies) against `.agents/skills/cloudguard-grc-security-auditor/SKILL.md`.

---

## 1. Executive Summary & Security Posture

A comprehensive security, architecture, and code-level audit was conducted across the entire CloudGuard GRC codebase. CloudGuard GRC adheres to strict read-only, agentless security principles. AWS access requires AWS STS `AssumeRole` with an `ExternalId` parameter and an enforced IAM managed policy allowlist (`SecurityAudit` and `ViewOnlyAccess`). No AWS credentials or secrets are accepted from browser clients or stored in the database.

Multi-tenancy is enforced with defense-in-depth:
1. **Application Layer:** Every database query in `TenantRepository` and background workers explicitly filters by `tenant_id`.
2. **Database Layer:** PostgreSQL Row-Level Security (RLS) is enabled and forced (`FORCE ROW LEVEL SECURITY`) on all core entity tables (`cloud_accounts`, `scans`, `findings`, `tenant_settings`, and `audit_logs`), keyed to the transaction-local variable `app.current_tenant_id`.

---

## 2. Verification of Prior Security & Bug Fixes

The codebase was audited to confirm that all 14 previously identified vulnerabilities and 9 bugs were addressed and remain securely implemented:

| ID | Issue & Description | Current Code Status | Verification Evidence |
| :--- | :--- | :--- | :--- |
| **SEC-001** | Docker containers running as root | **RESOLVED** | `apps/api/Dockerfile` creates and runs as `appuser`. `apps/web/Dockerfile` runs as `node`. |
| **SEC-002** | Database & Redis ports exposed on host | **RESOLVED** | `docker-compose.yml` removed host port mappings for `postgres` and `redis`. Services communicate exclusively over the internal Docker network. |
| **SEC-003** | Hardcoded secrets in config / source | **RESOLVED** | `apps/api/app/core/config.py` requires `database_url` and `jwt_secret` from environment variables, validating `jwt_secret` is ≥32 characters. |
| **SEC-004** | PostgreSQL RLS bypass by table owners | **RESOLVED** | Migration `585f85e76efb` and `20261002_operational` apply `ALTER TABLE ... FORCE ROW LEVEL SECURITY` across all tenant-scoped tables. |
| **SEC-005** | Plaintext tokens in `localStorage` | **RESOLVED** | `useAuthStore.ts` and `api.ts` completely eliminated `localStorage`/`sessionStorage` token storage. Authentication uses secure `HttpOnly`, `SameSite=Lax` cookies. |
| **SEC-006** | Absence of rate limiting on auth endpoints | **RESOLVED** | `slowapi` rate limiter backed by Redis is configured on `/api/v1/auth/login` (10/min), `/register` (5/min), and `/refresh` (20/min). |
| **SEC-007** | Brute-force account lockout missing | **RESOLVED** | `User` model tracks `failed_login_attempts`. 5 consecutive failed logins trigger a 15-minute lockout (`locked_until`). |
| **SEC-008** | Missing HTTP security headers | **RESOLVED** | Middleware in `main.py` applies `Content-Security-Policy`, `X-Frame-Options: DENY`, and `X-Content-Type-Options: nosniff` to all HTTP responses. |
| **SEC-009** | Path traversal in local secret scanning | **RESOLVED** | `/api/v1/scans/secrets` validates `target.is_relative_to(root)` and rejects unauthorized traversal outside `secret_scan_root` with HTTP 403. |
| **SEC-010** | Unredacted secrets in alerts/evidence | **RESOLVED** | `secret_scanner.py` applies `redact_secret()`, masking all but the first 4 characters. |
| **SEC-011** | Dashboard stats including suppressed findings | **RESOLVED** | `main.py` `/api/v1/dashboard` aggregates only findings where `status == "OPEN"`. |
| **SEC-012** | Pre-filled admin email on login page | **RESOLVED** | `Login.tsx` initializes `email` state to an empty string. |
| **SEC-013** | Dynamic severity chart heights | **RESOLVED** | `Dashboard.tsx` calculates bar chart heights proportionally to `maxSeverityCount`. |
| **SEC-014** | Finding drawer badge styling | **RESOLVED** | `FindingsExplorer.tsx` applies distinct styling classes for `CRITICAL`, `HIGH`, `MEDIUM`, and `LOW` severities. |
| **BUG-001** | IAM Wildcard detection rule failure | **RESOLVED** | `_check_policy_document` in `aws_auditor.py` passes `has_wildcard=True` to `evaluate_iam_wildcard`, ensuring wildcard admin policies are correctly detected. |
| **BUG-002** | FindingOut missing `evidence` field | **RESOLVED** | `FindingOut` in `schemas.py` includes `evidence: dict[str, Any]`, allowing sanitized evidence to display in the frontend drawer. |
| **BUG-003** | Frontend Finding type missing `risk_score` | **RESOLVED** | `types/index.ts` includes `risk_score: number`. |
| **BUG-004** | Duplicate attributes in `config.py` | **RESOLVED** | Duplicate definitions of `redis_url` and `slack_webhook_url` were removed. |
| **BUG-005** | ISO 27001 control A.8.12 permanently in NEEDS_REVIEW | **RESOLVED** | Added `secrets.exposed-aws-access-key` to `SUPPORTED_AWS_RULES` in `compliance.py`. |
| **BUG-006** | Framework export route ignoring `framework_id` | **RESOLVED** | `/api/v1/reports/compliance/{framework_id}/export` filters compliance list and findings strictly by `framework_id` and returns HTTP 404 for unknown frameworks. |
| **BUG-007** | Hardcoded scan schedule on Dashboard | **RESOLVED** | `Dashboard.tsx` dynamically renders schedule label from `useSettings` API data. |
| **BUG-008** | Company name showing tenant UUID | **RESOLVED** | `Settings.tsx` displays `organization?.name` fetched from the `/api/v1/organization` endpoint. |
| **BUG-009** | Static non-functional Settings page | **RESOLVED** | `Settings.tsx` is fully wired to `useSettings` and `useUpdateSettings` mutations. |

---

## 3. Current Codebase Audit Findings

Below are the findings identified during the current codebase audit, categorized by severity:

### Finding CG-2026-01 (Medium)
**Title:** Docker Compose AWS Credential Mount Path vs Non-Root User Permissions  
**Component:** `docker-compose.yml`, `apps/api/Dockerfile`  
**Description:**  
In `apps/api/Dockerfile`, the container user is configured as `appuser` (non-root):
```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```
However, in `docker-compose.yml`, lines 33–34, 40, 57–58, and 62 configure:
```yaml
AWS_SHARED_CREDENTIALS_FILE: /root/.aws/credentials
AWS_CONFIG_FILE: /root/.aws/config
volumes:
  - ${AWS_CONFIG_DIR:-./.aws}:/root/.aws:ro
```
Because `/root` on Linux default installations has restrictive permissions (`0700`), the unprivileged user `appuser` will encounter `PermissionDenied` errors when attempting to read `/root/.aws/credentials` or `/root/.aws/config` inside the container.  
**Impact:** AWS STS AssumeRole calls will fail to locate host AWS credentials when running inside the Docker Compose environment unless the container runs as root or the mount path is adjusted.  
**Remediation:**  
Update `docker-compose.yml` to mount credentials into `/home/appuser/.aws:ro` and set:
```yaml
AWS_SHARED_CREDENTIALS_FILE: /home/appuser/.aws/credentials
AWS_CONFIG_FILE: /home/appuser/.aws/config
volumes:
  - ${AWS_CONFIG_DIR:-./.aws}:/home/appuser/.aws:ro
```

---

### Finding CG-2026-02 (Low)
**Title:** Local Secret Scanner Findings are Ephemeral (Not Persisted in Findings Database)  
**Component:** `apps/api/app/main.py` (`scan_secrets_endpoint`), `apps/api/app/services/secret_scanner.py`  
**Description:**  
The secret scanning endpoint `POST /api/v1/scans/secrets` runs `scan_local_path` or `scan_content` and returns a list of dictionaries directly in the HTTP response. The findings are not converted to `Finding` records or associated with an audit scan in the PostgreSQL database.  
**Impact:** Secret scanning results are not reflected on the Dashboard ThreatScore, Findings Explorer, or exported compliance reports.  
**Remediation:**  
Optionally provide an endpoint to attach local secret scan findings to a designated audit scan or create a dedicated "Source Repository Audit" entity.

---

### Finding CG-2026-03 (Low)
**Title:** PDF Export Does Not Support Framework Scoping (Unlike HTML Export)  
**Component:** `apps/api/app/main.py` (`export_audit_pdf`), `apps/api/app/services/pdf_reporter.py`  
**Description:**  
While the HTML export endpoint supports scoping by framework (`GET /api/v1/reports/compliance/{framework_id}/export`), the PDF endpoint (`GET /api/v1/reports/export.pdf`) exports all frameworks and all open findings globally.  
**Impact:** Users cannot download a single-framework PDF compliance report (e.g., exclusively CIS AWS or HIPAA).  
**Remediation:**  
Update `export_audit_pdf` to accept an optional `framework_id: str | None = None` query parameter and filter the `frameworks` list and `findings` list using `framework_rule_ids()` before passing them to `generate_audit_pdf`.

---

### Finding CG-2026-04 (Low)
**Title:** Ruff Linting Code Style and Formatting Warnings in Test Files  
**Component:** `apps/api/tests/`  
**Description:**  
Running `ruff check .` across `apps/api` reports formatting and unused import warnings in test files:
- Unused imports (`evaluate_s3_encryption` in `test_rules.py`, `pytest_asyncio` in `test_tenant_isolation.py`, `app.db.engine` in `test_workflow.py`).
- Line lengths exceeding 100 characters in assertion statements.  
**Impact:** Minor code hygiene and CI lint test failures.  
**Remediation:**  
Run `ruff check . --fix` and `ruff format .` across `apps/api`.

---

### Finding CG-2026-05 (Informational)
**Title:** Daily Automated Scans are Scheduled Sequentially Across Accounts  
**Component:** `apps/api/app/worker.py` (`enqueue_due_daily_scans`)  
**Description:**  
In `worker.py`, the scheduled cron job queries all active cloud accounts for a tenant and enqueues scan jobs into the ARQ queue. While the ARQ worker executes up to 4 concurrent jobs (`max_jobs = 4`), for large multi-account enterprises (dozens of accounts), enqueued jobs will queue up in Redis.  
**Impact:** None for current MVP scale. Relevant for enterprise roadmap scaling.  
**Remediation:**  
Monitor queue length and scale worker replica containers in `docker-compose.yml` or production ECS task definitions.

---

### Finding CG-2026-06 (Informational)
**Title:** Playwright Browser Integration Tests Not Yet Implemented  
**Component:** `apps/web/`  
**Description:**  
Phase 9 calls for Playwright browser E2E tests (`login -> connect account -> validate -> start scan -> inspect findings -> compliance -> report`). Currently, unit tests cover backend APIs extensively, while frontend tests rely on TypeScript compilation and manual verification.  
**Impact:** UI regressions could occur without automated end-to-end browser testing.  
**Remediation:**  
Scaffold Playwright test suite in `apps/web` with simulated API fixtures.

---

## 4. Security Verification Summary

| Security Domain | Posture | Audit Evaluation |
| :--- | :--- | :--- |
| **AWS Authentication** | Strict Read-Only | Uses STS `AssumeRole` with ExternalId; validates `SecurityAudit` policy; disallows inline policies; no keys stored. |
| **Tenant Isolation** | Defense-in-Depth | PostgreSQL RLS enabled and forced on all tables; repository layer explicitly scopes all queries to `tenant_id`. |
| **Credential Storage** | Secure | Passwords hashed with Argon2id; refresh tokens stored as SHA-256 hashes; secrets redacted from logs and evidence. |
| **Transport & Session** | Hardened | HttpOnly SameSite=Lax cookies; SlowAPI rate limiting; 15-minute account lockout; CSP security headers. |
| **Destructive Actions** | Prohibited | Zero AWS mutations; auto-remediation disabled; account deletion drops local metadata only. |

