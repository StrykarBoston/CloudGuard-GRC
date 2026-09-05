from typing import Any, Dict, List, Optional
from app.services.rules.base import RemediationTemplate, RuleResult, SecurityRule


def evaluate_root_mfa(account_context: Dict[str, Any]) -> Optional[RuleResult]:
    account_id = account_context.get("account_number", "123456789012")
    # If root MFA is not enabled in simulated or actual context
    if not account_context.get("root_mfa_enabled", False):
        return RuleResult(
            rule_id="aws.iam.root-mfa",
            service_name="IAM",
            resource_arn=f"arn:aws:iam::{account_id}:root",
            severity="CRITICAL",
            title="Root account MFA is not enabled",
            description="The AWS root user account does not have Multi-Factor Authentication (MFA) enabled.",
            impact="Compromise of root credentials allows unrestricted administrative control of all AWS resources.",
            compliance_controls=["CIS AWS 1.5", "ISO 27001 A.5.15", "DPDPA Section 8(4)"],
            remediation=RemediationTemplate(
                explanation="Enable hardware or virtual MFA for the AWS root account immediately.",
                cli="aws iam enable-mfa-device --user-name root --serial-number <mfa-arn> --authentication-code-1 <c1> --authentication-code-2 <c2>",
                terraform="# Root user MFA must be configured via AWS Console or AWS Organizations SCP boundary."
            ),
            privilege_scope=True,
            evidence={"root_mfa_enabled": False}
        )
    return None


def evaluate_s3_public_access_block(bucket_data: Dict[str, Any]) -> Optional[RuleResult]:
    account_id = bucket_data.get("account_number", "123456789012")
    bucket_name = bucket_data.get("bucket_name", f"local-audit-{account_id}")
    block_config = bucket_data.get("public_access_block", {})
    is_safe = (
        block_config.get("BlockPublicAcls", False)
        and block_config.get("IgnorePublicAcls", False)
        and block_config.get("BlockPublicPolicy", False)
        and block_config.get("RestrictPublicBuckets", False)
    )
    if not is_safe:
        return RuleResult(
            rule_id="aws.s3.public-access-block",
            service_name="S3",
            resource_arn=f"arn:aws:s3:::{bucket_name}",
            severity="CRITICAL",
            title="S3 bucket does not block public access",
            description=f"Bucket '{bucket_name}' does not enforce all four S3 Block Public Access controls.",
            impact="Public access permissions can unintentionally expose confidential business and customer data.",
            compliance_controls=["CIS AWS 2.1.1", "GDPR Art. 32", "DPDPA Section 8(5)"],
            remediation=RemediationTemplate(
                explanation="Enable all four S3 Block Public Access settings on the bucket.",
                cli=f"aws s3api put-public-access-block --bucket {bucket_name} --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true",
                terraform=f"""resource "aws_s3_bucket_public_access_block" "example" {{
  bucket = "{bucket_name}"
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}}"""
            ),
            internet_exposed=True,
            evidence={"bucket": bucket_name, "public_access_block": block_config}
        )
    return None


def evaluate_s3_encryption(bucket_data: Dict[str, Any]) -> Optional[RuleResult]:
    account_id = bucket_data.get("account_number", "123456789012")
    bucket_name = bucket_data.get("bucket_name", f"local-assets-{account_id}")
    if not bucket_data.get("encryption_enabled", False):
        return RuleResult(
            rule_id="aws.s3.default-encryption",
            service_name="S3",
            resource_arn=f"arn:aws:s3:::{bucket_name}",
            severity="MEDIUM",
            title="S3 bucket has no default encryption",
            description=f"Bucket '{bucket_name}' is not configured with default server-side encryption (SSE).",
            impact="Objects uploaded without explicit encryption flags will be stored in cleartext at rest.",
            compliance_controls=["CIS AWS 2.1.2", "GDPR Art. 32", "ISO 27001 A.8.24"],
            remediation=RemediationTemplate(
                explanation="Enable AES256 or AWS KMS default server-side encryption on the bucket.",
                cli=f"aws s3api put-bucket-encryption --bucket {bucket_name} --server-side-encryption-configuration '{{\"Rules\": [{{\"ApplyServerSideEncryptionByDefault\": {{\"SSEAlgorithm\": \"AES256\"}}}}]}}'",
                terraform=f"""resource "aws_s3_bucket_server_side_encryption_configuration" "example" {{
  bucket = "{bucket_name}"
  rule {{
    apply_server_side_encryption_by_default {{
      sse_algorithm = "AES256"
    }}
  }}
}}"""
            ),
            evidence={"bucket": bucket_name, "encryption_enabled": False}
        )
    return None


