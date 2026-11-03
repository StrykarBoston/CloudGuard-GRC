# CloudGuard GRC — Actionable Engineering & Audit Backlog (TODO)

**Document Version:** 2.0.0  
**Last Updated:** October 06, 2026  
**Status:** Active  
**Reference:** `.agents/skills/cloudguard-grc-security-auditor/SKILL.md` (Phases 8, 9, 10 & Roadmap)

---

## 1. Immediate Operational Fixes (Priority: High)

- [ ] **TODO-01: Update Docker Compose AWS Credentials Mount for `appuser`**
  - **Component:** `docker-compose.yml`, `apps/api/Dockerfile`
  - **Issue:** Containers run as `appuser`, but credentials are mounted to `/root/.aws:ro`.
  - **Action:**
    - Change mount target to `/home/appuser/.aws:ro` in `docker-compose.yml` for both `api` and `worker` services.
    - Update `AWS_SHARED_CREDENTIALS_FILE: /home/appuser/.aws/credentials` and `AWS_CONFIG_FILE: /home/appuser/.aws/config`.
    - Ensure `apps/api/Dockerfile` creates `/home/appuser/.aws` with appropriate ownership.
  - **Acceptance Criteria:** `appuser` inside `api` and `worker` containers can read host AWS credentials without permission errors.

- [x] **TODO-02: Framework-Scoped PDF Export Endpoint** (Completed: Support both query and path /reports/compliance/{id}/export.pdf with scoped findings & ThreatScore)
  - **Component:** `apps/api/app/main.py`, `apps/api/app/services/pdf_reporter.py`
  - **Action:**
    - Add endpoint `@app.get("/api/v1/reports/compliance/{framework_id}/export.pdf")` (or accept optional query parameter `framework_id: str | None = None` on `/api/v1/reports/export.pdf`).
    - Filter `frameworks` list to the requested framework ID and filter `findings` using `framework_rule_ids(framework_id)`.
    - Return 404 if the framework ID does not exist in `FRAMEWORK_CATALOG`.
  - **Acceptance Criteria:** Downloading a PDF for CIS AWS Foundations contains only CIS controls and mapped findings.

- [ ] **TODO-03: Resolve Ruff Lint Warnings in Test Suite**
  - **Component:** `apps/api/tests/`
  - **Action:**
    - Run `ruff check . --fix` in `apps/api`.
    - Format imports and shorten long test assertion strings in `test_tenant_isolation.py` and `test_workflow.py`.
  - **Acceptance Criteria:** `ruff check .` returns 0 errors.

---

## 2. Team Member Workstream Allocations (Priority: Medium)

### Team Member 1 — DevOps & Production Infrastructure (Phase 10)
- [ ] **TODO-04: Terraform Infrastructure as Code (IaC) for AWS**
  - **Files to create:** `terraform/main.tf`, `terraform/vpc.tf`, `terraform/ecs.tf`, `terraform/rds.tf`, `terraform/redis.tf`
  - **Deliverable:**
    - Modular VPC (public subnets for ALB, private subnets for ECS and RDS).
    - AWS RDS PostgreSQL 15 instance with automatic backups and encryption at rest.
    - AWS ElastiCache Redis cluster for ARQ queue.
    - AWS ECS Fargate task definitions for `api` and `worker` services.
    - Application Load Balancer (ALB) with HTTPS listener and ACM certificate integration.
- [ ] **TODO-05: GitHub Actions CI/CD Pipeline**
  - **Files to create:** `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`
  - **Deliverable:**
    - Automated pipeline running on Pull Requests: Pytest unit tests, Ruff linting, TypeScript build (`tsc -b`), and Docker image build verification.
    - Deployment workflow pushing Docker images to AWS ECR and updating ECS Fargate services.

---

### Team Member 2 — Backend & Third-Party Integrations (Phase 8)
- [ ] **TODO-06: Jira REST API Integration for Finding Triage**
  - **Files to touch:** `apps/api/app/main.py`, `apps/api/app/services/jira.py`, `apps/api/app/schemas.py`
  - **Deliverable:**
    - Endpoint `POST /api/v1/findings/{id}/jira-issue` creating an issue in the customer's Jira Cloud project.
    - Include finding severity, description, affected resource ARN, and remediation steps in the Jira issue body.
    - Store external Jira issue URL/key on the finding metadata.
- [ ] **TODO-07: Email Notification Service via AWS SES / SendGrid**
  - **Files to touch:** `apps/api/app/services/email_notifications.py`, `apps/api/app/worker.py`
  - **Deliverable:**
    - Send scheduled daily or weekly email posture summaries to tenant administrators.
    - HTML email template displaying ThreatScore, newly detected critical findings, and compliance status.
- [ ] **TODO-08: Persistent Secret Scanner Findings**
  - **Files to touch:** `apps/api/app/main.py`, `apps/api/app/services/secret_scanner.py`
  - **Deliverable:**
    - Option in `POST /api/v1/scans/secrets` to persist detected secrets as finding records in the `findings` table under service name `"Secrets"`.

---

### Team Member 3 — Frontend & Automated QA (Phase 9)
- [ ] **TODO-09: Playwright Browser End-to-End Test Suite**
  - **Files to touch:** `apps/web/playwright.config.ts`, `apps/web/e2e/auth.spec.ts`, `apps/web/e2e/onboarding.spec.ts`, `apps/web/e2e/findings.spec.ts`
  - **Deliverable:**
    - End-to-end browser tests verifying:
      1. User registration, login, and session restoration.
      2. Cloud account onboarding wizard with ExternalId copy action.
      3. Dashboard metrics display and navigation to findings.
      4. Finding detail drawer slide-over, ownership assignment, and status updates (Suppress/Resolve).
      5. Compliance matrix view and HTML/PDF report triggers.
- [ ] **TODO-10: Frontend Jira Ticket Action Button**
  - **Files to touch:** `apps/web/src/pages/FindingsExplorer.tsx`, `apps/web/src/services/api.ts`
  - **Deliverable:**
    - "Create Jira Ticket" button in the Finding Detail Drawer footer.
    - Displays modal to select Jira project/issue type or confirms creation with direct link to Jira ticket.
- [ ] **TODO-11: Framework PDF Export Dropdown**
  - **Files to touch:** `apps/web/src/pages/ComplianceMatrix.tsx`, `apps/web/src/services/api.ts`
  - **Deliverable:**
    - Export button dropdown offering "Export HTML Report" and "Export Audit PDF" for the selected framework.

---

## 3. Future Prototype & V2 Roadmap (Priority: Low)

- [ ] **TODO-12: Multi-Cloud Expansion (Azure & GCP)**
  - Integrate Azure Service Principal credential validation and Azure Resource Graph API.
  - Integrate GCP Service Account validation and Cloud Asset Inventory API.
- [ ] **TODO-13: AWS Organizations Multi-Account Discovery**
  - Connect AWS Organizations management account via delegated admin role to automatically discover and audit child AWS accounts.
- [ ] **TODO-14: Event-Driven Near-Real-Time Auditing**
  - Ingest AWS EventBridge / CloudTrail events via SQS to trigger incremental scans upon security group or S3 policy changes.
- [ ] **TODO-15: Attack Path Graph Visualization**
  - Graph-based visualization of IAM principal permissions leading to exposed resources.

