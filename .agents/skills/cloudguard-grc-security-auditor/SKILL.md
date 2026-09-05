---
name: cloudguard-grc-security-auditor
description: Persistent Antigravity project skill for building CloudGuard GRC, an open-source AWS cloud security auditing, CSPM and GRC automation platform. Covers product scope, AWS read-only auditing, secret exposure detection, risk scoring, compliance mapping, remediation guidance, multi-tenancy, architecture, security, testing, UI, APIs, and phased implementation.
---

# CloudGuard GRC — Antigravity Project Skill

## 1. Mission and product definition

Build **CloudGuard GRC**, an agentless, open-source Cloud Security Posture Management (CSPM) and GRC automation tool for **AWS**.

Core value:
**find → explain → prioritize → map to GRC controls → recommend safe remediation → re-scan → report**

The product detects:
- cloud configuration mismanagement
- public/excessive exposure
- excessive IAM permissions
- security/logging gaps
- selected encryption/configuration gaps
- exposed secrets in local source/configuration
- compliance-control failures

Primary mode for V1/MVP: **read-only**. No destructive AWS mutation and no automatic remediation.

Target users:
- Cloud/DevOps engineers
- developers
- security engineers
- GRC/security auditors
- startup teams
- instructors/students

Architecture target: multi-tenant SaaS with service-oriented/serverless-compatible components. The implementation must support a safe local MVP before production deployment.

## 2. Source-of-truth planning documents

Before major implementation, read these when present:
1. `docs/PRD.md`
2. `docs/TRD.md`
3. `docs/APP_FLOW.md`
4. `docs/UI_UX_BRIEF.md`
5. `docs/BACKEND_SCHEMA.md`
6. `docs/IMPLEMENTATION_PLAN.md`
7. `docs/DECISIONS.md`

Use this order:
PRD → TRD → App Flow → UI/UX Brief → Backend Schema → Implementation Plan.

Do not start substantial coding from a vague request. For substantial tasks:
1. inspect repo and relevant docs
2. state goal, assumptions, and acceptance criteria
3. create a concise implementation plan
4. implement the smallest coherent change
5. run focused tests/lint/type checks
6. verify behavior and security paths
7. summarize changed files, tests, and remaining risks
8. record architecture decisions in `docs/DECISIONS.md`

Do not rebuild unrelated modules.

## 3. Strict technology stack

Do not introduce replacements without explicit user approval.

### Frontend
- React 18+
- Vite
- TypeScript, strict mode
- TailwindCSS
- shadcn/ui
- Zustand for client state
- TanStack Query for server state
- React Router v6
- Recharts

Frontend conventions:
- functional components + React Hooks
- typed props/interfaces
- shadcn/ui primitives preferred over ad-hoc raw UI
- API access centralized in `services/api.ts`
- Axios interceptors may inject JWT access tokens
- no AWS credentials or boto3 calls in browser code
- scanners/business logic stay outside UI components

### Backend
- Python 3.11+
- FastAPI
- Pydantic
- boto3
- PyJWT
- Passlib with Argon2 for password hashing
- SQLAlchemy 2.0 Async
- Alembic

Backend layering:
`routes/controllers → services → repositories → data layer`

Use Python type hints universally. Validate all request/response payloads with Pydantic.

### Database
Production target:
- PostgreSQL 15+
- Row-Level Security (RLS) for tenant isolation

MVP option:
- SQLite is acceptable only for a deliberately local MVP if the schema and repository layer remain migration-friendly to PostgreSQL.
- Do not weaken authorization rules merely because SQLite lacks PostgreSQL RLS.

### Background scanning
Target:
- AWS SQS + boto3
- Celery may be used where appropriate

Keep the scan engine decoupled so local development can use an in-process/mock queue and production can use a durable worker queue.

## 4. Security architecture and AWS access

