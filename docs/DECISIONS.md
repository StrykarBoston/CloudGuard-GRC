# Architecture decisions

## 2026-09-05 — Phase 1 local development baseline

**Decision:** Use the required dual-directory repository layout: `apps/web` for the React/Vite client and `apps/api` for the FastAPI service. The original local-emulation phase used PostgreSQL 15, Redis 7, and LocalStack; that simulator runtime has since been removed.

**Rationale:** This matches the approved technical plan while keeping the scan engine, database migrations, and production worker choices open for their designated later phases.

**Security impact:** This was a historical Phase 1 decision. The current AWS path uses runtime credentials and STS AssumeRole as recorded in the 2026-10-01 decision below.

## 2026-10-01 — Replace LocalStack runtime with live read-only AWS access

**Decision:** Remove LocalStack from the default Compose stack. The API uses the AWS SDK credential provider chain to assume a customer IAM role with an STS ExternalId, accepts only SecurityAudit and optional ViewOnlyAccess policies, and performs read-only inventory calls.

**Rationale:** Replace synthetic runtime findings with evidence collected from AWS. Unit tests stub only the AWS network boundary; runtime onboarding and scans do not generate mock findings.

**Security impact:** AWS credentials remain with the API runtime and are not accepted from the browser or stored in PostgreSQL. The API obtains temporary STS credentials for validation and scans. The policy allowlist is a guardrail and does not replace independent IAM review.

## 2026-09-05 — API health contract

**Decision:** Expose an unauthenticated `GET /health` endpoint returning service name, environment, and status only.

**Rationale:** Docker and deployment probes require a low-risk readiness signal before authentication and database migrations are introduced in later phases.

## 2026-10-03 — Phase 2 tenant-scoped operational controls

**Decision:** Settings, organization metadata, organization-user lookup, audit history, and cloud-account lifecycle operations are exposed through tenant-scoped API routes. Account removal requires an administrative role, is confirmed in the UI, and writes an audit event before removal.

**Rationale:** Operations screens must use authenticated server data rather than client-side placeholders while preserving the database and application tenant boundary.

**Security impact:** Assignment changes validate the assignee belongs to the current tenant. Evidence is returned only from the finding record, whose scanner contract requires redaction. Cloud-account removal never issues an AWS mutation; it only removes CloudGuard's local connection metadata and related local scan records.

## 2026-10-03 — Framework report scoping

**Decision:** A report requested for a framework includes only that framework's control model and rule-mapped open findings; unknown framework IDs return 404.

**Rationale:** A framework-specific export must not present unrelated technical evidence as if it were in scope.

## 2026-09-05 — Stitch MCP UI/UX system & design token integration

**Decision:** Ported Stitch MCP Project `9613006758110477400` design specifications, typography (`Space Grotesk` headlines, `Inter` body), and dark-mode cyber palette (`#00D4FF` primary, `#090d16` canvas, `#0e1417` / `#131c2e` surfaces) into `apps/web`. Implemented the full suite of client views: `AppShell`, `AuthLayout`, `Login`, `Register`, `Dashboard`, `FindingsExplorer` with sliding `FindingDetailDrawer`, `ComplianceMatrix`, `AccountOnboarding`, `Accounts`, and `Settings`.

**Rationale:** Aligns the live React frontend with the pre-built visual specifications created in Stitch MCP and the repository's `UI_UX Design Brief`, while preserving strict read-only boundaries and preventing AWS secret leakage.

**Security impact:** Frontend is strictly read-only and uses non-executing guidance for remediation (Terraform and AWS CLI snippets). No AWS credentials, root tokens, or boto3 calls exist in browser code. Cross-account IAM role assumption supports external ID parameters.

