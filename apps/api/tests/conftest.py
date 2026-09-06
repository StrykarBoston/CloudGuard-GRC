import pytest_asyncio
from app.db import engine
from app.models import Finding, Scan, Session, AuditLog, User, CloudAccount, Tenant
from sqlalchemy import delete


@pytest_asyncio.fixture(autouse=True)
async def clean_database_fixture():
    # Clear connection pool before test so a fresh connection is bound to current loop
    await engine.dispose()
    preserved_emails = ["konaapvt@gmail.com", "alexsirin455@gmail.com", "admin@cloudguard.io"]
    preserved_tenants = ["konaaa", "Alex Security Org", "CloudGuard Security"]
    async with engine.begin() as conn:
        for table in [Finding, Scan, Session, AuditLog, CloudAccount]:
            await conn.execute(delete(table))
        await conn.execute(delete(User).where(~User.email.in_(preserved_emails)))
        await conn.execute(delete(Tenant).where(~Tenant.name.in_(preserved_tenants)))
    yield
    async with engine.begin() as conn:
        for table in [Finding, Scan, Session, AuditLog, CloudAccount]:
            await conn.execute(delete(table))
        await conn.execute(delete(User).where(~User.email.in_(preserved_emails)))
        await conn.execute(delete(Tenant).where(~Tenant.name.in_(preserved_tenants)))
    await engine.dispose()