### Non-negotiable rules
1. Never hardcode AWS keys.
2. Never ask users to upload long-lived production access keys when role assumption is possible.
3. Never use AWS root credentials.
4. Use a dedicated **read-only IAM role** and STS `AssumeRole`.
5. Require/use an `ExternalId` for SaaS-style cross-account role assumption.
6. Store only connection metadata; never store plaintext AWS secrets.
7. Keep AWS access server-side.
8. MVP contains no destructive AWS calls.
9. Never execute generated remediation automatically.
10. Redact secrets from UI, API, logs, reports, fixtures, screenshots, and tests.
11. Enforce authorization on the server.
12. Treat AWS metadata and scanner findings as untrusted data.
13. Mark incomplete scans as `partial`; never report a partial scan as clean.

MVP account onboarding:
`IAM Role ARN + ExternalId → STS AssumeRole validation → account metadata stored → scan authorization`

Validate access with harmless calls only.

## 5. Core user journey

`Login/Register → Add AWS account → Validate read-only access → Configure scan → Start scan → Scan progress → Findings → Risk prioritization → GRC mapping → Remediation guidance → Re-scan → Audit report`

## 6. Core product modules

1. Authentication and authorization
2. Multi-tenant organization/account management
3. AWS connector and STS role assumption
4. Scan orchestrator and background workers
5. Deterministic security rule engine
6. Local secret scanner
7. Finding normalizer
8. Risk scoring engine
9. GRC/control mapper
10. Remediation guidance generator
11. Dashboard and finding explorer
12. Compliance/audit reporting
13. Immutable audit/event logging
14. Notifications/integrations in later phases

## 7. MVP security checks

Start with deterministic read-only rules for:

### S3
- public bucket/access exposure
- public access configuration
- selected encryption/configuration posture

### EC2/network
- security groups permitting unrestricted administrative ingress, especially SSH/RDP exposure
- region-aware resource enumeration

### IAM
- unsafe wildcard actions/resources where determinable
- excessive/admin-like permissions
- overly broad policies and trust/permission anomalies that can be evaluated safely

### Logging
- CloudTrail/logging posture

### Local secret scanning
Scan the user's local project/source tree, not their live AWS data by default.
- configurable paths/file types
- ignore binaries and dependency/build directories
- pattern + context/entropy checks where useful
- suppression with reason
- never print or persist the complete detected secret
- use fake sentinel secrets in tests

The scanner must:
- use read-only AWS APIs only
- paginate
- handle regions
- timeout and retry with backoff on throttling
- distinguish `AccessDenied`, unsupported service/region, and partial scan
- never silently skip failures

## 8. Rule engine contract

Keep rules data-driven and independent of UI.

Each rule defines:
- `rule_id`
- `service`
- `title`
- `description`
- `category`
- `severity`
- secure-state/evaluation logic
- evidence template
- remediation
- `owner_role`
- `grc_controls`
- references
- enabled state

Adding a rule:
1. define threat/problem
2. define secure state
3. define minimal AWS read-only calls
4. implement deterministic evaluation
5. define sanitized evidence
6. define severity and rationale
7. define owner role
8. map to controls
9. add remediation guidance
10. add positive/negative/error tests
11. register the rule
12. surface it in findings/reporting
13. verify no secret leakage

UI must never contain rule evaluation logic.

## 9. Canonical finding model

At minimum:
- finding_id
- rule_id
- scan_id
- tenant_id
- account_id
- region
- resource_type
- resource_identifier
- severity
- risk_score
- status
- first_seen
- last_seen
- title
- explanation
- evidence
- remediation
- owner_role
- grc_controls
- suppression_reason

Never store secret values as finding evidence.

## 10. Risk engine

Use a transparent, documented risk model rather than an opaque AI score.

Possible inputs:
- severity
- internet exposure
- privilege scope
- sensitive-data relevance
- exploitability/likelihood
- compensating controls

Output:
- Critical
- High
- Medium
- Low

Always show enough rationale that a developer/auditor can understand why the result received its score.

## 11. GRC and compliance mapping

The GRC layer maps technical findings to control frameworks.

Initial framework coverage may include:
- CIS-aligned AWS controls
- DPDPA-related controls
- GDPR-related controls where applicable

Keep framework data separate from scanner code.

Each framework/control record should retain:
- framework name/version
- control ID
- title
- control summary
- mapped rule IDs
- scanner evidence
- status: `pass | fail | needs-review`