def evaluate_security_group_ssh(sg_data: Dict[str, Any]) -> Optional[RuleResult]:
    account_id = sg_data.get("account_number", "123456789012")
    sg_id = sg_data.get("group_id", "sg-local-audit")
    open_ssh = False
    for rule in sg_data.get("ip_permissions", []):
        from_port = rule.get("from_port")
        to_port = rule.get("to_port")
        ranges = [ip_range.get("cidr_ip") for ip_range in rule.get("ip_ranges", [])]
        if (from_port is None or from_port <= 22 <= to_port) and ("0.0.0.0/0" in ranges or "::/0" in ranges):
            open_ssh = True
            break

    if open_ssh:
        return RuleResult(
            rule_id="aws.ec2.security-group.open-admin",
            service_name="EC2",
            resource_arn=f"arn:aws:ec2:us-east-1:{account_id}:security-group/{sg_id}",
            severity="CRITICAL",
            title="Security group permits unrestricted SSH",
            description=f"Security group '{sg_id}' allows ingress on port 22 from 0.0.0.0/0.",
            impact="Direct administrative SSH access is exposed to the entire public internet, risking brute-force compromise.",
            compliance_controls=["CIS AWS 5.2", "ISO 27001 A.8.20"],
            remediation=RemediationTemplate(
                explanation="Revoke ingress from 0.0.0.0/0 on port 22 and restrict SSH strictly to corporate VPN or bastion IP CIDRs.",
                cli=f"aws ec2 revoke-security-group-ingress --group-id {sg_id} --protocol tcp --port 22 --cidr 0.0.0.0/0",
                terraform=f"""# In resource "aws_security_group" "{sg_id}":
# Replace ingress 0.0.0.0/0 on port 22 with authorized bastion CIDR:
# cidr_blocks = ["10.0.0.0/16"]"""
            ),
            internet_exposed=True,
            evidence={"security_group_id": sg_id, "port": 22, "source": "0.0.0.0/0"}
        )
    return None


def evaluate_iam_wildcard(policy_data: Dict[str, Any]) -> Optional[RuleResult]:
    account_id = policy_data.get("account_number", "123456789012")
    policy_name = policy_data.get("policy_name", "LocalAuditBroadPolicy")
    has_wildcard = policy_data.get("has_wildcard", True)
    if has_wildcard:
        return RuleResult(
            rule_id="aws.iam.wildcard-admin",
            service_name="IAM",
            resource_arn=f"arn:aws:iam::{account_id}:policy/{policy_name}",
            severity="HIGH",
            title="IAM policy grants wildcard administration",
            description=f"Policy '{policy_name}' contains an Allow statement with Action='*' and Resource='*'.",
            impact="A compromised principal granted this policy acquires full administrative control over all account resources.",
            compliance_controls=["CIS AWS 1.16", "DPDPA Section 8(4)", "ISO 27001 A.5.15"],
            remediation=RemediationTemplate(
                explanation="Replace wildcard actions and resources with the least privilege needed for workload operations.",
                cli=f"aws iam create-policy-version --policy-arn arn:aws:iam::{account_id}:policy/{policy_name} --policy-document file://least-privilege.json --set-as-default",
                terraform="""data "aws_iam_policy_document" "least_privilege" {
  statement {
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = ["arn:aws:s3:::my-app-bucket/*"]
  }
}"""
            ),
            privilege_scope=True,
            evidence={"policy_name": policy_name, "actions": ["*"], "resources": ["*"]}
        )
    return None


