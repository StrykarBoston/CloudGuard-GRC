import pytest
import pytest_asyncio
from app.db import engine
from app.models import Tenant
from sqlalchemy import delete


@pytest_asyncio.fixture
async def clean_database_fixture():
    await engine.dispose()
    async with engine.begin() as conn:
        await conn.execute(delete(Tenant).where(Tenant.name.like("__CLOUDGUARD_TEST__:%")))
    try:
        from app.core.config import get_settings
        import redis.asyncio as aioredis
        r = aioredis.from_url(get_settings().redis_url)
        await r.flushdb()
        await r.aclose()
    except Exception:
        pass
    yield
    async with engine.begin() as conn:
        await conn.execute(delete(Tenant).where(Tenant.name.like("__CLOUDGUARD_TEST__:%")))
    try:
        from app.core.config import get_settings
        import redis.asyncio as aioredis
        r = aioredis.from_url(get_settings().redis_url)
        await r.flushdb()
        await r.aclose()
    except Exception:
        pass
    await engine.dispose()



@pytest.fixture
def inline_scan_queue(monkeypatch):
    from app.services.scanner import run_scan

    class QueueStub:
        async def aclose(self):
            return None

    async def get_queue():
        return QueueStub()

    async def enqueue(redis, scan_id: str, tenant_id: str) -> bool:
        await run_scan(scan_id, tenant_id)
        return True

    monkeypatch.setattr("app.main.get_queue", get_queue)
    monkeypatch.setattr("app.main.enqueue_scan", enqueue)

