from typing import Any, Dict, List
import httpx


def format_slack_payload(finding: Dict[str, Any]) -> Dict[str, Any]:
    """Format finding into Slack Block Kit message payload."""
    severity = finding.get("severity", "CRITICAL")
    title = finding.get("title", "Security Alert")
    resource = finding.get("resource_arn", "Unknown Resource")
    rule = finding.get("rule_id", "Unknown Rule")
    impact = finding.get("impact", "")
    controls = ", ".join(finding.get("compliance_controls", []))

    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 CloudGuard GRC Alert: {severity} Risk Detected",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Title:*\n{title}"},
                    {"type": "mrkdwn", "text": f"*Severity:*\n`{severity}`"},
                    {"type": "mrkdwn", "text": f"*Rule ID:*\n`{rule}`"},
                    {"type": "mrkdwn", "text": f"*Controls:*\n{controls or 'N/A'}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Resource:*\n`{resource}`\n*Impact:*\n{impact}"
                }
            }
        ]
    }


async def dispatch_critical_alerts(webhook_url: str, findings: List[Dict[str, Any]]) -> int:
    """Send critical findings to configured webhook endpoint."""
    if not webhook_url:
        return 0

    dispatched = 0
    critical_findings = [f for f in findings if f.get("severity") == "CRITICAL"]

    async with httpx.AsyncClient(timeout=5.0) as client:
        for finding in critical_findings:
            payload = format_slack_payload(finding)
            try:
                response = await client.post(webhook_url, json=payload)
                if response.is_success:
                    dispatched += 1
            except Exception:
                # Webhook failure should never crash core audit operations
                continue

    return dispatched