def evaluate_iam_stale_keys(key_data: Dict[str, Any]) -> Optional[RuleResult]:
    account_id = key_data.get("account_number", "123456789012")
    user_name = key_data.get("user_name", "deploy-service-account")
    age_days = key_data.get("age_days", 120)
    if age_days > 90:
        return RuleResult(
            rule_id="aws.iam.stale-access-keys",
            service_name="IAM",
            resource_arn=f"arn:aws:iam::{account_id}:user/{user_name}",
            severity="HIGH",
            title="IAM user access key not rotated within 90 days",
            description=f"Active access key for user '{user_name}' is {age_days} days old without rotation.",
            impact="Stale access keys increase the window of vulnerability if credentials are leaked or compromised.",
            compliance_controls=["CIS AWS 1.14", "ISO 27001 A.5.15"],
            remediation=RemediationTemplate(
                explanation="Generate a new active access key, update consuming systems, and deactivate/delete the expired key.",
                cli=f"aws iam create-access-key --user-name {user_name}\naws iam update-access-key --user-name {user_name} --access-key-id <old-key-id> --status Inactive",
                terraform="# IAM access key lifecycle should be managed via automated rotation or IAM Identity Center SSO."
            ),
            evidence={"user": user_name, "key_age_days": age_days}
        )
    return None


def evaluate_cloudtrail_logging(trail_data: Dict[str, Any]) -> Optional[RuleResult]:
    account_id = trail_data.get("account_number", "123456789012")
    is_logging = trail_data.get("is_logging", False)
    is_multi_region = trail_data.get("is_multi_region", False)
    if not is_logging or not is_multi_region:
        return RuleResult(
            rule_id="aws.cloudtrail.logging-enabled",
            service_name="CloudTrail",
            resource_arn=f"arn:aws:cloudtrail:us-east-1:{account_id}:trail/main-audit-trail",
            severity="MEDIUM",
            title="CloudTrail multi-region audit logging is disabled",
            description="CloudTrail is either not actively logging or not configured to capture events across all AWS regions.",
            impact="Absence of continuous API activity logs severely impairs post-incident forensics and compliance verification.",
            compliance_controls=["CIS AWS 3.1", "ISO 27001 A.8.15", "GDPR Art. 32"],
            remediation=RemediationTemplate(
                explanation="Enable multi-region CloudTrail logging and ensure events are written to an encrypted S3 bucket.",
                cli="aws cloudtrail update-trail --name main-audit-trail --is-multi-region-trail\naws cloudtrail start-logging --name main-audit-trail",
                terraform="""resource "aws_cloudtrail" "main" {
  name                          = "main-audit-trail"
  s3_bucket_name                = "audit-logs-bucket"
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_logging                = true
}"""
            ),
            evidence={"is_logging": is_logging, "is_multi_region": is_multi_region}
        )
    return None


