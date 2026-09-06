# CloudGuard GRC

CloudGuard GRC is an agentless, read-only AWS cloud-security auditing and GRC automation platform. It is being built as a local-first MVP before production deployment.
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-v3+-38B2AC.svg)](https://tailwindcss.com/)

## Phase 1 status
**CloudGuard GRC** is an open-source, agentless Cloud Security Posture Management (**CSPM**) and **GRC automation platform** for AWS. Built for security engineers, compliance auditors, and DevOps teams, CloudGuard GRC automates the continuous security auditing lifecycle:

Phase 1 establishes the monorepo layout, reproducible local dependencies, Docker Compose services, and baseline API/web health checks. No AWS mutation or credential storage is implemented.
$$\text{Find} \longrightarrow \text{Explain} \longrightarrow \text{Prioritize} \longrightarrow \text{Map to GRC Controls} \longrightarrow \text{Remediate (Terraform/CLI)} \longrightarrow \text{Audit Report}$$

## Prerequisites
---

- Docker Desktop with Compose v2
- Node.js 20.19+ or 22.12+
- Python 3.11+
## 🚀 Key Features

## Local startup
- **🛡️ Agentless & Read-Only AWS Auditing**: Zero agents required. Connects via dedicated read-only IAM roles using AWS STS `AssumeRole` with unique `ExternalId` parameters to prevent Confused Deputy attacks.
- **⚡ Deterministic CIS Rules Engine**: Out-of-the-box checks aligned with **CIS AWS Foundations Benchmark v1.4.0**:
  - `aws.iam.root-mfa`: Enforce hardware/virtual MFA on AWS root accounts.
  - `aws.s3.public-access-block`: Detect buckets without full S3 Block Public Access.
  - `aws.ec2.security-group.open-admin`: Flag unrestricted ingress on Port 22 (SSH) from `0.0.0.0/0`.
  - `aws.iam.wildcard-admin`: Catch overly permissive wildcard `*:*` policies.
  - `aws.iam.stale-access-keys`: Highlight active user access keys unrotated for $>90$ days.
  - `aws.s3.default-encryption`: Verify bucket server-side encryption (SSE-S3 / KMS).
  - `aws.cloudtrail.logging-enabled`: Check multi-region CloudTrail audit trails.
- **🔍 Zero-Leakage Local Secret Scanner**: Scans configurations, files, and environment trees for exposed AWS keys (`AKIA...`), GitHub personal access tokens, Slack tokens, and private keys. Strictly redacts matches (`AKIA****************`) to prevent secret leakage.
- **📜 Multi-Framework GRC Control Mapping**: Maps technical finding evidence directly to:
  - **CIS AWS Foundations Benchmark v1.4.0**
  - **GDPR** (EU 2016/679 Art. 32 & 33)
  - **DPDPA 2023** (Digital Personal Data Protection Act Sec. 8)
  - **ISO/IEC 27001:2022** (A.5.15, A.8.12, A.8.20, A.8.24)
- **🔒 True Multi-Tenancy with PostgreSQL RLS**: Tenant data isolation enforced natively in PostgreSQL using **Row-Level Security (RLS)** (`app.current_tenant_id`). Cross-tenant data leakage is cryptographically blocked at the engine layer.
- **📑 Executive Audit Reports**: Export professional HTML/PDF compliance reports containing threat scores, risk breakdowns, account inventories, and auditor attestation notices.
- **🛠️ Actionable Remediation Guidance**: Every finding provides copyable **Terraform HCL** blocks and **AWS CLI** commands for immediate resolution.
- **🚨 Real-Time Webhook Alerting**: Formats and dispatches critical security notifications formatted for Slack Block Kit.

1. Copy `.env.example` to `.env` and replace the local database password.
2. Run `docker compose up --build`.
3. Open `http://localhost:5173` and check `http://localhost:8000/health`.
---

For faster host-based development, see `apps/api/README.md` and `apps/web/README.md`.
## 🏗️ Architecture

## Repository layout
```text
React 18 + TypeScript + Vite + TailwindCSS
                  │ (REST / JSON)
                  ▼
         FastAPI (Python 3.12)
                  │
   ┌──────────────┼──────────────┐
   ▼              ▼              ▼
JWT Auth &     Rules Engine   Local Secret
Argon2id       (CIS AWS)      Scanner (Redacted)
   │              │              │
   └──────────────┼──────────────┘
                  ▼
       PostgreSQL 15 + AsyncPG
     (Row-Level Security / RLS)
```

---

## 📋 Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite, TypeScript (Strict), Tailwind CSS, Lucide Icons, TanStack Query v5, Zustand, React Router v6 |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy 2.0 Async, Alembic, Pydantic v2, Passlib (Argon2id), PyJWT, HTTPX |
| **Database** | PostgreSQL 15+ with native Row-Level Security (RLS) policies |
| **Testing** | Pytest, Pytest-Asyncio, HTTPX ASGI Transport |
| **Containers** | Docker, Docker Compose |

---

## ⚡ Quickstart & Local Setup

### 1. Prerequisites
- [Docker Desktop](https://www.docker.com/) with Compose
- [Python 3.11+](https://www.python.org/) & [`uv`](https://docs.astral.sh/uv/)
- [Node.js 20+](https://nodejs.org/) & `npm`

### 2. Clone the Repository
```bash
git clone https://github.com/StrykarBoston/CloudGuard-GRC.git
cd CloudGuard-GRC
```

### 3. Start Database (PostgreSQL with RLS)
```bash
docker compose up -d postgres
```

### 4. Setup and Start Backend API
```bash
cd apps/api

# Install dependencies via uv
uv sync

# Run database migrations
uv run alembic upgrade head

# Start FastAPI server
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **API Swagger Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check:** [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### 5. Setup and Start Frontend Web Portal
In a separate terminal:
```bash
cd apps/web

# Install packages
npm install

# Start Vite dev server
npm run dev
```
- **Web Application Portal:** [http://localhost:5173](http://localhost:5173)

---

## 🔐 Default Access & Authentication

CloudGuard GRC enforces secure authentication with `Argon2id` password hashing and JWT sessions.

- **Email:** `admin@cloudguard.io`
- **Password:** `AdminPassword123!`
- **Role:** `ACCOUNT_ADMIN`

*To create additional tenants, visit the `/register` route. Each registration automatically establishes an isolated PostgreSQL tenant boundary.*

---

## 🧪 Automated Testing & QA

Run the full automated test suite covering rules evaluation, secret redaction, multi-tenant isolation, and E2E workflows:

```bash
cd apps/api
uv run pytest -v
```

### Test Coverage Highlights:
- `tests/test_rules.py`: Validates positive and negative cases for all AWS CIS rules.
- `tests/test_secret_scanner.py`: Verifies zero-leakage redaction of credentials.
- `tests/test_tenant_isolation.py`: Security audit proving PostgreSQL RLS blocks cross-tenant access.
- `tests/test_workflow.py`: Verifies the complete user journey: *Register ➔ Onboard ➔ Scan ➔ Findings ➔ Compliance*.

---

## 📁 Repository Structure

```text
apps/
  api/   FastAPI service: routes -> services -> repositories -> data layer
  web/   React + TypeScript + Vite client
docs/    Architecture decisions
.
├── apps/
│   ├── api/                     # FastAPI Backend Service
│   │   ├── app/
│   │   │   ├── core/            # Security (Argon2/JWT) & Config
│   │   │   ├── services/        # Scanner, Secret Scanner, Reporter, Alerting
│   │   │   │   └── rules/       # CIS AWS Foundations Rules Suite
│   │   │   ├── db.py            # Async SQLAlchemy engine & session
│   │   │   ├── models.py        # Database ORM models
│   │   │   ├── repositories.py  # Tenant-aware repositories with RLS injection
│   │   │   └── main.py          # REST API endpoints
│   │   ├── migrations/          # Alembic async migration scripts (RLS policies)
│   │   └── tests/               # Pytest automated test suite
│   └── web/                     # React 18 + Vite Web App
│       ├── src/
│       │   ├── components/      # UI components and AppShell
│       │   ├── pages/           # Dashboard, Findings, Compliance, Onboarding
│       │   ├── hooks/           # TanStack Query hooks
│       │   └── services/        # Centralized Axios API client
├── docs/                        # Architecture & Planning Documentation
├── docker-compose.yml           # Local multi-service configuration
└── README.md
```

## Security boundary
---

CloudGuard’s MVP is read-only. AWS access will be server-side only, through a dedicated role and STS AssumeRole with an ExternalId. Never add AWS credentials to source control or browser code.
## 🛡️ Security Boundary & Guidelines

1. **Read-Only Enforced**: CloudGuard GRC contains no destructive AWS API mutation calls.
2. **Never Store Plaintext Secrets**: AWS access relies exclusively on role assumption via STS. All detected secrets are redacted in-memory.
3. **Tenant Boundary**: Authorization is checked at both the service layer and natively enforced at the PostgreSQL database engine layer using Row-Level Security.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
