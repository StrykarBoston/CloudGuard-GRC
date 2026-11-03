import asyncio
from uuid import uuid4
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db import engine
from app.models import Base

pytestmark = pytest.mark.usefixtures("clean_database_fixture")


@pytest.mark.asyncio
async def test_e2e_audit_workflow(monkeypatch, inline_scan_queue):
    monkeypatch.setattr("app.main.validate_aws_account", lambda *args: None)
    monkeypatch.setattr("app.services.scanner.scan_aws_account", lambda account: ([{
        "rule_id": "aws.iam.root-mfa",
        "service_name": "IAM",
        "resource_arn": f"arn:aws:iam::{account.account_number}:root",
        "region": "global",
        "severity": "CRITICAL",
        "title": "Root MFA is disabled",
        "description": "Test boundary result from the AWS API adapter.",
        "impact": "Privileged account exposure.",
        "controls": ["CIS AWS 1.5"],
        "remediation": {"explanation": "Enable MFA.", "cli": "", "terraform": ""},
        "evidence": {"root_mfa_enabled": False},
        "privilege": True,
    }], []))
    unique_id = uuid4().hex
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register & Login
        res = await client.post("/api/v1/auth/register", json={
            "organization_name": f"__CLOUDGUARD_TEST__:workflow-{unique_id}",
            "full_name": "Test User",
            "email": f"workflow-{unique_id}@example.com",
            "password": "SecurePassword123!"
        })
        if res.status_code != 201:
            print(res.json())
        assert res.status_code == 201

        # 2. Onboard Cloud Account (AWS network boundary is stubbed in this test)
        res = await client.post("/api/v1/cloud-accounts/onboard", json={
            "account_alias": "Prod AWS",
            "account_number": "123456789012",
            "role_arn": "arn:aws:iam::123456789012:role/AuditRole",
            "external_id": "cg-ext-test1234",
        })
        assert res.status_code == 201
        account_id = res.json()["id"]

        # 3. Trigger Scan
        res = await client.post("/api/v1/scans", json={"cloud_account_id": account_id})
        assert res.status_code == 202
        scan_id = res.json()["id"]

        # Wait for scan to complete (background task)
        for _ in range(10):
            await asyncio.sleep(0.5)
            res = await client.get(f"/api/v1/scans/{scan_id}")
            if res.json()["status"] == "completed":
                break
        assert res.json()["status"] == "completed"

        # 4. View Findings
        res = await client.get("/api/v1/findings")
        assert res.status_code == 200
        findings = res.json()
        assert len(findings) > 0
        assert findings[0]["evidence"] == {"root_mfa_enabled": False}

        # Settings, organization metadata, and audit history are tenant-scoped APIs.
        res = await client.get("/api/v1/organization")
        assert res.status_code == 200
        assert res.json()["name"] == f"__CLOUDGUARD_TEST__:workflow-{unique_id}"
        res = await client.put("/api/v1/settings", json={"daily_scans_enabled": True, "daily_scan_hour_utc": 23})
        assert res.status_code == 200
        assert res.json()["daily_scans_enabled"] is True
        assert res.json()["daily_scan_hour_utc"] == 23
        res = await client.get("/api/v1/audit-logs")
        assert res.status_code == 200
        assert any(item["event_type"] == "tenant.settings_updated" for item in res.json())

        # 5. Dashboard & Compliance
        res = await client.get("/api/v1/dashboard")
        assert res.status_code == 200
        dash = res.json()
        assert dash["total_findings"] == len(findings)

        res = await client.get("/api/v1/compliance")
        assert res.status_code == 200
        comp = res.json()
        assert len(comp) == 12
        assert all(framework["score_type"] == "TECHNICAL_POSTURE" for framework in comp)
        assert all(framework["assurance_status"] == "NOT_A_CERTIFICATION" for framework in comp)
        assert any(control["status"] == "NEEDS_REVIEW" for framework in comp for control in framework["controls"])
        assert any(c["status"] == "FAIL" for framework in comp for c in framework["controls"])

        # A framework export must not leak unrelated finding categories into its scope.
        res = await client.get("/api/v1/reports/compliance/gdpr/export")
        assert res.status_code == 200
        assert "Root MFA is disabled" not in res.text
        res = await client.get("/api/v1/reports/compliance/not-a-framework/export")
        assert res.status_code == 404

        # Framework-specific PDF export
        pdf_res = await client.get("/api/v1/reports/compliance/gdpr/export.pdf")
        assert pdf_res.status_code == 200
        assert pdf_res.headers["content-type"] == "application/pdf"
        assert pdf_res.content.startswith(b"%PDF-")
        assert "cloudguard-audit-report-gdpr.pdf" in pdf_res.headers.get("content-disposition", "")

        pdf_404 = await client.get("/api/v1/reports/compliance/not-a-framework/export.pdf")
        assert pdf_404.status_code == 404
