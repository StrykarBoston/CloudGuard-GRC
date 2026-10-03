import asyncio
from datetime import UTC, datetime

from app.db import SessionLocal
from app.models import CloudAccount, Finding, Scan, TenantSettings
from app.services.aws_auditor import AwsAuditError, scan_aws_account
from app.services.alerting import dispatch_critical_alerts
from app.core.config import get_settings
from sqlalchemy import delete, text


def risk_score(severity: str, internet_exposed: bool = False, privilege_scope: bool = False) -> int:
    """Score severity with internet exposure and privilege bonuses."""
    base = {"CRITICAL": 90, "HIGH": 70, "MEDIUM": 45, "LOW": 20}.get(severity, 20)
    exposure_bonus = 10 if internet_exposed else 0
    privilege_bonus = 5 if privilege_scope else 0
    return min(100, base + exposure_bonus + privilege_bonus)


async def run_scan(scan_id: str, tenant_id: str) -> None:
    """Asynchronous scan runner with tenant RLS isolation and rule execution."""
    async with SessionLocal() as session:
        # Set tenant RLS context on session for Postgres row isolation
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
            {"tenant_id": tenant_id},
        )

        scan = await session.get(Scan, scan_id)
        if scan is None or scan.tenant_id != tenant_id:
            return

        account = await session.get(CloudAccount, scan.cloud_account_id)
        if account is None:
            scan.status, scan.partial, scan.error_summary = (
                "failed",
                True,
                "Cloud account was removed",
            )
            await session.commit()
            return

        scan.status, scan.progress, scan.started_at = "running", 10, datetime.now(UTC)
        await session.commit()
        if account.validation_mode != "aws_sts_readonly":
            scan.status, scan.partial = "failed", True
            scan.error_summary = (
                "This account used removed simulator mode; reconnect it through AWS STS."
            )
            await session.commit()
            return

        try:
            results, errors = await asyncio.to_thread(scan_aws_account, account)
        except AwsAuditError as exc:
            scan.status, scan.partial = "failed", True
            scan.error_summary = str(exc)[:2000]
            await session.commit()
            return
        except Exception as exc:
            scan.status, scan.partial = "failed", True
            scan.error_summary = f"Unexpected AWS scan failure ({type(exc).__name__})"
            await session.commit()
            return

        await session.execute(delete(Finding).where(Finding.scan_id == scan.id))
        for result in results:
            severity = str(result["severity"])
            session.add(
                Finding(
                    tenant_id=scan.tenant_id,
                    account_id=account.id,
                    scan_id=scan.id,
                    rule_id=str(result["rule_id"]),
                    service_name=str(result["service_name"]),
                    resource_arn=str(result["resource_arn"]),
                    region=str(result.get("region", "global")),
                    severity=severity,
                    risk_score=risk_score(
                        severity, bool(result.get("internet")), bool(result.get("privilege"))
                    ),
                    title=str(result["title"]),
                    description=str(result["description"]),
                    impact=str(result["impact"]),
                    evidence=dict(result.get("evidence", {"redacted": True})),
                    remediation_json=dict(result["remediation"]),
                    compliance_controls=list(result["controls"]),
                )
            )

        scan.status, scan.progress, scan.partial = "completed", 100, bool(errors)
        scan.error_summary = "; ".join(errors[:12])[:2000] if errors else None
        scan.completed_at = datetime.now(UTC)
        await session.commit()

        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
            {"tenant_id": tenant_id},
        )
        settings = get_settings()
        tenant_settings = await session.get(TenantSettings, tenant_id)
        if tenant_settings and tenant_settings.slack_alerts_enabled and settings.slack_webhook_url:
            alert_findings = [
                {**result, "compliance_controls": result.get("controls", [])}
                for result in results
            ]
            await dispatch_critical_alerts(settings.slack_webhook_url, alert_findings)
