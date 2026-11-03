# CloudGuard GRC API

The **CloudGuard GRC API** is a high-performance, asynchronous REST backend service built with **Python 3.11+** and **FastAPI**. It handles tenant isolation, authentication, background scan dispatching, compliance mapping, and executive report generation.

---

## 🏗️ Architecture & Layering

The API adheres to a strict four-layer clean architecture pattern:
1. **Routing & Controllers (`app/main.py`)**: Request validation, rate-limiting (`slowapi`), HTTP-only cookies, OpenAPI generation.
2. **Business Services (`app/services/`)**:
   - `aws_auditor.py`: Read-only AWS STS AssumeRole client, multi-region resource fetcher, rule executor.
   - `scanner.py`: Scan pipeline coordinator, risk score calculator, finding persistence.
   - `secret_scanner.py`: In-memory credential and secret exposure detector with automatic redaction.
   - `compliance.py`: Multi-framework posture calculators (CIS, GDPR, DPDPA, ISO 27001).
   - `pdf_reporter.py` & `reporter.py`: Executive PDF & HTML compliance report generators.
   - `alerting.py`: Slack Block Kit webhook notification dispatcher.
3. **Tenant Repositories (`app/repositories.py`)**: Data access layer injecting PostgreSQL Row-Level Security (`set_config('app.current_tenant_id', ...)`).
4. **Data Models & Database (`app/models.py`, `app/db.py`)**: Async SQLAlchemy 2.0 ORM mappings with declarative RLS schemas and Alembic migrations.

---

## 🚀 Key Endpoints

| Category | Method & Path | Description |
| :--- | :--- | :--- |
| **System** | `GET /api/v1/health` | Healthcheck returning service & environment status |
| **Auth** | `POST /api/v1/auth/register` | Create a new tenant organization and admin account |
| **Auth** | `POST /api/v1/auth/login` | Authenticate with Argon2id; sets HttpOnly JWT session cookies |
| **Auth** | `POST /api/v1/auth/forgot-password` | Generate single-use password reset token |
| **Auth** | `GET /api/v1/auth/reset-password/verify` | Verify reset token expiration and validity |
| **Auth** | `POST /api/v1/auth/reset-password` | Reset password, lift lockouts, and revoke active sessions |
| **Accounts** | `GET /api/v1/cloud-accounts` | List all onboarded AWS accounts under active tenant |
| **Accounts** | `POST /api/v1/cloud-accounts/onboard` | Validate and onboard an AWS account using STS AssumeRole |
| **Scans** | `POST /api/v1/scans` | Enqueue an asynchronous scan job in Redis queue |
| **Findings** | `GET /api/v1/findings` | Query detected security findings with evidence and remediation |
| **Compliance** | `GET /api/v1/compliance` | Compute real-time scores for CIS, GDPR, DPDPA, and ISO 27001 |
| **Reports** | `GET /api/v1/reports/export.pdf` | Generate printable executive PDF audit report |
| **Reports** | `GET /api/v1/reports/compliance/{framework_id}/export.pdf` | Generate PDF report filtered by specific framework |

---

## 🛠️ Local Development

### 1. Setup Virtual Environment & Dependencies
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 2. Apply Database Migrations
```powershell
alembic upgrade head
```

### 3. Start Development Server
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 4. Start Background Worker (ARQ)
```powershell
arq app.worker.WorkerSettings
```

---

## 🧪 Testing & Code Quality

```powershell
# Run automated tests
pytest -v

# Run type checker (0 errors, 0 warnings certified)
npx pyright app
```