A technical finding mapped to a control is **not** by itself proof of legal compliance or certification. Do not make certification claims.

A finding may map to one or multiple controls.

## 12. Remediation guidance

Each actionable finding should provide:
- what is wrong
- why it matters
- likely impact
- responsible owner role
- safe remediation steps
- AWS CLI example where deterministic
- Terraform example where deterministic

Environment-specific commands must be clearly marked as examples.

AI may assist in producing non-executing remediation guidance, but:
- separate generation from execution
- never auto-run AI-generated commands
- never treat AI output as a security authority
- sanitize untrusted finding/resource content before sending to any model

## 13. Database and multi-tenancy

Core entities:
1. `tenants`
2. `users`
3. `sessions`
4. `cloud_accounts`
5. `scans`
6. `findings`
7. `rules`
8. `grc_frameworks`
9. `grc_controls`
10. `finding_control_mappings`
11. `audit_logs` / `audit_events`
12. `reports`

User roles:
- SUPER_ADMIN
- ACCOUNT_ADMIN
- ANALYST
- AUDITOR
- VIEWER

Relationships:
- tenant owns users, cloud accounts, scans, findings, reports and audit events
- scan belongs to one cloud account and tenant
- finding belongs to scan, rule, cloud account and tenant
- finding/control mapping connects findings to GRC controls

### Critical RLS requirement for PostgreSQL
For `findings`, `cloud_accounts`, and `audit_logs`, enforce tenant isolation using:
`tenant_id = current_setting('app.current_tenant_id')`

The application must also enforce tenant authorization in service/repository queries. Never rely only on a client-supplied tenant ID.

## 14. UI/screens

Required baseline screens:
- `/login`
- `/register`
- `/dashboard`
- `/accounts/onboard`
- `/findings`
- finding detail drawer
- `/compliance`

Dashboard:
- global ThreatScore/risk score
- risk distribution charts
- top findings
- scan status/history
- account summary
- compliance overview

Account onboarding:
- IAM Role ARN
- ExternalId
- validation result
- permissions/access errors
- account identity/region summary

Findings:
- filtering by severity/service/account/region/status
- search
- resource identifier
- sanitized evidence
- owner
- GRC control mapping
- remediation
- scan timestamp

Finding detail drawer:
- title
- explanation
- impact
- affected AWS resource/ARN
- severity/risk rationale
- GRC controls
- Terraform/CLI guidance

Compliance:
- framework/control matrix
- pass/fail/needs-review
- evidence references
- PDF export

UI design direction from the project context:
- dark mode
- canvas `#090d16`
- surface `#131c2e`
- primary CTA `#2563eb`
Use these consistently unless a later approved UI/UX document overrides them.

## 15. API surface

Keep route handlers thin. Business logic belongs in services.

Suggested API groups:
- `/auth/*`
- `/tenants/*`
- `/users/*`
- `/cloud-accounts/*`
- `/scans/*`
- `/findings/*`
- `/rules/*`
- `/compliance/*`
- `/reports/*`
- `/audit-logs/*`

Important behaviors:
- JWT-based authentication
- refresh-session handling
- server-side authorization/RBAC
- tenant extraction from authenticated identity
- consistent error schema
- validation with Pydantic
- no sensitive secret material in response bodies

## 16. Error and partial-scan behavior

Handle explicitly:
- invalid/expired AWS access
- `AccessDenied` on individual services/resources
- throttling
- unsupported/missing regions
- empty AWS accounts
- no findings
- malformed IAM policies
- large source repositories
- unreadable/binary files
- duplicate findings
- worker failure
- report generation failure

Never fail silently.

A scan with incomplete permissions or failed rules must expose the partial/incomplete state and explain the limitation.

## 17. Reporting and audit trail

Reports should support:
- scan summary
- account/region scope
- severity distribution
- findings
- risk score
- GRC/control status
- remediation status
- partial-scan warnings
- generation timestamp

Planned formats:
- PDF
- CSV
- HTML where useful

