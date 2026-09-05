# CloudGuard GRC: Comprehensive Summary & Build Plan

## Part 1: Executive Summary of Understanding

### Core Purpose & Value Proposition
CloudGuard GRC is an open-source, agentless Cloud Security Posture Management (CSPM) and GRC automation platform initially targeting AWS. Its primary value proposition is to automate the discovery of cloud misconfigurations, exposed secrets, and security gaps; prioritize these risks using a ThreatScore; map them to established compliance frameworks (CIS, DPDPA, GDPR, ISO 27001); and provide safe, actionable remediation guidance (Terraform/CLI snippets). It offers organizations continuous, automated visibility and audit evidence without requiring mutation access to their environments.

### Target Users & Primary Workflows
- **Security & Cloud Engineers:** Onboard cloud accounts securely via IAM role assumption (STS), trigger/schedule scans, and triage prioritized risks to harden the cloud environment.
- **DevOps & Developers:** Use clear, non-executing remediation guidance (Terraform/CLI) to implement fixes locally or in CI/CD pipelines.
- **Auditors & Compliance Officers:** Export audit-ready PDF/CSV reports mapping technical findings to compliance controls.
- **Super Admins:** Manage multi-tenant organizations, access controls (RBAC), and subscription tiers.

### Key Functional Modules
1. **Authentication & Multi-Tenancy:** Secure JWT-based access with strict PostgreSQL Row-Level Security (RLS) tenant isolation.
2. **AWS Connector & Scanner:** Asynchronous, read-only scanning engine utilizing AWS STS and boto3.
3. **Security Rules & Secret Detection:** Deterministic evaluation of IAM, S3, EC2, and CloudTrail configurations, alongside local/repo secret scanning.
4. **Risk & GRC Mapping Engine:** Normalizes findings, calculates ThreatScores, and maps technical violations to framework controls.
5. **Dashboard & Remediation UI:** High-density, dark-mode interface for rapid risk triage with step-by-step fix drawers.
6. **Reporting & Audit Logging:** Immutable system action logs and compliance report generation.

### Technology Stack & Architecture
- **Frontend:** React 18+ (Vite, TypeScript), TailwindCSS, shadcn/ui, Zustand, TanStack Query, Recharts.
- **Backend:** Python 3.11+, FastAPI, Pydantic, SQLAlchemy 2.0 (Async), boto3, PyJWT, Passlib (Argon2).
- **Database:** PostgreSQL 15+ (with RLS) via Alembic. (SQLite permissible only for local MVP testing).
- **Architecture Style:** Service-oriented/Serverless-compatible (AWS SQS, Lambda/ECS Fargate) with a strict separation between API, rules engine, and scan orchestration.

### Security, Compliance, & Audit Requirements
- **Strict Read-Only Access:** 100% agentless via STS `AssumeRole` with `ExternalId` (Confused Deputy protection). No automatic mutation of cloud resources.
- **Data Protection:** Encryption at rest and in transit. No hardcoded keys. Secrets detected in scans must be redacted and never stored in full.
- **Tenant Isolation:** Enforced via RLS in PostgreSQL and context injection in FastAPI middleware.
- **Audit Trails:** Immutable logging of all user and system actions.

---

## Part 2: Gap Analysis & Missing Details

> [!WARNING]
> Several critical ambiguities and contradictions exist between the provided documents that require clarification before execution.

### 1. Ambiguities & Inconsistencies
- **Local Secret Scanning vs. SaaS Agentless Model:** The `SKILL.md` emphasizes a "Local secret scanner" that scans the "user's local project/source tree, not their live AWS data". However, the PRD and Architecture describe a centralized SaaS platform scanning connected cloud accounts. *Question: Should the secret scanner be built as a separate local CLI tool, or does the SaaS platform connect to GitHub/GitLab repositories to perform this scan?*
- **Database Schema vs. SKILL.md:** The `Backend Schema Document` defines 7 tables (Tenants, Users, Sessions, CloudAccounts, Scans, Findings, AuditLogs). However, `SKILL.md` references additional critical tables: `rules`, `grc_frameworks`, `grc_controls`, `finding_control_mappings`, and `reports`. *Question: Should I expand the canonical backend schema to explicitly include these missing GRC and Rule tables?*
- **Billing & Subscriptions:** The `App Flow Document` maps out an upgrade journey via Stripe checkout. The database schema only holds a `subscription_plan` string, lacking Stripe Customer IDs, payment history, and webhook sync metadata. *Question: Should Stripe schema integration be added, or is billing deferred to a later phase?*

### 2. Missing Technical Specifications
- **Rules Engine Execution:** The documents mention native Python rules and OPA/Rego. It is unclear if OPA is a hard requirement for the MVP or if native Python evaluation is sufficient. *Assumption: Native Python is sufficient for MVP to maintain simplicity.*
- **ThreatScore Algorithm:** The exact mathematical formula and weights for the 0-100 ThreatScore calculation are not defined.
- **Scan Pagination & Memory Limits:** While pagination is mentioned, handling massive AWS accounts (e.g., thousands of IAM roles) may exceed memory if not streamed properly to the DB.

