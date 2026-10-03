from types import SimpleNamespace

from app.services.pdf_reporter import generate_audit_pdf


def test_pdf_export_returns_valid_pdf_bytes():
    framework = SimpleNamespace(
        name="CIS AWS Foundations Benchmark",
        version="v1.4.0",
        score=72,
        assurance_status="NOT_A_CERTIFICATION",
        passed_controls=5,
        total_controls=7,
    )
    finding = SimpleNamespace(
        severity="HIGH",
        rule_id="aws.ec2.security-group.open-admin",
        service_name="EC2",
        region="us-east-1",
        resource_arn="arn:aws:ec2:us-east-1:111122223333:security-group/sg-example",
        title="Public SSH access",
        remediation_json={"explanation": "Restrict SSH to trusted addresses."},
    )

    result = generate_audit_pdf("Example Org", 52, "High", [framework], [finding])

    assert result.startswith(b"%PDF-")
    assert len(result) > 1000