Audit logs should capture immutable security-relevant application events such as:
- login/logout
- cloud account onboarding
- scan start/stop
- report creation
- suppression changes
- role/permission changes

Never log secrets or full credentials.

## 18. Architecture

Logical flow:

```text
React + TypeScript + Vite
          |
       FastAPI
          |
 Auth / RBAC / Tenant Context
          |
    Scan Orchestrator
       /    |     \
 AWS      Rules    Secret
Connector Engine   Scanner
       \    |     /
      Finding Normalizer
             |
        Risk Engine
             |
       GRC Control Mapper
             |
     Reports / Dashboard
             |
 PostgreSQL + Worker Queue
```

The AWS connector must be behind a service interface.

The frontend must never call AWS directly.

The rule engine must accept normalized resource data and return deterministic findings.

## 19. Performance requirements

Baseline goals:
- UI remains responsive during scan execution
- scans execute asynchronously for non-trivial environments
- paginated APIs for large datasets
- bounded concurrency for AWS APIs
- exponential backoff on throttling
- idempotent scan jobs where practical
- avoid N+1 database queries
- indexes on tenant, account, scan, rule, severity, status and timestamps
- do not load an entire repository into memory for secret scanning
- provide scan progress/state where feasible

Performance values may be tuned during implementation based on measured results rather than guessed targets.

## 20. Third-party integrations

MVP should minimize external integrations.

Planned/optional integrations:
- AWS IAM/STS APIs
- AWS S3
- AWS EC2/EC2 networking APIs
- AWS CloudTrail
- AWS SQS for production scan jobs
- Slack webhook alerts for critical findings in later prototype/release phases
- GitHub Actions/PR checks in later prototype
- optional AI provider only for non-authoritative explanation/remediation assistance

Do not require external AI to perform core detection.

## 21. MVP boundary

MVP must be a real, usable local product—not a UI mock.

MVP includes:
- React web UI
- FastAPI backend
- persistence
- authentication basics
- AWS read-only connection validation
- scan orchestration
- initial AWS rules
- local secret scanner
- finding normalization
- transparent risk scoring
- basic GRC mapping
- findings UI
- remediation guidance
- scan history
- basic report generation
- automated tests
- safe demo fixtures

Recommended MVP database:
- SQLite for fastest local setup, with repository abstractions and schema designed for PostgreSQL migration.

Do NOT include in V1:
- auto-remediation
- destructive AWS mutations
- multi-cloud
- enterprise SSO
- billing/subscriptions
- compliance certification claims
- autonomous exploitation or penetration testing
- hidden background mutations

## 22. Prototype and later roadmap

### Prototype
After MVP is stable:
- richer dashboard/trends
- scan comparison
- broader AWS rule coverage
- richer GRC matrix
- improved PDF/HTML reporting
- Terraform remediation examples
- GitHub Actions/CI security gates
- PR comments
- Slack alerts
- stronger demo mode

### Later production roadmap
- AWS Organizations/multi-account
- continuous monitoring
- notifications
- enterprise SSO
- organization/project hierarchies
- multi-cloud
- plugin architecture
- approval-based remediation
- advanced resource relationship/attack-path visualization when evidence supports it

## 23. Testing standard

Unit tests required for:
- every security rule
- IAM parsing
- S3 exposure detection
- security-group exposure detection
- CloudTrail posture
- secret detection + redaction
- risk scoring
- GRC mappings
- API authorization
- tenant isolation
- AWS `AccessDenied`
- throttling/retry behavior
- duplicate findings
- partial scans
- “no secrets in logs”

Integration/E2E:
`login → connect account → validate → start scan → inspect findings → compliance → report`

Frontend E2E may use Playwright.
Backend tests use pytest.
Mock AWS APIs for normal unit/integration tests; normal CI must not require a live customer AWS account.

## 24. Implementation phases

Follow sequentially.

### Phase 1 — Project setup
- initialize Vite React frontend
- initialize FastAPI backend
- Docker Compose for local services
- define repository structure
- install/pin dependencies
- establish lint/type/test tooling

