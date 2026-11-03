# CloudGuard GRC — Engineering Team Handoff & Developer Guide

**Document Version:** 2.0.0  
**Handoff Date:** October 06, 2026  
**Target Audience:** Core Engineering Team, DevOps Engineers, Security Auditors, and Project Evaluators  
**Primary Repository:** `f:/FYP`  
**Master Specification:** `.agents/skills/cloudguard-grc-security-auditor/SKILL.md`

---

## 1. System Overview & Technology Stack

CloudGuard GRC is an agentless, multi-tenant Cloud Security Posture Management (CSPM) and GRC automation platform for AWS. It discovers cloud assets via AWS STS `AssumeRole`, evaluates configuration state against deterministic security rules, maps findings to 12 regulatory and industry compliance frameworks, provides non-executing Terraform/CLI remediation guidance, and exports audit-ready reports.

### Strict Technology Stack
- **Frontend (`apps/web`):**
  - React 18, TypeScript (Strict Mode), Vite 6
  - TailwindCSS, Custom Dark/Light Theme Cyber Design Tokens
  - Zustand (Client State), TanStack Query v5 (Server State Caching)
  - React Router v6, Axios (with `withCredentials: true` and 401 refresh interceptors), Lucide React
- **Backend (`apps/api`):**
  - Python 3.11+, FastAPI, Pydantic v2 Settings & Models
  - SQLAlchemy 2.0 Async (`asyncpg`), Alembic Migrations
  - Passlib with Argon2id (Password Hashing), PyJWT (HS256)
  - `boto3` (AWS SDK), `slowapi` (Redis-backed Rate Limiting)
  - `reportlab` (Audit PDF Generation), `httpx` (Slack Webhooks)
- **Database & Queue:**
  - PostgreSQL 15 with Row-Level Security (RLS)
  - Redis 7.4 + ARQ (`arq==0.26.3`) Asynchronous Worker Queue

---

## 2. Directory Layout & Key Modules

```text
f:/FYP/
├── apps/
│   ├── api/                           # FastAPI backend service
│   │   ├── app/
│   │   │   ├── core/                  # Configuration & Argon2/JWT security
│   │   │   │   ├── config.py          # Pydantic BaseSettings (.env loading)
│   │   │   │   └── security.py        # Password hashing, JWT creation & token digests
│   │   │   ├── services/              # Business logic & scanners
│   │   │   │   ├── aws_auditor.py     # STS AssumeRole & read-only AWS inventory
│   │   │   │   ├── rules/             # Deterministic security rules
│   │   │   │   │   ├── base.py        # RuleResult, RemediationTemplate contracts
│   │   │   │   │   └── aws_rules.py   # IAM, S3, EC2, KMS, CloudTrail rule logic
│   │   │   │   ├── compliance.py      # 12 GRC frameworks & control evaluation
│   │   │   │   ├── scanner.py         # Scan orchestrator, risk scoring & alert dispatch
│   │   │   │   ├── secret_scanner.py  # Local filesystem/code regex secret detector
│   │   │   │   ├── alerting.py        # Slack Block Kit notification dispatcher
│   │   │   │   ├── reporter.py        # Executive HTML compliance report generator
│   │   │   │   └── pdf_reporter.py    # Landscape A4 PDF audit report generator
│   │   │   ├── db.py                  # Async SQLAlchemy engine & session factory
│   │   │   ├── dependencies.py        # Auth cookie/bearer extractor & RLS injection
│   │   │   ├── main.py                # REST API routes & middleware
│   │   │   ├── models.py              # DeclarativeBase SQLAlchemy ORM entities
│   │   │   ├── queue.py               # Redis connection pool & ARQ scan enqueueing
│   │   │   ├── repositories.py        # TenantRepository with RLS context enforcement
│   │   │   ├── schemas.py             # Pydantic v2 request/response schemas
│   │   │   └── worker.py              # ARQ worker process & scheduled daily scan cron
│   │   ├── migrations/                # Alembic database migrations (with RLS)
│   │   ├── tests/                     # Pytest unit & integration test suites
│   │   ├── Dockerfile                 # Non-root (appuser) container build
│   │   └── pyproject.toml             # Pinned backend dependencies
│   └── web/                           # React frontend client
│       ├── src/
│       │   ├── components/layout/     # AppShell (Sidebar/Header) & AuthLayout
│       │   ├── hooks/                 # useCloudGuard TanStack Query hooks & mutations
│       │   ├── pages/                 # Full screen implementations
│       │   │   ├── Login.tsx          # Login with account lockout feedback
│       │   │   ├── Register.tsx       # Organization & admin user creation
│       │   │   ├── Dashboard.tsx      # ThreatScore, charts & urgent actions
│       │   │   ├── FindingsExplorer.tsx # Findings table, CSV export & detail drawer
│       │   │   ├── ComplianceMatrix.tsx # 12 Frameworks bento grid & HTML export
│       │   │   ├── Accounts.tsx       # Cloud account inventory & Scan Now
│       │   │   ├── AccountOnboarding.tsx # STS wizard with ExternalId copy
│       │   │   ├── Settings.tsx       # Tenant profile, scan schedule & Slack alert toggles
│       │   │   └── AuditLog.tsx       # Immutable audit event history viewer
│       │   ├── services/api.ts        # Axios API client with cookie refresh interceptors
│       │   ├── store/                 # Zustand stores (useAuthStore, useScanStore)
│       │   ├── types/index.ts         # TypeScript interfaces matching backend models
│       │   ├── App.tsx                # React Router v6 guarded route matrix
│       │   └── styles.css             # TailwindCSS design tokens & fonts
│       ├── Dockerfile                 # Non-root (node) container build
│       └── package.json               # Frontend dependencies
├── docs/                              # Project documentation & decisions
│   ├── AWS_TEST_ACCOUNT_SETUP_MANUAL.txt # Live AWS test account creation guide
│   └── DECISIONS.md                   # Architecture Decision Records (ADRs)
├── PDF/                               # Source-of-truth PRD, TRD, Schema, & UX documents
├── docker-compose.yml                 # Local multi-service orchestrator
├── progress.md                        # Project progress & phase implementation report
├── findings.md                        # Comprehensive security & codebase audit findings
├── todo.md                            # Prioritized backlog and team member allocations
└── handoff.md                         # This developer handoff and operations guide
```

