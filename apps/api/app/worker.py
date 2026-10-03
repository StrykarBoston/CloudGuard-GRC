from datetime import UTC, datetime

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select, text

from app.core.config import get_settings
from app.db import SessionLocal
from app.models import CloudAccount, Scan, Tenant, TenantSettings
from app.services.scanner import run_scan

settings = get_settings()


async def run_scan_job(ctx: dict, scan_id: str, tenant_id: str) -> None:
    await run_scan(scan_id, tenant_id)


async def enqueue_due_daily_scans(ctx: dict) -> None:
    now = datetime.now(UTC)
    async with SessionLocal() as session:
        tenant_ids = list((await session.scalars(select(Tenant.id))).all())
        for tenant_id in tenant_ids:
            await session.execute(
                text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
                {"tenant_id": tenant_id},
            )
            schedule = await session.get(TenantSettings, tenant_id)
            if schedule is None or not schedule.daily_scans_enabled:
                await session.rollback()
                continue
            if schedule.daily_scan_hour_utc != now.hour:
                await session.rollback()
                continue
            if schedule.last_scheduled_at and schedule.last_scheduled_at.date() == now.date():
                await session.rollback()
                continue

            accounts = list(
                (
                    await session.scalars(
                        select(CloudAccount).where(
                            CloudAccount.tenant_id == tenant_id,
                            CloudAccount.validation_mode == "aws_sts_readonly",
                            CloudAccount.connection_status == "ACTIVE",
                        )
                    )
                ).all()
            )
            scans = []
            for account in accounts:
                scan = Scan(tenant_id=tenant_id, cloud_account_id=account.id)
                session.add(scan)
                scans.append(scan)
            schedule.last_scheduled_at = now
            await session.commit()
            for scan in scans:
                try:
                    await ctx["redis"].enqueue_job(
                        "run_scan_job",
                        scan.id,
                        tenant_id,
                        _job_id=f"cloudguard:scan:{scan.id}",
                    )
                except Exception:
                    await session.execute(
                        text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
                        {"tenant_id": tenant_id},
                    )
                    failed_scan = await session.get(Scan, scan.id)
                    if failed_scan is None:
                        continue
                    failed_scan.status = "failed"
                    failed_scan.partial = True
                    failed_scan.error_summary = "Could not enqueue scheduled scan."
                    await session.commit()


class WorkerSettings:
    functions = [run_scan_job]
    cron_jobs = [cron(enqueue_due_daily_scans, minute=set(range(60)), unique=True)]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 4
    job_timeout = 60 * 30
    keep_result = 60 * 60
