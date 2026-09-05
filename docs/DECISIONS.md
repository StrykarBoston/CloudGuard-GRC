# Architecture decisions

## 2026-09-05 — Phase 1 local development baseline

**Decision:** Use the required dual-directory repository layout: `apps/web` for the React/Vite client and `apps/api` for the FastAPI service. Docker Compose provisions PostgreSQL 15, Redis 7, and LocalStack for local-only emulation.

**Rationale:** This matches the approved technical plan while keeping the scan engine, database migrations, and production worker choices open for their designated later phases.

**Security impact:** No application service contains AWS credentials. LocalStack is isolated to the development environment, and no AWS API calls or cloud mutations are implemented in Phase 1.

## 2026-09-05 — API health contract

**Decision:** Expose an unauthenticated `GET /health` endpoint returning service name, environment, and status only.

**Rationale:** Docker and deployment probes require a low-risk readiness signal before authentication and database migrations are introduced in later phases.

## 2026-09-05 — Stitch MCP UI/UX system & design token integration

**Decision:** Ported Stitch MCP Project `9613006758110477400` design specifications, typography (`Space Grotesk` headlines, `Inter` body), and dark-mode cyber palette (`#00D4FF` primary, `#090d16` canvas, `#0e1417` / `#131c2e` surfaces) into `apps/web`. Implemented the full suite of client views: `AppShell`, `AuthLayout`, `Login`, `Register`, `Dashboard`, `FindingsExplorer` with sliding `FindingDetailDrawer`, `ComplianceMatrix`, `AccountOnboarding`, `Accounts`, and `Settings`.

**Rationale:** Aligns the live React frontend with the pre-built visual specifications created in Stitch MCP and the repository's `UI_UX Design Brief`, while preserving strict read-only boundaries and preventing AWS secret leakage.

**Security impact:** Frontend is strictly read-only and uses non-executing guidance for remediation (Terraform and AWS CLI snippets). No AWS credentials, root tokens, or boto3 calls exist in browser code. Cross-account IAM role assumption supports external ID parameters.