---

## 3. Local Development & Quickstart

### Option A: Running with Docker Compose (Recommended)
Prerequisites: Docker Desktop installed and running.
```bash
# 1. From repository root:
docker-compose up -d --build

# 2. Check running services:
docker-compose ps

# Services available:
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - API Health: http://localhost:8000/health
# - API Swagger Docs: http://localhost:8000/docs
```

### Option B: Running Services Locally on Host (Windows / WSL)
Prerequisites: Python 3.11+, Node.js 20+, PostgreSQL 15, Redis 7.

#### 1. Start PostgreSQL & Redis
Ensure PostgreSQL is listening on port 5432 and Redis on port 6379. Create the database:
```sql
CREATE DATABASE cloudguard;
CREATE USER cloudguard WITH PASSWORD 'change-me-for-local-development';
GRANT ALL PRIVILEGES ON DATABASE cloudguard TO cloudguard;
```

#### 2. Start Backend API & Worker
```powershell
cd f:/FYP/apps/api

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e .

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In a separate terminal, start the background worker:
arq app.worker.WorkerSettings
```

#### 3. Start Frontend Client
```powershell
cd f:/FYP/apps/web

# Install npm packages
npm install

# Start Vite development server
npm run dev
# Accessible at http://localhost:5173
```

---

## 4. Key Architecture Patterns & Rules

### 1. Multi-Tenancy & Row-Level Security (RLS)
- Never query database tables without tenant isolation.
- Every transaction calls:
  ```python
  await session.execute(
      text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
      {"tenant_id": tenant_id},
  )
  ```
- PostgreSQL enforces: `tenant_id = current_setting('app.current_tenant_id', true)` across `cloud_accounts`, `scans`, `findings`, `tenant_settings`, and `audit_logs`.
- Defense-in-depth: Every query in `TenantRepository` also explicitly includes `.where(Model.tenant_id == self.tenant_id)`.

### 2. AWS STS AssumeRole Contract
- CloudGuard **never** accepts long-lived AWS Access Keys from users.
- Onboarding requires:
  1. Target AWS Account Number (12 digits).
  2. Target IAM Role ARN (`arn:aws:iam::<account>:role/<name>`).
  3. External ID (`cg-ext-<uuid>`) generated on the client.
