import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db import engine
from app.models import Base

pytestmark = pytest.mark.usefixtures("clean_database_fixture")


@pytest.mark.asyncio
async def test_e2e_audit_workflow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register & Login
        res = await client.post("/api/v1/auth/register", json={
            "organization_name": "Test Org",
            "full_name": "Test User",
            "email": "test@cloudguard.io",
            "password": "SecurePassword123!"
        })
        if res.status_code != 201:
            print(res.json())
        assert res.status_code == 201
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Onboard Cloud Account (Mock STS Validation)
        res = await client.post("/api/v1/cloud-accounts/onboard", headers=headers, json={
            "account_alias": "Prod AWS",
            "account_number": "123456789012",
            "role_arn": "arn:aws:iam::123456789012:role/AuditRole",
            "external_id": "cg-ext-test1234",
            "validation_mode": "local_mock"
        })
        assert res.status_code == 201
        account_id = res.json()["id"]

        # 3. Trigger Scan
        res = await client.post("/api/v1/scans", headers=headers, json={"cloud_account_id": account_id})
        assert res.status_code == 202
        scan_id = res.json()["id"]

        # Wait for scan to complete (background task)
        for _ in range(10):
            await asyncio.sleep(0.5)
            res = await client.get(f"/api/v1/scans/{scan_id}", headers=headers)
            if res.json()["status"] == "completed":
                break
        assert res.json()["status"] == "completed"

        # 4. View Findings
        res = await client.get("/api/v1/findings", headers=headers)
        assert res.status_code == 200
        findings = res.json()
        assert len(findings) > 0

        # 5. Dashboard & Compliance
        res = await client.get("/api/v1/dashboard", headers=headers)
        assert res.status_code == 200
        dash = res.json()
        assert dash["total_findings"] == len(findings)

        res = await client.get("/api/v1/compliance", headers=headers)
        assert res.status_code == 200
        comp = res.json()
        assert len(comp) == 12
        assert all(framework["score_type"] == "TECHNICAL_POSTURE" for framework in comp)
        assert all(framework["assurance_status"] == "NOT_A_CERTIFICATION" for framework in comp)
        assert any(control["status"] == "NEEDS_REVIEW" for framework in comp for control in framework["controls"])
        assert any(c["status"] == "FAIL" for framework in comp for c in framework["controls"])
