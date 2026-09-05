from app.services.secret_scanner import redact_secret, scan_content


def test_redact_secret_masking():
    raw_key = "AKIAIOSFODNN7EXAMPLE"
    masked = redact_secret(raw_key)
    assert masked.startswith("AKIA")
    assert "IOSFODNN7EXAMPLE" not in masked
    assert len(masked) == len(raw_key)
    assert "*" in masked


def test_scan_content_aws_key_detection():
    sample_text = """
    # Infrastructure Environment File
    AWS_DEFAULT_REGION=us-east-1
    AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
    DATABASE_URL=postgres://localhost
    """
    findings = scan_content(sample_text, filename=".env.production")
    assert len(findings) == 1
    finding = findings[0]
    assert finding["rule_id"] == "secrets.exposed-aws-access-key"
    assert finding["severity"] == "CRITICAL"
    assert finding["evidence"]["redacted"] is True
    # Crucial security guarantee: raw token is strictly NOT stored in evidence
    assert "AKIAIOSFODNN7EXAMPLE" not in str(finding["evidence"])
    assert "AKIA****************" in finding["evidence"]["masked_match"]


def test_scan_content_github_token():
    fake_gh_token = "ghp_123456789012345678901234567890123456"
    sample_text = f"GITHUB_PAT = '{fake_gh_token}'"
    findings = scan_content(sample_text, filename="config.py")
    assert len(findings) == 1
    assert findings[0]["rule_id"] == "secrets.exposed-github-token"
    assert fake_gh_token not in str(findings[0]["evidence"])


def test_scan_content_clean_text():
    clean_sample = """
    # Standard Terraform Configuration
    terraform {
      required_version = ">= 1.5.0"
    }
    resource "aws_s3_bucket" "b" {
      bucket = "my-secure-bucket"
    }
    """
    findings = scan_content(clean_sample, filename="main.tf")
    assert len(findings) == 0