- The target role must have a trust policy allowing CloudGuard's identity with the specific `sts:ExternalId`.
- The assumed role must have the AWS-managed `SecurityAudit` policy attached and **zero** inline policies.

### 3. Asynchronous Scan Lifecycle
```text
POST /api/v1/scans ➔ Scan (queued) ➔ ARQ enqueue_scan() ➔ Redis ➔
worker.py (run_scan_job) ➔ scanner.py (run_scan) ➔ aws_auditor.py (scan_aws_account) ➔
Persist Findings ➔ Update Scan (completed) ➔ Dispatch Slack Alerts
```
- Long-running scans never block HTTP request threads.
- Incomplete scans (due to throttling or regional permissions) are marked `partial=True` with `error_summary`. Never report a partial scan as fully clean.

### 4. GRC Compliance Framework Architecture
- The compliance engine (`compliance.py`) is decoupled from scanner logic.
- Controls map to supported rule IDs.
- Controls evaluate strictly to:
  - `PASS`: Scans executed and zero open findings for mapped rules.
  - `FAIL`: At least one open finding detected for a mapped rule.
  - `NEEDS_REVIEW`: Account not yet scanned, or control requires manual evidence.
- Every report and API response includes:
  `score_type: "TECHNICAL_POSTURE"` and `assurance_status: "NOT_A_CERTIFICATION"`.

---

## 5. Testing & Verification Guide

### Backend Unit & Integration Tests
Run pytest from `apps/api`:
```powershell
cd f:/FYP/apps/api
pytest
```
- **Rules Suite (`test_rules.py`):** Verifies deterministic rule evaluation against mock AWS payloads.
- **AWS Auditor Suite (`test_aws_auditor.py`):** Verifies STS AssumeRole guardrails, policy allowlists, and error handling.
- **Compliance Suite (`test_compliance.py`):** Verifies control pass/fail scoring and framework scoping.
- **Auth Security Suite (`test_auth_security.py`):** Verifies rate limiting, password hashing, and account lockout.
- **Tenant Isolation Suite (`test_tenant_isolation.py`):** Verifies cross-tenant data leakage prevention under PostgreSQL RLS.
- **PDF Reporter Suite (`test_pdf_reporter.py`):** Verifies PDF report generation with empty and populated findings.
- **Secret Scanner Suite (`test_secret_scanner.py`):** Verifies pattern detection, redaction, and path traversal prevention.

### Frontend Compilation & Typecheck
Run typecheck and build from `apps/web`:
```powershell
cd f:/FYP/apps/web
npm run build
```
Builds cleanly with zero TypeScript errors.

---

## 6. Seed Credentials & Test Accounts

### Pre-configured Local Test User:
- **Email:** `admin@cloudguard.io`
- **Password:** `AdminPassword123!`
- **Role:** `ACCOUNT_ADMIN`
- **Organization:** `Acme Security Inc.`

### Live AWS Test Account Integration:
To connect a real AWS sandbox account:
1. Follow the step-by-step instructions in [`docs/AWS_TEST_ACCOUNT_SETUP_MANUAL.txt`](file:///f:/FYP/docs/AWS_TEST_ACCOUNT_SETUP_MANUAL.txt).
2. Create the IAM role `CloudGuardAuditRole` with `SecurityAudit` managed policy.
3. Configure the trust policy with CloudGuard's AWS caller ARN and the ExternalId from the onboarding wizard.
4. Paste the Role ARN into the CloudGuard Onboarding Wizard (`/accounts/onboard`) and click **Verify & Connect**.

---

## 7. Golden Rules for Future Development (SKILL.md Section 26)

1. **Strictly Read-Only:** Never introduce AWS API calls that create, update, or delete cloud resources.
2. **Never Execute Remediation:** Generated Terraform and AWS CLI snippets are advisory guidance only. Never execute remediation automatically.
3. **Never Log or Store Secrets:** All detected secrets must be masked with `redact_secret()`. Never store plaintext AWS credentials.
4. **Enforce Tenant Context:** Never bypass RLS or write raw SQL queries that omit `tenant_id`.
5. **No Rule Evaluation in UI:** Rule evaluation logic belongs exclusively in `app/services/rules/`. The UI only displays normalized findings and compliance scores.

