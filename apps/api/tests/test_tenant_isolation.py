import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db import engine




@pytest.mark.asyncio
async def test_tenant_rls_isolation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register Tenant A
        res_a = await client.post("/api/v1/auth/register", json={
            "organization_name": "Tenant Alpha Corp",
            "full_name": "Alpha Admin",
            "email": "admin@alpha.io",
            "password": "AlphaPassword123!"
        })
        assert res_a.status_code == 201
        token_a = res_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Onboard account for Tenant A
        res_acc_a = await client.post("/api/v1/cloud-accounts/onboard", headers=headers_a, json={
            "account_alias": "Alpha AWS Production",
            "account_number": "111111111111",
            "role_arn": "arn:aws:iam::111111111111:role/AlphaAuditRole",
            "external_id": "cg-ext-alpha",
            "validation_mode": "local_mock"
        })
        assert res_acc_a.status_code == 201
        account_id_a = res_acc_a.json()["id"]

        # Run scan for Tenant A
        res_scan_a = await client.post("/api/v1/scans", headers=headers_a, json={"cloud_account_id": account_id_a})
        assert res_scan_a.status_code == 202
        scan_id_a = res_scan_a.json()["id"]

        for _ in range(15):
            await asyncio.sleep(0.3)
            status_res = await client.get(f"/api/v1/scans/{scan_id_a}", headers=headers_a)
            if status_res.json()["status"] == "completed":
                break

        # Tenant A verifies findings exist
        res_find_a = await client.get("/api/v1/findings", headers=headers_a)
        findings_a = res_find_a.json()
        assert len(findings_a) > 0
        finding_id_a = findings_a[0]["id"]

        # 2. Register Tenant B (Separate Company)
        res_b = await client.post("/api/v1/auth/register", json={
            "organization_name": "Tenant Beta LLC",
            "full_name": "Beta Security",
            "email": "secops@beta.io",
            "password": "BetaPassword123!"
        })
        assert res_b.status_code == 201
        token_b = res_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 3. Security Audit Checks:
        # Check A: Tenant B querying findings must return EMPTY list (cannot see Tenant A findings)
        res_find_b = await client.get("/api/v1/findings", headers=headers_b)
        assert res_find_b.status_code == 200
        findings_b = res_find_b.json()
        assert len(findings_b) == 0, "Security Violation: Tenant B saw findings belonging to Tenant A!"

        # Check B: Tenant B querying cloud accounts must return EMPTY list (cannot see Tenant A accounts)
        res_acc_b = await client.get("/api/v1/cloud-accounts", headers=headers_b)
        assert res_acc_b.status_code == 200
        accounts_b = res_acc_b.json()
        assert len(accounts_b) == 0, "Security Violation: Tenant B saw cloud accounts belonging to Tenant A!"

        # Check C: Tenant B attempting to suppress or update Tenant A's finding by direct ID
        res_hack = await client.patch(f"/api/v1/findings/{finding_id_a}", headers=headers_b, json={"status": "RESOLVED"})
        assert res_hack.status_code == 404, "Security Violation: Tenant B was able to modify Tenant A's finding!"

        # Check D: Tenant A's finding remains unmodified and open
        res_verify_a = await client.get("/api/v1/findings", headers=headers_a)
        assert res_verify_a.json()[0]["status"] == "OPEN"
