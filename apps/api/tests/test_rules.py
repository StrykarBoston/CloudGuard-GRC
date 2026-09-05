from app.services.rules.aws_rules import (
    evaluate_cloudtrail_logging,
    evaluate_iam_stale_keys,
    evaluate_iam_wildcard,
    evaluate_root_mfa,
    evaluate_s3_encryption,
    evaluate_s3_public_access_block,
    evaluate_security_group_ssh,
)


def test_root_mfa_detection():
    # Negative case (MFA disabled) -> Finding
    result = evaluate_root_mfa({"account_number": "111222333444", "root_mfa_enabled": False})
    assert result is not None
    assert result.rule_id == "aws.iam.root-mfa"
    assert result.severity == "CRITICAL"
    assert "CIS AWS 1.5" in result.compliance_controls

    # Positive case (MFA enabled) -> Clean
    clean = evaluate_root_mfa({"account_number": "111222333444", "root_mfa_enabled": True})
    assert clean is None


def test_s3_public_access_block_detection():
    # Misconfigured bucket
    result = evaluate_s3_public_access_block({
        "account_number": "111222333444",
        "bucket_name": "exposed-bucket",
        "public_access_block": {"BlockPublicAcls": False}
    })
    assert result is not None
    assert result.rule_id == "aws.s3.public-access-block"
    assert result.severity == "CRITICAL"
    assert result.internet_exposed is True
    assert "GDPR Art. 32" in result.compliance_controls

    # Fully compliant bucket
    clean = evaluate_s3_public_access_block({
        "account_number": "111222333444",
        "bucket_name": "safe-bucket",
        "public_access_block": {
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True
        }
    })
    assert clean is None


def test_security_group_ssh_detection():
    # 0.0.0.0/0 on port 22
    result = evaluate_security_group_ssh({
        "account_number": "111222333444",
        "group_id": "sg-open",
        "ip_permissions": [
            {"from_port": 22, "to_port": 22, "ip_ranges": [{"cidr_ip": "0.0.0.0/0"}]}
        ]
    })
    assert result is not None
    assert result.rule_id == "aws.ec2.security-group.open-admin"
    assert result.severity == "CRITICAL"

    # Restricted CIDR
    clean = evaluate_security_group_ssh({
        "account_number": "111222333444",
        "group_id": "sg-safe",
        "ip_permissions": [
            {"from_port": 22, "to_port": 22, "ip_ranges": [{"cidr_ip": "10.0.0.0/16"}]}
        ]
    })
    assert clean is None


def test_iam_wildcard_detection():
    result = evaluate_iam_wildcard({
        "account_number": "111222333444",
        "policy_name": "AdminPolicy",
        "has_wildcard": True
    })
    assert result is not None
    assert result.rule_id == "aws.iam.wildcard-admin"
    assert result.severity == "HIGH"
    assert result.privilege_scope is True


def test_iam_stale_keys_detection():
    # 100 days old (>90)
    result = evaluate_iam_stale_keys({
        "account_number": "111222333444",
        "user_name": "ci-user",
        "age_days": 100
    })
    assert result is not None
    assert result.rule_id == "aws.iam.stale-access-keys"
    assert result.severity == "HIGH"

    # 45 days old (<=90)
    clean = evaluate_iam_stale_keys({
        "account_number": "111222333444",
        "user_name": "ci-user",
        "age_days": 45
    })
    assert clean is None


def test_cloudtrail_logging_detection():
    result = evaluate_cloudtrail_logging({
        "account_number": "111222333444",
        "is_logging": False,
        "is_multi_region": False
    })
    assert result is not None
    assert result.rule_id == "aws.cloudtrail.logging-enabled"
    assert result.severity == "MEDIUM"

    clean = evaluate_cloudtrail_logging({
        "account_number": "111222333444",
        "is_logging": True,
        "is_multi_region": True
    })
    assert clean is None

