import asyncio
from uuid import uuid4
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db import engine

pytestmark = pytest.mark.usefixtures("clean_database_fixture")




@pytest.mark.asyncio
async def test_tenant_rls_isolation(monkeypatch, inline_scan_queue):
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
    async with (
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client_a,
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client_b,
    ):
        # 1. Register Tenant A
        res_a = await client_a.post("/api/v1/auth/register", json={
            "organization_name": f"__CLOUDGUARD_TEST__:alpha-{unique_id}",
            "full_name": "Alpha Admin",
            "email": f"alpha-{unique_id}@example.com",
            "password": "AlphaPassword123!"
        })
        assert res_a.status_code == 201

        # Onboard account for Tenant A
        res_acc_a = await client_a.post("/api/v1/cloud-accounts/onboard", json={
            "account_alias": "Alpha AWS Production",
            "account_number": "111111111111",
            "role_arn": "arn:aws:iam::111111111111:role/AlphaAuditRole",
            "external_id": "cg-ext-alpha",
        })
        assert res_acc_a.status_code == 201
        account_id_a = res_acc_a.json()["id"]

        # Run scan for Tenant A
        res_scan_a = await client_a.post("/api/v1/scans", json={"cloud_account_id": account_id_a})
        assert res_scan_a.status_code == 202
        scan_id_a = res_scan_a.json()["id"]

        for _ in range(15):
            await asyncio.sleep(0.3)
            status_res = await client_a.get(f"/api/v1/scans/{scan_id_a}")
            if status_res.json()["status"] == "completed":
                break

        # Tenant A verifies findings exist
        res_find_a = await client_a.get("/api/v1/findings")
        findings_a = res_find_a.json()
        assert len(findings_a) > 0
        finding_id_a = findings_a[0]["id"]

        # 2. Register Tenant B (Separate Company)
        res_b = await client_b.post("/api/v1/auth/register", json={
            "organization_name": f"__CLOUDGUARD_TEST__:beta-{unique_id}",
            "full_name": "Beta Security",
            "email": f"beta-{unique_id}@example.com",
            "password": "BetaPassword123!"
        })
        assert res_b.status_code == 201

        # 3. Security Audit Checks:
        # Check A: Tenant B querying findings must return EMPTY list (cannot see Tenant A findings)
        res_find_b = await client_b.get("/api/v1/findings")
        assert res_find_b.status_code == 200
        findings_b = res_find_b.json()
        assert len(findings_b) == 0, "Security Violation: Tenant B saw findings belonging to Tenant A!"

        # Check B: Tenant B querying cloud accounts must return EMPTY list (cannot see Tenant A accounts)
        res_acc_b = await client_b.get("/api/v1/cloud-accounts")
        assert res_acc_b.status_code == 200
        accounts_b = res_acc_b.json()
        assert len(accounts_b) == 0, "Security Violation: Tenant B saw cloud accounts belonging to Tenant A!"

        # Check C: Tenant B attempting to suppress or update Tenant A's finding by direct ID
        res_hack = await client_b.patch(f"/api/v1/findings/{finding_id_a}", json={"status": "RESOLVED"})
        assert res_hack.status_code == 404, "Security Violation: Tenant B was able to modify Tenant A's finding!"

        # Check D: Tenant A's finding remains unmodified and open
        res_verify_a = await client_a.get("/api/v1/findings")
        assert res_verify_a.json()[0]["status"] == "OPEN"
