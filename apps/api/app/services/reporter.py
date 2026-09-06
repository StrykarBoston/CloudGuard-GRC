from datetime import datetime, timezone
from html import escape
from typing import Any, Dict, List


def generate_executive_html_report(
    organization_name: str,
    threat_score: int,
    risk_level: str,
    accounts: List[Any],
    frameworks: List[Any],
    findings: List[Any],
    generated_at: datetime | None = None
) -> str:
    """Generate a printable HTML executive compliance audit report."""
    if generated_at is None:
        generated_at = datetime.now(timezone.utc)
    date_str = generated_at.strftime("%B %d, %Y - %H:%M UTC")

    # Severity counts
    critical_count = sum(1 for f in findings if getattr(f, "severity", "") == "CRITICAL")
    high_count = sum(1 for f in findings if getattr(f, "severity", "") == "HIGH")
    med_count = sum(1 for f in findings if getattr(f, "severity", "") == "MEDIUM")
    low_count = sum(1 for f in findings if getattr(f, "severity", "") == "LOW")

    risk_color = "#ef4444" if threat_score >= 80 else "#f97316" if threat_score >= 60 else "#eab308" if threat_score >= 30 else "#10b981"

    # Accounts table rows
    accounts_rows = ""
    for acc in accounts:
        accounts_rows += f"""
        <tr>
            <td style="padding: 10px 12px; border-bottom: 1px solid #e2e8f0;">{escape(str(getattr(acc, 'provider', 'AWS')))}</td>
            <td style="padding: 10px 12px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">{escape(str(getattr(acc, 'account_alias', '')))}</td>
            <td style="padding: 10px 12px; border-bottom: 1px solid #e2e8f0; font-family: monospace;">{escape(str(getattr(acc, 'account_number', '')))}</td>
            <td style="padding: 10px 12px; border-bottom: 1px solid #e2e8f0; font-family: monospace; font-size: 11px;">{escape(str(getattr(acc, 'role_arn', '')))}</td>
            <td style="padding: 10px 12px; border-bottom: 1px solid #e2e8f0; color: #10b981; font-weight: bold;">{escape(str(getattr(acc, 'connection_status', 'ACTIVE')))}</td>
        </tr>
        """

    # Framework scorecard rows
    framework_cards = ""
    for fw in frameworks:
        score = getattr(fw, 'score', 0) if hasattr(fw, 'score') else fw.get('score', 0)
        name = getattr(fw, 'name', '') if hasattr(fw, 'name') else fw.get('name', '')
        version = getattr(fw, 'version', '') if hasattr(fw, 'version') else fw.get('version', '')
        passed = getattr(fw, 'passed_controls', 0) if hasattr(fw, 'passed_controls') else fw.get('passed_controls', 0)
        total = getattr(fw, 'total_controls', 0) if hasattr(fw, 'total_controls') else fw.get('total_controls', 0)
        status_badge_color = "#10b981" if score >= 80 else "#ef4444"

        framework_cards += f"""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; flex: 1; min-width: 200px;">
            <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">{escape(str(version))}</div>
            <div style="font-weight: 700; font-size: 16px; margin-bottom: 8px; color: #0f172a;">{escape(str(name))}</div>
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <span style="font-size: 28px; font-weight: 800; color: {status_badge_color};">{score}%</span>
                <span style="font-size: 12px; color: #64748b;">{passed}/{total} Passed</span>
            </div>
        </div>
        """

    # Detailed Findings rows
    findings_rows = ""
    for f in findings:
        sev = getattr(f, "severity", "LOW")
        sev_color = "#ef4444" if sev == "CRITICAL" else "#f97316" if sev == "HIGH" else "#eab308" if sev == "MEDIUM" else "#3b82f6"
        rule_id = getattr(f, "rule_id", "")
        title = getattr(f, "title", "")
        arn = getattr(f, "resource_arn", "")
        controls = ", ".join(getattr(f, "compliance_controls", []))
        remediation = getattr(f, "remediation_json", {})
        explanation = remediation.get("explanation", "")

        findings_rows += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 12px; vertical-align: top;">
                <span style="background: {sev_color}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{sev}</span>
            </td>
            <td style="padding: 12px; vertical-align: top;">
                <div style="font-weight: 600; color: #0f172a; margin-bottom: 4px;">{escape(str(title))}</div>
                <div style="font-size: 11px; font-family: monospace; color: #475569; word-break: break-all;">{escape(str(arn))}</div>
                <div style="font-size: 12px; color: #64748b; margin-top: 6px;"><strong>Remediation:</strong> {escape(str(explanation))}</div>
            </td>
            <td style="padding: 12px; vertical-align: top; font-size: 11px; font-family: monospace; color: #0284c7;">
                {escape(str(controls))}
            </td>
            <td style="padding: 12px; vertical-align: top; font-size: 12px; font-weight: bold; color: #dc2626;">
                OPEN
            </td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CloudGuard GRC Executive Audit Report - {organization_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 40px;
            color: #0f172a;
            background-color: #ffffff;
            line-height: 1.5;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #0284c7;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .brand-title {{
            font-size: 26px;
            font-weight: 800;
            color: #0284c7;
            letter-spacing: -0.5px;
        }}
        .brand-sub {{
            font-size: 13px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .meta-box {{
            text-align: right;
            font-size: 12px;
            color: #475569;
        }}
        .summary-grid {{
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}
        .score-card {{
            flex: 1;
            min-width: 220px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}
        .section-heading {{
            font-size: 18px;
            font-weight: 700;
            color: #1e293b;
            margin-top: 30px;
            margin-bottom: 12px;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 6px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th {{
            background: #f1f5f9;
            text-align: left;
            padding: 10px 12px;
            font-weight: 600;
            color: #475569;
            border-bottom: 1px solid #cbd5e1;
        }}
        .disclaimer {{
            margin-top: 40px;
            padding: 16px;
            background: #f8fafc;
            border-left: 4px solid #0284c7;
            font-size: 11px;
            color: #64748b;
            border-radius: 0 8px 8px 0;
        }}
        @media print {{
            body {{ padding: 20px; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="margin-bottom: 20px; text-align: right;">
        <button onclick="window.print()" style="background: #0284c7; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer;">
            Print / Save as PDF
        </button>
    </div>

    <div class="header">
        <div>
            <div class="brand-title">CloudGuard GRC</div>
            <div class="brand-sub">Executive Cloud Security & Compliance Audit</div>
        </div>
        <div class="meta-box">
            <div><strong>Organization:</strong> {escape(str(organization_name))}</div>
            <div><strong>Audit Date:</strong> {date_str}</div>
            <div><strong>Report Scope:</strong> AWS Cloud Security Posture (CSPM)</div>
        </div>
    </div>

    <div class="summary-grid">
        <div class="score-card">
            <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; color: #64748b;">Threat Score</div>
            <div style="font-size: 42px; font-weight: 800; color: {risk_color}; margin: 6px 0;">{threat_score}</div>
            <span style="background: {risk_color}; color: white; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">
                {risk_level} RISK
            </span>
        </div>
        <div class="score-card" style="display: flex; justify-content: space-around; align-items: center;">
            <div>
                <div style="font-size: 24px; font-weight: 800; color: #ef4444;">{critical_count}</div>
                <div style="font-size: 11px; color: #64748b; font-weight: 600;">CRITICAL</div>
            </div>
            <div>
                <div style="font-size: 24px; font-weight: 800; color: #f97316;">{high_count}</div>
                <div style="font-size: 11px; color: #64748b; font-weight: 600;">HIGH</div>
            </div>
            <div>
                <div style="font-size: 24px; font-weight: 800; color: #eab308;">{med_count}</div>
                <div style="font-size: 11px; color: #64748b; font-weight: 600;">MEDIUM</div>
            </div>
            <div>
                <div style="font-size: 24px; font-weight: 800; color: #3b82f6;">{low_count}</div>
                <div style="font-size: 11px; color: #64748b; font-weight: 600;">LOW</div>
            </div>
        </div>
    </div>

    <div class="section-heading">Compliance Framework Posture</div>
    <div class="disclaimer">Scores are technical posture scores derived from available scan evidence. They are not official compliance certifications, attestations, or audit opinions.</div>
    <div style="display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap;">
        {framework_cards}
    </div>

    <div class="section-heading">Audited Cloud Accounts</div>
    <table style="margin-bottom: 24px;">
        <thead>
            <tr>
                <th>Provider</th>
                <th>Account Alias</th>
                <th>Account ID</th>
                <th>Assumed Role ARN</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {accounts_rows}
        </tbody>
    </table>

    <div class="section-heading">Detected Security Misconfigurations & GRC Control Gaps</div>
    <table>
        <thead>
            <tr>
                <th style="width: 100px;">Severity</th>
                <th>Issue Title & Remediation</th>
                <th style="width: 180px;">Mapped Controls</th>
                <th style="width: 80px;">Status</th>
            </tr>
        </thead>
        <tbody>
            {findings_rows}
        </tbody>
    </table>

    <div class="disclaimer">
        <strong>Auditor Attestation & Legal Notice:</strong>
        This document reflects technical audit results automatically derived from read-only AWS API telemetry and local configuration checks. Control mappings (CIS AWS Foundations Benchmark, GDPR, DPDPA, ISO 27001) represent technical alignment evidence and do not constitute official statutory legal certification.
    </div>
</body>
</html>
"""

