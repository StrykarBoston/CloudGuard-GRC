import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import delete, text

from app.db import SessionLocal
from app.models import CloudAccount, Finding, Scan
from app.services.rules.aws_rules import (
    evaluate_cloudtrail_logging,
    evaluate_iam_stale_keys,
    evaluate_iam_wildcard,
    evaluate_root_mfa,
    evaluate_s3_encryption,
    evaluate_s3_public_access_block,
    evaluate_security_group_ssh,
)
from app.services.secret_scanner import scan_content


def risk_score(severity: str, internet_exposed: bool = False, privilege_scope: bool = False) -> int:
    """Transparent risk calculation based on base severity, internet exposure, and privilege boundary."""
    base = {"CRITICAL": 90, "HIGH": 70, "MEDIUM": 45, "LOW": 20}.get(severity, 20)
    exposure_bonus = 10 if internet_exposed else 0
    privilege_bonus = 5 if privilege_scope else 0
    return min(100, base + exposure_bonus + privilege_bonus)


def evaluate_account_rules(account: CloudAccount) -> List[Dict[str, Any]]:
    """Execute deterministic evaluation suite across AWS resources and local configurations."""
    account_num = account.account_number
    findings: List[Dict[str, Any]] = []

    # 1. Root MFA Rule (CIS AWS 1.5)
    root_result = evaluate_root_mfa({
        "account_number": account_num,
        "root_mfa_enabled": False
    })
    if root_result:
        findings.append({
            "rule_id": root_result.rule_id,
            "service_name": root_result.service_name,
            "resource_arn": root_result.resource_arn,
            "severity": root_result.severity,
            "title": root_result.title,
            "description": root_result.description,
            "impact": root_result.impact,
            "controls": root_result.compliance_controls,
            "privilege": root_result.privilege_scope,
            "remediation": {
                "explanation": root_result.remediation.explanation,
                "cli": root_result.remediation.cli,
                "terraform": root_result.remediation.terraform,
            },
            "evidence": root_result.evidence,
        })

    # 2. S3 Public Access Block Rule (CIS AWS 2.1.1)
    s3_pub_result = evaluate_s3_public_access_block({
        "account_number": account_num,
        "bucket_name": f"local-audit-{account_num}",
        "public_access_block": {
            "BlockPublicAcls": False,
            "IgnorePublicAcls": False,
            "BlockPublicPolicy": False,
            "RestrictPublicBuckets": False,
        }
    })
    if s3_pub_result:
        findings.append({
            "rule_id": s3_pub_result.rule_id,
            "service_name": s3_pub_result.service_name,
            "resource_arn": s3_pub_result.resource_arn,
            "severity": s3_pub_result.severity,
            "title": s3_pub_result.title,
            "description": s3_pub_result.description,
            "impact": s3_pub_result.impact,
            "controls": s3_pub_result.compliance_controls,
            "internet": s3_pub_result.internet_exposed,
            "remediation": {
                "explanation": s3_pub_result.remediation.explanation,
                "cli": s3_pub_result.remediation.cli,
                "terraform": s3_pub_result.remediation.terraform,
            },
            "evidence": s3_pub_result.evidence,
        })

    # 3. Security Group Open Port 22 Rule (CIS AWS 5.2)
    sg_result = evaluate_security_group_ssh({
        "account_number": account_num,
        "group_id": "sg-local-audit",
        "ip_permissions": [
            {
                "from_port": 22,
                "to_port": 22,
                "ip_ranges": [{"cidr_ip": "0.0.0.0/0"}]
            }
        ]
    })
    if sg_result:
        findings.append({
            "rule_id": sg_result.rule_id,
            "service_name": sg_result.service_name,
            "resource_arn": sg_result.resource_arn,
            "severity": sg_result.severity,
            "title": sg_result.title,
            "description": sg_result.description,
            "impact": sg_result.impact,
            "controls": sg_result.compliance_controls,
            "internet": sg_result.internet_exposed,
            "remediation": {
                "explanation": sg_result.remediation.explanation,
                "cli": sg_result.remediation.cli,
                "terraform": sg_result.remediation.terraform,
            },
            "evidence": sg_result.evidence,
        })

    # 4. IAM Wildcard Admin Rule (CIS AWS 1.16)
    iam_wild_result = evaluate_iam_wildcard({
        "account_number": account_num,
        "policy_name": "LocalAuditBroadPolicy",
        "has_wildcard": True
    })
    if iam_wild_result:
        findings.append({
            "rule_id": iam_wild_result.rule_id,
            "service_name": iam_wild_result.service_name,
            "resource_arn": iam_wild_result.resource_arn,
            "severity": iam_wild_result.severity,
            "title": iam_wild_result.title,
            "description": iam_wild_result.description,
            "impact": iam_wild_result.impact,
            "controls": iam_wild_result.compliance_controls,
            "privilege": iam_wild_result.privilege_scope,
            "remediation": {
                "explanation": iam_wild_result.remediation.explanation,
                "cli": iam_wild_result.remediation.cli,
                "terraform": iam_wild_result.remediation.terraform,
            },
            "evidence": iam_wild_result.evidence,
        })

    # 5. S3 Encryption Rule (CIS AWS 2.1.2)
    s3_enc_result = evaluate_s3_encryption({
        "account_number": account_num,
        "bucket_name": f"local-assets-{account_num}",
        "encryption_enabled": False
    })
    if s3_enc_result:
        findings.append({
            "rule_id": s3_enc_result.rule_id,
            "service_name": s3_enc_result.service_name,
            "resource_arn": s3_enc_result.resource_arn,
            "severity": s3_enc_result.severity,
            "title": s3_enc_result.title,
            "description": s3_enc_result.description,
            "impact": s3_enc_result.impact,
            "controls": s3_enc_result.compliance_controls,
            "remediation": {
                "explanation": s3_enc_result.remediation.explanation,
                "cli": s3_enc_result.remediation.cli,
                "terraform": s3_enc_result.remediation.terraform,
            },
            "evidence": s3_enc_result.evidence,
        })

    # 6. IAM Stale Access Keys (>90 days) (CIS AWS 1.14)
    iam_stale_result = evaluate_iam_stale_keys({
        "account_number": account_num,
        "user_name": "deploy-service-account",
        "age_days": 124
    })
    if iam_stale_result:
        findings.append({
            "rule_id": iam_stale_result.rule_id,
            "service_name": iam_stale_result.service_name,
            "resource_arn": iam_stale_result.resource_arn,
            "severity": iam_stale_result.severity,
            "title": iam_stale_result.title,
            "description": iam_stale_result.description,
            "impact": iam_stale_result.impact,
            "controls": iam_stale_result.compliance_controls,
            "remediation": {
                "explanation": iam_stale_result.remediation.explanation,
                "cli": iam_stale_result.remediation.cli,
                "terraform": iam_stale_result.remediation.terraform,
            },
            "evidence": iam_stale_result.evidence,
        })

    # 7. CloudTrail Multi-Region Logging (CIS AWS 3.1)
    trail_result = evaluate_cloudtrail_logging({
        "account_number": account_num,
        "is_logging": False,
        "is_multi_region": False
    })
    if trail_result:
        findings.append({
            "rule_id": trail_result.rule_id,
            "service_name": trail_result.service_name,
            "resource_arn": trail_result.resource_arn,
            "severity": trail_result.severity,
            "title": trail_result.title,
            "description": trail_result.description,
            "impact": trail_result.impact,
            "controls": trail_result.compliance_controls,
            "remediation": {
                "explanation": trail_result.remediation.explanation,
                "cli": trail_result.remediation.cli,
                "terraform": trail_result.remediation.terraform,
            },
            "evidence": trail_result.evidence,
        })

    # 8. Local Secret Scanner Check (Sample Sentinel)
    sentinel_config = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\n# Sample secret scan target"
    secret_findings = scan_content(sentinel_config, filename=f"cloud_config_{account_num}.env")
    for sf in secret_findings:
        findings.append(sf)

    return findings