ALL_AWS_RULES: List[SecurityRule] = [
    SecurityRule(
        rule_id="aws.iam.root-mfa",
        service_name="IAM",
        category="Identity and Access Management",
        severity="CRITICAL",
        title="Root account MFA is not enabled",
        description="The AWS root user account does not have Multi-Factor Authentication (MFA) enabled.",
        impact="Compromise of root credentials allows unrestricted administrative control of all AWS resources.",
        compliance_controls=["CIS AWS 1.5", "ISO 27001 A.5.15", "DPDPA Section 8(4)"],
        remediation=RemediationTemplate(
            explanation="Enable hardware or virtual MFA for the AWS root account immediately.",
            cli="aws iam enable-mfa-device --user-name root ...",
            terraform="# Root user MFA must be configured via AWS Console."
        ),
        evaluator=evaluate_root_mfa
    ),
    SecurityRule(
        rule_id="aws.s3.public-access-block",
        service_name="S3",
        category="Storage & Access Control",
        severity="CRITICAL",
        title="S3 bucket does not block public access",
        description="Bucket does not enforce all four S3 Block Public Access controls.",
        impact="Public access permissions can unintentionally expose confidential business and customer data.",
        compliance_controls=["CIS AWS 2.1.1", "GDPR Art. 32", "DPDPA Section 8(5)"],
        remediation=RemediationTemplate(
            explanation="Enable all four S3 Block Public Access settings on the bucket.",
            cli="aws s3api put-public-access-block ...",
            terraform="resource \"aws_s3_bucket_public_access_block\" \"example\" { ... }"
        ),
        evaluator=evaluate_s3_public_access_block
    ),
    SecurityRule(
        rule_id="aws.ec2.security-group.open-admin",
        service_name="EC2",
        category="Network Security",
        severity="CRITICAL",
        title="Security group permits unrestricted SSH",
        description="Security group allows ingress on port 22 from 0.0.0.0/0.",
        impact="Direct administrative SSH access is exposed to the entire public internet, risking brute-force compromise.",
        compliance_controls=["CIS AWS 5.2", "ISO 27001 A.8.20"],
        remediation=RemediationTemplate(
            explanation="Revoke ingress from 0.0.0.0/0 on port 22 and restrict SSH strictly to corporate VPN.",
            cli="aws ec2 revoke-security-group-ingress ...",
            terraform="# Revoke 0.0.0.0/0 ingress."
        ),
        evaluator=evaluate_security_group_ssh
    ),
    SecurityRule(
        rule_id="aws.iam.wildcard-admin",
        service_name="IAM",
        category="Identity and Access Management",
        severity="HIGH",
        title="IAM policy grants wildcard administration",
        description="Policy contains an Allow statement with Action='*' and Resource='*'.",
        impact="Full administrative control over all account resources.",
        compliance_controls=["CIS AWS 1.16", "DPDPA Section 8(4)", "ISO 27001 A.5.15"],
        remediation=RemediationTemplate(
            explanation="Replace wildcard actions and resources with least privilege.",
            cli="aws iam create-policy-version ...",
            terraform="# Use least-privilege IAM policy document."
        ),
        evaluator=evaluate_iam_wildcard
    ),
    SecurityRule(
        rule_id="aws.iam.stale-access-keys",
        service_name="IAM",
        category="Identity and Access Management",
        severity="HIGH",
        title="IAM user access key not rotated within 90 days",
        description="Active access key is over 90 days old.",
        impact="Stale access keys increase the window of vulnerability.",
        compliance_controls=["CIS AWS 1.14", "ISO 27001 A.5.15"],
        remediation=RemediationTemplate(
            explanation="Rotate access keys periodically.",
            cli="aws iam create-access-key ...",
            terraform="# Manage access key rotation."
        ),
        evaluator=evaluate_iam_stale_keys
    ),
    SecurityRule(
        rule_id="aws.s3.default-encryption",
        service_name="S3",
        category="Storage & Access Control",
        severity="MEDIUM",
        title="S3 bucket has no default encryption",
        description="Bucket is not configured with default server-side encryption.",
        impact="Cleartext storage at rest.",
        compliance_controls=["CIS AWS 2.1.2", "GDPR Art. 32", "ISO 27001 A.8.24"],
        remediation=RemediationTemplate(
            explanation="Enable AES256 or KMS default encryption.",
            cli="aws s3api put-bucket-encryption ...",
            terraform="# Configure bucket encryption."
        ),
        evaluator=evaluate_s3_encryption
    ),
    SecurityRule(
        rule_id="aws.cloudtrail.logging-enabled",
        service_name="CloudTrail",
        category="Logging & Monitoring",
        severity="MEDIUM",
        title="CloudTrail multi-region audit logging is disabled",
        description="CloudTrail is not logging across all regions.",
        impact="Impaired post-incident forensics and auditability.",
        compliance_controls=["CIS AWS 3.1", "ISO 27001 A.8.15", "GDPR Art. 32"],
        remediation=RemediationTemplate(
            explanation="Enable multi-region CloudTrail logging.",
            cli="aws cloudtrail update-trail ...",
            terraform="# Configure multi-region CloudTrail."
        ),
        evaluator=evaluate_cloudtrail_logging
    ),
]

