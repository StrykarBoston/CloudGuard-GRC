import pytest_asyncio
from app.db import engine
from app.models import Finding, Scan, Session, AuditLog, User, CloudAccount, Tenant
from sqlalchemy import delete


@pytest_asyncio.fixture(autouse=True)
async def clean_database_fixture():
    # Clear connection pool before test so a fresh connection is bound to current loop
    await engine.dispose()
    async with engine.begin() as conn:
        for table in [Finding, Scan, Session, AuditLog, User, CloudAccount, Tenant]:
            await conn.execute(delete(table))
    yield
    async with engine.begin() as conn:
        for table in [Finding, Scan, Session, AuditLog, User, CloudAccount, Tenant]:
            await conn.execute(delete(table))
    # Dispose pool upon loop termination
    await engine.dispose()