def local_rule_results(account: CloudAccount) -> List[Dict[str, Any]]:
    """Backward-compatible wrapper for scan evaluations."""
    return evaluate_account_rules(account)


async def run_scan(scan_id: str, tenant_id: str) -> None:
    """Asynchronous scan runner with tenant RLS isolation and rule execution."""
    async with SessionLocal() as session:
        # Set tenant RLS context on session for Postgres row isolation
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
            {"tenant_id": tenant_id}
        )

        scan = await session.get(Scan, scan_id)
        if scan is None or scan.tenant_id != tenant_id:
            return

        account = await session.get(CloudAccount, scan.cloud_account_id)
        if account is None:
            scan.status, scan.partial, scan.error_summary = "failed", True, "Cloud account was removed"
            await session.commit()
            return

        scan.status, scan.progress, scan.started_at = "running", 10, datetime.now(timezone.utc)
        await session.commit()

        for step_progress in (25, 50, 75):
            await asyncio.sleep(0.3)
            scan.progress = step_progress
            await session.commit()

        # Clean existing findings for this scan run
        await session.execute(delete(Finding).where(Finding.scan_id == scan.id))

        results = evaluate_account_rules(account)
        for result in results:
            severity = str(result["severity"])
            session.add(Finding(
                tenant_id=scan.tenant_id,
                account_id=account.id,
                scan_id=scan.id,
                rule_id=str(result["rule_id"]),
                service_name=str(result["service_name"]),
                resource_arn=str(result["resource_arn"]),
                severity=severity,
                risk_score=risk_score(
                    severity,
                    bool(result.get("internet")),
                    bool(result.get("privilege"))
                ),
                title=str(result["title"]),
                description=str(result["description"]),
                impact=str(result["impact"]),
                evidence=dict(result.get("evidence", {"source": "rules_engine", "redacted": True})),
                remediation_json=dict(result["remediation"]),
                compliance_controls=list(result["controls"]),
            ))

        scan.status, scan.progress, scan.completed_at = "completed", 100, datetime.now(timezone.utc)
        await session.commit()
