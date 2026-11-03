from __future__ import annotations

from html import escape
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_audit_pdf(
    organization_name: str,
    threat_score: int,
    risk_level: str,
    frameworks: list[Any],
    findings: list[Any],
) -> bytes:
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=13 * mm,
        bottomMargin=13 * mm,
        title=f"CloudGuard technical posture report - {organization_name}",
        author="CloudGuard GRC",
    )
    base = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle", parent=base["Title"], alignment=TA_CENTER, textColor=colors.HexColor("#075985")
    )
    small = ParagraphStyle("Small", parent=base["BodyText"], fontSize=7, leading=9)
    body = ParagraphStyle("Body", parent=base["BodyText"], fontSize=8, leading=10)
    story = [
        Paragraph("CloudGuard GRC Audit Report", title_style),
        Paragraph(escape(str(organization_name)), base["Heading2"]),
        Paragraph(
            f"Technical posture score: {int(threat_score)}/100 ({escape(str(risk_level))}). "
            "This report is evidence-based and is not an official compliance certification or audit opinion.",
            body,
        ),
        Spacer(1, 5 * mm),
        Paragraph("Framework Posture", base["Heading2"]),
    ]
    framework_data: list[list[Any]] = [["Framework", "Version", "Posture", "Passed", "Controls"]]
    for framework in frameworks:
        framework_data.append([
            Paragraph(escape(str(framework.name)), small),
            escape(str(framework.version)),
            f"{framework.score}% ({escape(str(framework.assurance_status))})",
            str(framework.passed_controls),
            str(framework.total_controls),
        ])
    story.append(Table(framework_data, repeatRows=1, colWidths=[62 * mm, 25 * mm, 63 * mm, 20 * mm, 20 * mm]))
    story[-1].setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f2fe")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#94a3b8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([Spacer(1, 5 * mm), Paragraph("Open Findings", base["Heading2"])])
    finding_data: list[list[Any]] = [["Severity", "Rule", "Service / Region", "Resource", "Finding", "Remediation"]]
    for finding in findings:
        remediation = finding.remediation_json or {}
        finding_data.append([
            escape(str(finding.severity)),
            Paragraph(escape(str(finding.rule_id)), small),
            Paragraph(f"{escape(str(finding.service_name))} / {escape(str(finding.region))}", small),
            Paragraph(escape(str(finding.resource_arn)), small),
            Paragraph(escape(str(finding.title)), small),
            Paragraph(escape(str(remediation.get("explanation", ""))), small),
        ])
    if len(finding_data) == 1:
        finding_data.append(["None", "", "", "", "No open findings", ""])
    finding_table = Table(
        finding_data,
        repeatRows=1,
        colWidths=[22 * mm, 40 * mm, 36 * mm, 64 * mm, 54 * mm, 57 * mm],
    )
    finding_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f2fe")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#94a3b8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(finding_table)
    document.build(story)
    return output.getvalue()