---

## Part 3: Phased Build Plan Aligned with MVP → Prototype → Final Product

> [!NOTE]
> This macro-plan aligns the 10 micro-phases from the `Implementation Plan Document` with the rigid Guardrails and Definition of Done established in `SKILL.md`.

### Phase 1: Minimum Viable Product (MVP)
**Goal:** Deliver a secure, localized, and verifiable read-only scanning platform demonstrating core end-to-end value on a single AWS account.

- **Scope & Features:**
  - Full project skeleton (Vite/React + FastAPI).
  - PostgreSQL database with Alembic migrations and RLS implemented.
  - JWT Authentication, RBAC basics, and Tenant context middleware.
  - Basic SaaS shell UI (Dark Mode, shadcn/ui components).
  - AWS Onboarding (IAM Role + ExternalId validation).
  - Synchronous or simple background scan engine for deterministic S3, IAM, and EC2 checks (CIS benchmarks).
  - Risk scoring and finding normalization (displaying Terraform/CLI remediation).
- **Deliverables & Acceptance Criteria:**
  - Runnable Docker Compose setup.
  - User can log in, add a read-only AWS role, trigger a scan, and view findings with remediation code.
  - Tests verify tenant isolation (RLS) and AWS `AssumeRole` logic using mocked LocalStack credentials.
- **SKILL.md Alignment:** Strictly adheres to read-only rules, no AWS mutation, redacted secrets, and clear separation of rules from the UI.
- **Complexity & Risks:** High complexity in setting up RLS correctly and ensuring robust boto3 STS logic. 

### Phase 2: Prototype (Expanded Features)
**Goal:** Scale the MVP into a comprehensive GRC tool with broader rule coverage, compliance mapping, asynchronous scale, and automated reporting.

- **Scope & Features:**
  - Asynchronous task orchestration (Celery/Redis or SQS) for parallel cloud account scanning.
  - Expanded Ruleset (CloudTrail, KMS, advanced networking).
  - Formal GRC Mapping Engine connecting findings to CIS, DPDPA, and GDPR controls.
  - Interactive UI enhancements: GRC Compliance Matrix views, detailed filtering, and suppression workflows.
  - Report Generation API (WeasyPrint) for exporting PDF/CSV executive audits.
  - Initial integrations (Slack webhook alerts for critical findings).
- **Deliverables & Acceptance Criteria:**
  - App can reliably scan multiple accounts asynchronously without blocking the API.
  - Users can generate and download a PDF compliance report.
  - Dashboard analytics (donut charts, ThreatScore gauges) render live DB data accurately.
- **SKILL.md Alignment:** Implements the "Prototype and later roadmap" directives including richer dashboards, reporting, and decoupled asynchronous background workers.
- **Complexity & Risks:** Medium complexity. Risk of AWS rate limiting (throttling); requires robust exponential backoff and pagination in the scan engine.

### Phase 3: Final Product (Advanced Features)
**Goal:** Enterprise hardening, deployment readiness, continuous monitoring, and CI/CD/AI integrations.

- **Scope & Features:**
  - Infrastructure-as-Code (Terraform) for AWS production deployment (ECS Fargate, RDS, CloudFront).
  - GitHub Actions CI/CD pipelines with zero-downtime deployment.
  - Local/CI Secret Scanning integration (CLI or GitHub App hooks).
  - Advanced Integrations (Jira ticketing, SNS alerts).
  - Implementation of "Optional AI": Integration with an LLM provider to offer dynamic, non-authoritative explanations for complex architectural findings (never auto-executing).
  - Billing flow integration (Stripe) for multi-account unlocking.
- **Deliverables & Acceptance Criteria:**
  - Production-ready cloud deployment.
  - Automated CI/CD pipeline achieving >80% test coverage.
  - Application gracefully handles API throttling, partial scans, and multi-tenant scaling.
- **SKILL.md Alignment:** Meets the stringent "Definition of Done" for deployment, strictly isolating AI from authoritative detection logic, and ensuring partial scans are handled without silent failures.
- **Complexity & Risks:** High complexity in DevOps and production networking. Risk of unexpected AWS costs if scan loops are not managed properly.

---

## Next Steps & User Review Required
Please review the Gap Analysis (Part 2). Specifically, I need your guidance on:
1. Should I immediately update the database schema plan to include the GRC (`grc_frameworks`, `grc_controls`) tables mentioned in `SKILL.md`?
2. Does the "Local Secret Scanner" refer to a CLI tool, or should we focus strictly on the cloud-connected SaaS features for Phase 1?
3. Should we proceed with Phase 1 (MVP) initialization?