### Phase 2 — Database
- implement schema
- Alembic migrations
- PostgreSQL RLS target
- local SQLite compatibility if MVP requires it
- indexes and FK constraints

### Phase 3 — Auth
- registration/login
- Argon2 password hashing
- JWT access/refresh/session flow
- tenant context
- RBAC

### Phase 4 — UI shell
- dark theme
- navigation/sidebar
- shadcn/ui foundation
- empty/loading/error states

### Phase 5 — Cloud onboarding
- account onboarding wizard
- IAM role ARN + ExternalId
- STS AssumeRole validation
- account/region discovery
- sanitized errors

### Phase 6 — Scan engine
- queue/orchestrator
- AWS connectors
- S3/IAM/EC2 networking/CloudTrail rules
- secret scanner
- normalized findings
- partial-scan semantics

### Phase 7 — Dashboard/findings
- TanStack Query hooks
- risk charts
- findings table
- finding drawer
- scan status/history
- GRC view

### Phase 8 — Reporting/integrations
- PDF reporting
- compliance matrix
- CSV/HTML where appropriate
- Slack webhook for critical risks

### Phase 9 — Testing
- pytest
- frontend unit/component tests
- Playwright E2E
- security/privacy tests
- tenant isolation tests

### Phase 10 — Polish/release
- error/empty states
- performance review
- dependency/security review
- Docker/reproducible setup
- deployment preparation
- open-source README/contributing/security policy
- final-year project demo and documentation

Do not implement a later phase while an earlier phase is materially incomplete unless explicitly instructed.

## 25. Demo environment

Maintain safe demo fixtures:
- fake AWS credentials/sentinel secrets
- sample IAM policies
- sample S3 policy/configuration
- sample security-group rules
- simulated CloudTrail posture
- sample findings and GRC mappings

Prefer mocked AWS/LocalStack for demonstrations. Never create intentionally vulnerable resources in a real customer account without explicit, controlled authorization and a separate lab process.

## 26. AI-agent guardrails

Antigravity must:
- treat this file and repository planning docs as project context
- not invent a conflicting stack
- not silently alter architecture
- ask before destructive repository/database changes
- never expose secrets
- never execute generated remediation
- not broaden cloud scope without a documented decision
- make smallest safe assumptions for low-risk ambiguities
- stop and preserve read-only behavior for security-sensitive ambiguity
- update tests with feature changes
- update docs when behavior/architecture changes

When asked to “build the project”, first report:
- current phase
- prerequisites
- files to change
- acceptance criteria
- verification commands

Then implement only that phase.

## 27. Decision tree

**New security check?**
→ add a rule, tests, GRC mapping, remediation, references; do not put detection logic in UI.

**Need AWS access?**
→ use connector/service layer and STS role assumption.

**Need to mutate AWS?**
→ stop; MVP is read-only unless scope is explicitly changed and reviewed.

**Need AI remediation?**
→ generate non-executing guidance only.

**New GRC framework?**
→ add framework/control data and mappings; keep scanner logic unchanged.

**Detected secret?**
→ redact immediately; store metadata, not secret value.

**Scan incomplete?**
→ status `partial`; explain failed permissions/resources.

**Need a new dependency?**
→ justify it, pin it, update documentation/tests, and avoid replacements of required stack without approval.

## 28. Definition of done

A feature is done only when:
- acceptance criteria pass
- relevant unit/integration/E2E tests pass
- type/lint checks pass where configured
- authorization/tenant isolation is enforced
- security/error paths are covered
- no secrets leak into logs/reports/UI
- partial scans are represented correctly
- UI and reports reflect the new behavior
- relevant planning docs are updated
- architecture decisions are recorded
- unrelated files are untouched
- reproducible local setup still works

## 29. Project identity for generated artifacts

Use these defaults unless an approved project document overrides them:

**Product name:** CloudGuard GRC  
**Project title:** Security Auditing GRC Tool for Cloud Infrastructure  
**Primary cloud:** AWS  
**Security mode:** Read-only  
**Primary purpose:** Cloud security auditing + CSPM + GRC automation  
**Future distribution:** Open source  
**Primary build environment:** Antigravity IDE
