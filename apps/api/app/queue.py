from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import get_settings


async def get_queue() -> ArqRedis:
    return await create_pool(RedisSettings.from_dsn(get_settings().redis_url))


async def enqueue_scan(redis: ArqRedis, scan_id: str, tenant_id: str) -> bool:
    job = await redis.enqueue_job(
        "run_scan_job",
        scan_id,
        tenant_id,
        _job_id=f"cloudguard:scan:{scan_id}",
    )
    return job is not None
