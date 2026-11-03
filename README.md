# CloudGuard GRC

**CloudGuard GRC** is an open-source, agentless Cloud Security Posture Management (**CSPM**) and **GRC automation platform** for AWS. Built for security engineers, compliance auditors, and DevOps teams, CloudGuard GRC automates the continuous security auditing lifecycle:

$$\text{Discover} \longrightarrow \text{Audit} \longrightarrow \text{Score Risk} \longrightarrow \text{Map to GRC Controls} \longrightarrow \text{Remediate (Terraform/CLI)} \longrightarrow \text{Audit Reports}$$

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6+-3178C6.svg)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7.4+-DC382D.svg)](https://redis.io/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-v3+-38B2AC.svg)](https://tailwindcss.com/)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose_v2-2496ED.svg)](https://www.docker.com/)

---

## 🚀 Key Features

- **🛡️ Agentless & Read-Only AWS Auditing**: Zero agents or sidecars required. Connects securely via AWS STS `AssumeRole` with unique `ExternalId` verification to protect against Confused Deputy attacks. Enforces strict read-only IAM policies (`SecurityAudit`, `ViewOnlyAccess`).
- **⚡ Regional AWS Scanning & Resource Discovery**: Multi-region discovery across S3, IAM, EC2, KMS, and CloudTrail spanning `us-east-1`, `us-west-2`, `eu-west-1`, and `ap-south-1`.
- **🔄 Durable Asynchronous Scan Queue**: Distributed scan workers powered by **Redis** and **ARQ**. Heavy cloud inventory sweeps and rules evaluation run asynchronously in background containers without API timeouts.
- **🔐 Hardened Authentication & Password Recovery**:
  - **Argon2id** password hashing with JWT access/refresh token rotation stored in HttpOnly, SameSite cookies.
  - **Login Rate Limiting**: Redis-backed request throttling (10 login attempts/min).
  - **Account Lockout**: Automatically locks accounts for 15 minutes after 5 consecutive failed login attempts.
  - **Forgot & Reset Password Flow**: Complete self-service password recovery (`/forgot-password` and `/reset-password`) with single-use, 1-hour expiration SHA-256 hashed tokens and session invalidation.
- **📜 Multi-Framework GRC Control Mapping**: Maps technical finding evidence directly to governance frameworks:
  - **CIS AWS Foundations Benchmark v1.4.0**
  - **GDPR** (EU 2016/679 Articles 32 & 33)
  - **DPDPA 2023** (Digital Personal Data Protection Act Section 8)
  - **ISO/IEC 27001:2022** (Controls A.5.15, A.8.12, A.8.20, A.8.24)
- **📑 Executive Audit Reports (PDF & HTML)**: Export professional printable compliance reports filtered by specific frameworks (`export.pdf?framework_id=cis`) or full global postures, including risk scores, severity breakdowns, and remediation plans.
- **🛠️ Actionable Remediation Guidance**: Every finding provides ready-to-apply **Terraform HCL** snippets and **AWS CLI** commands for instant remediation.
- **🔍 Zero-Leakage Local Secret Scanner**: Scans configurations, files, and environment directories for exposed AWS keys (`AKIA...`), GitHub personal access tokens, Slack webhooks, and private keys. Strictly redacts matches (`AKIA****************`) in-memory.
- **🔒 True Multi-Tenancy with PostgreSQL RLS**: Tenant data isolation enforced natively in PostgreSQL using **Row-Level Security (RLS)** (`app.current_tenant_id`). Cross-tenant leakage is cryptographically blocked at the engine layer.
- **🚨 Real-Time Webhook Alerting**: Formats and dispatches critical security notifications to Slack via Block Kit.

---

## 🏗️ Architecture

```text
               +-------------------------------------------------------+
               |             React 18 + TypeScript + Vite              |
               |                CloudGuard Web Portal                  |
               |                     (Port 5173)                       |
               +---------------------------+---------------------------+
                                           |  REST API / HttpOnly Cookies
                                           v
               +-------------------------------------------------------+
               |               FastAPI Application Engine              |
               |                      (Port 8000)                      |
               |  - Auth & Argon2id Password Hashing                   |
               |  - Rate Limiting (SlowAPI + Redis)                    |
               |  - Account Lockout & Password Reset Tokens            |
               |  - PDF / HTML Executive Report Generators             |
               +-------------+---------------------------+-------------+
                             |                           |
               Scan Enqueue  v                           v  Queries (RLS context)
     +----------------------------------+    +----------------------------------+
     |       Redis 7.4 In-Memory        |    |       PostgreSQL 15 (RLS)        |
     | - Durable Scan Job Queue         |    | - Row-Level Security Policies    |
     | - Rate Limit Counter Store       |    | - Tenants, Users, Accounts       |
     +-----------------+----------------+    | - Findings, Scans, Audit Logs    |
                       |                     +----------------------------------+
          Pulls Jobs   v
     +----------------------------------+
     |         ARQ Background           |
     |          Scan Worker             |
     | - AWS STS AssumeRole             |
     | - Multi-Region Discovery         |
     | - CIS & GRC Rules Engine         |
     | - Slack Webhook Dispatcher       |
     +-----------------+----------------+
                       |
                       v  sts:AssumeRole (Read-Only)
     +------------------------------------------------------------------+
     |                       Target AWS Accounts                        |
     |   [S3 Buckets]   [IAM Policies]   [EC2 Groups]   [CloudTrail]    |
     +------------------------------------------------------------------+
```

---

## 📋 Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend Portal** | React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons, TanStack Query v5, Zustand, React Router v6 |
| **Backend API** | Python 3.11+, FastAPI, SQLAlchemy 2.0 (Async), Alembic, Pydantic v2, Passlib (Argon2id), PyJWT, SlowAPI |
| **Worker & Queue** | ARQ, Redis 7.4 (Alpine), Boto3 (AWS SDK) |
| **Database** | PostgreSQL 15 (Alpine) with native Row-Level Security (RLS) policies |
| **Reporting** | ReportLab (PDF generation), Jinja-style HTML printable templates |
| **Testing & QA** | Pytest, Pytest-Asyncio, HTTPX, Pyright (0 errors) |
| **Containers** | Docker Engine, Docker Compose v2 |

---

## ⚡ Quickstart & Docker Setup

### Prerequisites
- [Docker Desktop](https://www.docker.com/) with Docker Compose v2
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local API development)

### 1. Clone the Repository
```bash
git clone https://github.com/StrykarBoston/CloudGuard-GRC.git
cd CloudGuard-GRC
```

### 2. Configure Environment Variables
Copy the sample environment file:
```bash
cp .env.example .env
```

### 3. Start the Full Stack with Docker Compose
```bash
docker compose up -d --build
```

This starts all 5 microservices:
| Service | Container Name | Port | Description |
| :--- | :--- | :--- | :--- |
| **Web Portal** | `fyp-web-1` | `5173` | React frontend application |
| **Backend API** | `fyp-api-1` | `8000` | FastAPI REST service |
| **Background Worker**| `fyp-worker-1` | Internal | ARQ async scan processor |
| **Database** | `fyp-postgres-1` | `5432` | PostgreSQL with Row-Level Security |
| **Queue & Cache** | `fyp-redis-1` | `6379` | Redis durable scan queue |

---

## 🌐 Application Endpoints & Access

* **Web UI Dashboard:** [http://localhost:5173](http://localhost:5173)
* **API Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **API Health Check:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
* **Forgot Password Page:** [http://localhost:5173/forgot-password](http://localhost:5173/forgot-password)

### Default Authentication Credentials
You can sign in with the pre-seeded administrative user or register a new organization:
- **Email:** `strykarboston@gmail.com`
- **Password:** `CloudGuard123!`
- **Role:** `ACCOUNT_ADMIN`

*(To test self-service password recovery, visit `/forgot-password`, enter your email, and reset your password securely via the generated token.)*

---

## 💻 Local Host Development (Without Docker)

### Backend API & Worker
```powershell
cd apps/api

# Create & activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install package dependencies
pip install -e ".[dev]"

# Apply database migrations
alembic upgrade head

# Start FastAPI API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In a separate terminal, start the background worker:
arq app.worker.WorkerSettings
```

### Frontend Web Portal
```powershell
cd apps/web

# Install npm packages
npm install

# Start Vite dev server
npm run dev

# Run production build & typecheck
npm run build
```

---

## 🧪 Testing & Code Quality

### Run Backend Test Suite
```bash
cd apps/api
pytest -v
```

### Static Type Checking (Pyright / Pylance)
The codebase is certified with **0 errors and 0 warnings** under strict type checking:
```bash
npx pyright apps/api/app
```

---

## 📁 Repository Structure

```text
├── apps/
│   ├── api/                              # FastAPI Backend Service
│   │   ├── app/
│   │   │   ├── core/                     # Security (Argon2/JWT), Config & Settings
│   │   │   ├── services/                 # Scanner, AWS Auditor, Alerting, Reports
│   │   │   │   └── rules/                # CIS AWS Foundations Rules Suite
│   │   │   ├── db.py                     # Async SQLAlchemy engine & session factory
│   │   │   ├── models.py                 # PostgreSQL ORM models & RLS declarations
│   │   │   ├── queue.py                  # ARQ / Redis job queue helpers
│   │   │   ├── repositories.py           # TenantRepository with RLS injection
│   │   │   ├── schemas.py                # Pydantic v2 input/output schemas
│   │   │   ├── worker.py                 # ARQ background scan worker & cron jobs
│   │   │   └── main.py                   # REST endpoints, routers & middleware
│   │   ├── migrations/                   # Alembic migration scripts
│   │   └── tests/                        # Pytest automated test suites
│   │
│   └── web/                              # React 18 + Vite Web Application
│       ├── src/
│       │   ├── components/               # AppShell, AuthLayout, UI components
│       │   ├── pages/                    # Dashboard, Findings, Compliance, Login,
│       │   │                             # Register, ForgotPassword, ResetPassword,
│       │   │                             # Accounts, Settings, AuditLog
│       │   ├── services/api.ts           # Central Axios client with token refresh
│       │   ├── store/                    # Zustand auth and scan state stores
│       │   └── types/                    # TypeScript interfaces & domain types
│       └── vite.config.ts                # Vite config & API reverse proxy
│
├── docker-compose.yml                    # Multi-container orchestration (5 services)
├── pyrightconfig.json                    # Pyright static type checker configuration
└── README.md                             # Project overview & documentation
```

---

## 🛡️ Security Boundary & Compliance Guidelines

1. **Strictly Read-Only**: CloudGuard GRC contains zero mutation APIs for cloud resources. It queries configurations via read-only APIs and suggests Terraform/CLI fixes.
2. **Confused Deputy Prevention**: Every STS AssumeRole call enforces an `ExternalId` tied to the onboarded tenant account.
3. **No Stored Cloud Credentials**: Never stores permanent AWS access keys. Connections use STS temporary session tokens only.
4. **Zero-Leakage Secret Redaction**: All detected secrets and keys are masked in memory (`AKIA****************`) before persistence or transmission.
5. **PostgreSQL Row-Level Security (RLS)**: Tenant boundaries are enforced directly in the database engine (`tenant_isolation_*` policies) on every connection.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
