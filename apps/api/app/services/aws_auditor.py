from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import boto3
from app.models import CloudAccount
from app.services.rules.aws_rules import (
    evaluate_cloudtrail_logging,
    evaluate_iam_stale_keys,
    evaluate_iam_wildcard,
    evaluate_root_mfa,
    evaluate_s3_encryption,
    evaluate_s3_public_access_block,
    evaluate_security_group_ssh,
)
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

ALLOWED_ROLE_POLICIES = {
    "arn:aws:iam::aws:policy/SecurityAudit",
    "arn:aws:iam::aws:policy/job-function/ViewOnlyAccess",
}
AWS_CONFIG = Config(
    connect_timeout=5,
    read_timeout=20,
    retries={"mode": "standard", "max_attempts": 4},
)


class AwsAuditError(Exception):
    pass


def _base_session() -> boto3.Session:
    return boto3.Session()


def _role_name(role_arn: str) -> str:
    resource = role_arn.split(":", 5)[-1]
    if not resource.startswith("role/"):
        raise AwsAuditError("The ARN must identify an IAM role")
    return resource.removeprefix("role/").rsplit("/", 1)[-1]


def assume_readonly_role(
    role_arn: str,
    external_id: str,
    expected_account: str,
    base_session: boto3.Session | None = None,
) -> boto3.Session:
    base = base_session or _base_session()
    sts = base.client("sts", config=AWS_CONFIG)
    try:
        response = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName="cloudguard-readonly-audit",
            ExternalId=external_id,
            DurationSeconds=900,
        )
    except (BotoCoreError, ClientError) as exc:
        raise AwsAuditError(
            "AWS STS AssumeRole failed; verify the role trust policy and ExternalId"
        ) from exc

    credentials = response["Credentials"]
    assumed = boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
        region_name=base.region_name or "us-east-1",
    )
    try:
        identity = assumed.client("sts", config=AWS_CONFIG).get_caller_identity()
    except (BotoCoreError, ClientError) as exc:
        raise AwsAuditError("Could not verify the assumed AWS identity") from exc
    if identity.get("Account") != expected_account:
        raise AwsAuditError("The assumed role belongs to a different AWS account")

    iam = assumed.client("iam", config=AWS_CONFIG)
    role_name = _role_name(role_arn)
    try:
        attached = iam.list_attached_role_policies(RoleName=role_name).get("AttachedPolicies", [])
        inline = iam.list_role_policies(RoleName=role_name).get("PolicyNames", [])
    except (BotoCoreError, ClientError) as exc:
        raise AwsAuditError("Could not verify permissions attached to the assumed role") from exc

    policy_arns = {policy["PolicyArn"] for policy in attached}
    if inline or not policy_arns or not policy_arns.issubset(ALLOWED_ROLE_POLICIES):
        raise AwsAuditError(
            "Role permissions are not on the approved read-only allowlist; "
            "remove inline or unapproved policies"
        )
    if "arn:aws:iam::aws:policy/SecurityAudit" not in policy_arns:
        raise AwsAuditError("Attach the AWS SecurityAudit managed policy to the audit role")
    return assumed


def validate_aws_account(role_arn: str, external_id: str, account_number: str) -> None:
    assumed = assume_readonly_role(role_arn, external_id, account_number)
    assumed.client("sts", config=AWS_CONFIG).get_caller_identity()


def _client(session: boto3.Session, service: str, region: str | None = None) -> Any:
    return session.client(service, region_name=region, config=AWS_CONFIG)


def _error_code(exc: ClientError) -> str:
    return str(exc.response.get("Error", {}).get("Code", "Unknown"))


def _finding(result: Any, region: str, resource_arn: str | None = None) -> dict[str, Any]:
    return {
        "rule_id": result.rule_id,
        "service_name": result.service_name,
        "resource_arn": resource_arn or result.resource_arn,
        "region": region,
        "severity": result.severity,
        "title": result.title,
        "description": result.description,
        "impact": result.impact,
        "controls": result.compliance_controls,
        "internet": result.internet_exposed,
        "privilege": result.privilege_scope,
        "evidence": result.evidence,
        "remediation": {
            "explanation": result.remediation.explanation,
            "cli": result.remediation.cli,
            "terraform": result.remediation.terraform,
        },
    }


def _is_missing_configuration(exc: ClientError) -> bool:
    return _error_code(exc) in {
        "NoSuchPublicAccessBlockConfiguration",
        "ServerSideEncryptionConfigurationNotFoundError",
        "NoSuchBucketPolicy",
        "NoSuchEntity",
    }


def _public_bucket_finding(bucket_name: str, reason: str) -> dict[str, Any]:
    resource_name = bucket_name.replace("-", "_")
    return {
        "rule_id": "aws.s3.public-exposure",
        "service_name": "S3",
        "resource_arn": f"arn:aws:s3:::{bucket_name}",
        "region": "global",
        "severity": "CRITICAL",
        "title": "S3 bucket has public access",
        "description": f"AWS reports public access on bucket '{bucket_name}' ({reason}).",
        "impact": (
            "Public bucket access can expose confidential or personal data "
            "to unauthenticated users."
        ),
        "controls": ["CIS AWS 2.1.1", "GDPR Art. 32", "DPDPA Section 8(5)"],
        "internet": True,
        "privilege": False,
        "evidence": {"bucket": bucket_name, "public_access_reason": reason, "redacted": True},
        "remediation": {
            "explanation": (
                "Remove public bucket policies or ACL grants and enable all S3 "
                "Block Public Access settings."
            ),
            "cli": (
                f"aws s3api put-public-access-block --bucket {bucket_name} "
                "--public-access-block-configuration "
                "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,"
                "RestrictPublicBuckets=true"
            ),
            "terraform": (
                'resource "aws_s3_bucket_public_access_block" '
                f'"{resource_name}" {{\n'
                f'  bucket = "{bucket_name}"\n'
                "  block_public_acls = true\n"
                "  block_public_policy = true\n"
                "  ignore_public_acls = true\n"
                "  restrict_public_buckets = true\n"
                "}"
            ),
        },
    }


def _check_managed_policy(
    iam: Any,
    arn: str,
    account_id: str,
    region: str,
    findings: list[dict[str, Any]],
    errors: list[str],
) -> None:
    try:
        policy = iam.get_policy(PolicyArn=arn)["Policy"]
        version_id = policy["DefaultVersionId"]
        document = iam.get_policy_version(PolicyArn=arn, VersionId=version_id)["PolicyVersion"][
            "Document"
        ]
    except ClientError as exc:
        errors.append(f"IAM policy inspection for {arn}: {_error_code(exc)}")
        return
    _check_policy_document(document, policy["PolicyName"], arn, account_id, region, findings)


def _check_policy_document(
    document: dict[str, Any],
    policy_name: str,
    resource_arn: str,
    account_id: str,
    region: str,
    findings: list[dict[str, Any]],
) -> None:
    statements = document.get("Statement", [])
    if isinstance(statements, dict):
        statements = [statements]
    for statement in statements:
        actions = statement.get("Action", [])
        resources = statement.get("Resource", [])
        actions = [actions] if isinstance(actions, str) else actions
        resources = [resources] if isinstance(resources, str) else resources
        if statement.get("Effect") == "Allow" and "*" in actions and "*" in resources:
            result = evaluate_iam_wildcard(
                {
                    "account_number": account_id,
                    "policy_name": policy_name,
                    "has_wildcard": True,
                }
            )
            if result:
                findings.append(_finding(result, region, resource_arn))
            return


def _scan_inline_policies(
    iam: Any, account_id: str, findings: list[dict[str, Any]], errors: list[str]
) -> None:
    entity_types = (
        ("roles", "Roles", "RoleName", "RoleName", "RoleArn"),
        ("users", "Users", "UserName", "UserName", "Arn"),
        ("groups", "Groups", "GroupName", "GroupName", "Arn"),
    )
    for collection, response_key, list_key, name_key, arn_key in entity_types:
        try:
            entity_paginator = iam.get_paginator(f"list_{collection}")
            policy_list_paginator = iam.get_paginator(f"list_{collection[:-1]}_policies")
            for page in entity_paginator.paginate():
                for entity in page.get(response_key, []):
                    name = entity[list_key]
                    resource_arn = entity.get(
                        arn_key, f"arn:aws:iam::{account_id}:{collection[:-1]}/{name}"
                    )
                    for policy_page in policy_list_paginator.paginate(**{name_key: name}):
                        for policy_name in policy_page.get("PolicyNames", []):
                            try:
                                response = getattr(iam, f"get_{collection[:-1]}_policy")(
                                    **{name_key: name, "PolicyName": policy_name}
                                )
                                _check_policy_document(
                                    response["PolicyDocument"],
                                    policy_name,
                                    resource_arn,
                                    account_id,
                                    "global",
                                    findings,
                                )
                            except ClientError as exc:
                                errors.append(
                                    f"IAM inline policy {name}/{policy_name}: {_error_code(exc)}"
                                )
        except (ClientError, BotoCoreError) as exc:
            errors.append(f"IAM {collection} inline policies: {type(exc).__name__}")


def scan_aws_account(account: CloudAccount) -> tuple[list[dict[str, Any]], list[str]]:
    session = assume_readonly_role(account.role_arn, account.external_id, account.account_number)
    findings: list[dict[str, Any]] = []
    errors: list[str] = []
    account_id = account.account_number
    home_region = session.region_name or "us-east-1"

    iam = _client(session, "iam")
    try:
        summary = iam.get_account_summary()["SummaryMap"]
        result = evaluate_root_mfa(
            {
                "account_number": account_id,
                "root_mfa_enabled": bool(summary.get("AccountMFAEnabled", 0)),
            }
        )
        if result:
            findings.append(_finding(result, "global"))
    except ClientError as exc:
        errors.append(f"IAM account summary: {_error_code(exc)}")

    try:
        paginator = iam.get_paginator("list_policies")
        for page in paginator.paginate(Scope="All", OnlyAttached=True):
            for policy in page.get("Policies", []):
                _check_managed_policy(iam, policy["Arn"], account_id, "global", findings, errors)
    except (ClientError, BotoCoreError) as exc:
        errors.append(f"IAM managed policies: {type(exc).__name__}")

    _scan_inline_policies(iam, account_id, findings, errors)

    try:
        users = iam.get_paginator("list_users")
        now = datetime.now(UTC)
        for page in users.paginate():
            for user in page.get("Users", []):
                keys = iam.get_paginator("list_access_keys")
                for key_page in keys.paginate(UserName=user["UserName"]):
                    for key in key_page.get("AccessKeyMetadata", []):
                        if key["Status"] != "Active":
                            continue
                        created = key["CreateDate"]
                        age = (now - created.astimezone(UTC)).days
                        result = evaluate_iam_stale_keys(
                            {
                                "account_number": account_id,
                                "user_name": user["UserName"],
                                "age_days": age,
                            }
                        )
                        if result:
                            findings.append(_finding(result, "global", user["Arn"]))
    except (ClientError, BotoCoreError) as exc:
        errors.append(f"IAM access keys: {type(exc).__name__}")

    try:
        s3 = _client(session, "s3", home_region)
        response = s3.list_buckets()
        while True:
            for bucket in response.get("Buckets", []):
                name = bucket["Name"]
                try:
                    block = s3.get_public_access_block(Bucket=name)[
                        "PublicAccessBlockConfiguration"
                    ]
                except ClientError as exc:
                    if _is_missing_configuration(exc):
                        block = {}
                    else:
                        errors.append(f"S3 public access block for {name}: {_error_code(exc)}")
                        continue
                result = evaluate_s3_public_access_block(
                    {
                        "account_number": account_id,
                        "bucket_name": name,
                        "public_access_block": block,
                    }
                )
                if result:
                    findings.append(_finding(result, "global", f"arn:aws:s3:::{name}"))
                try:
                    policy_status = s3.get_bucket_policy_status(Bucket=name).get("PolicyStatus", {})
                    if policy_status.get("IsPublic"):
                        findings.append(_public_bucket_finding(name, "bucket policy is public"))
                except ClientError as exc:
                    if not _is_missing_configuration(exc):
                        errors.append(f"S3 policy status for {name}: {_error_code(exc)}")
                try:
                    acl = s3.get_bucket_acl(Bucket=name)
                    public_groups = {
                        "http://acs.amazonaws.com/groups/global/AllUsers",
                        "http://acs.amazonaws.com/groups/global/AuthenticatedUsers",
                    }
                    if any(
                        grant.get("Grantee", {}).get("URI") in public_groups
                        and grant.get("Permission")
                        in {"READ", "WRITE", "READ_ACP", "WRITE_ACP", "FULL_CONTROL"}
                        for grant in acl.get("Grants", [])
                    ):
                        findings.append(
                            _public_bucket_finding(
                                name, "bucket ACL grants access to a public group"
                            )
                        )
                except ClientError as exc:
                    errors.append(f"S3 ACL for {name}: {_error_code(exc)}")
                try:
                    s3.get_bucket_encryption(Bucket=name)
                    encryption_enabled = True
                except ClientError as exc:
                    if _is_missing_configuration(exc):
                        encryption_enabled = False
                    else:
                        errors.append(f"S3 encryption for {name}: {_error_code(exc)}")
                        continue
                result = evaluate_s3_encryption(
                    {
                        "account_number": account_id,
                        "bucket_name": name,
                        "encryption_enabled": encryption_enabled,
                    }
                )
                if result:
                    findings.append(_finding(result, "global", f"arn:aws:s3:::{name}"))
            token = response.get("NextContinuationToken")
            if not response.get("IsTruncated") or not token:
                break
            response = s3.list_buckets(ContinuationToken=token)
    except (ClientError, BotoCoreError) as exc:
        errors.append(f"S3 bucket inventory: {type(exc).__name__}")

    try:
        region_response = _client(session, "ec2", home_region).describe_regions(AllRegions=False)
        regions = [item["RegionName"] for item in region_response.get("Regions", [])]
    except (ClientError, BotoCoreError) as exc:
        errors.append(f"AWS region discovery: {type(exc).__name__}")
        regions = [home_region]

    for region in regions:
        ec2 = _client(session, "ec2", region)
        try:
            paginator = ec2.get_paginator("describe_security_groups")
            for page in paginator.paginate():
                for group in page.get("SecurityGroups", []):
                    for permission in group.get("IpPermissions", []):
                        start = permission.get("FromPort", 0)
                        end = permission.get("ToPort", 65535)
                        if not (start <= 22 <= end or start <= 3389 <= end):
                            continue
                        public_ranges = [
                            item.get("CidrIp") for item in permission.get("IpRanges", [])
                        ] + [item.get("CidrIpv6") for item in permission.get("Ipv6Ranges", [])]
                        if "0.0.0.0/0" not in public_ranges and "::/0" not in public_ranges:
                            continue
                        result = evaluate_security_group_ssh(
                            {
                                "account_number": account_id,
                                "group_id": group["GroupId"],
                                "ip_permissions": [
                                    {
                                        "from_port": 0 if start is None else start,
                                        "to_port": 65535 if end is None else end,
                                        "ip_ranges": [{"cidr_ip": cidr} for cidr in public_ranges],
                                    }
                                ],
                            }
                        )
                        if result:
                            from_p = 0 if start is None else start
                            to_p = 65535 if end is None else end
                            port = 22 if from_p <= 22 <= to_p else 3389
                            result.title = f"Security group exposes administrative port {port}"
                            result.description = (
                                f"Security group '{group['GroupId']}' permits "
                                f"public ingress on port {port}."
                            )
                            result.evidence.update({"port": port, "sources": public_ranges})
                            arn = (
                                f"arn:aws:ec2:{region}:{account_id}:security-group/"
                                f"{group['GroupId']}"
                            )
                            findings.append(_finding(result, region, arn))
        except (ClientError, BotoCoreError) as exc:
            errors.append(f"EC2 security groups in {region}: {type(exc).__name__}")

        try:
            kms = _client(session, "kms", region)
            key_paginator = kms.get_paginator("list_keys")
            for page in key_paginator.paginate():
                for key in page.get("Keys", []):
                    metadata = kms.describe_key(KeyId=key["KeyId"])["KeyMetadata"]
                    if (
                        metadata.get("KeyManager") != "CUSTOMER"
                        or metadata.get("KeyState") != "Enabled"
                        or metadata.get("KeySpec") != "SYMMETRIC_DEFAULT"
                        or metadata.get("KeyUsage") != "ENCRYPT_DECRYPT"
                        or metadata.get("Origin") != "AWS_KMS"
                    ):
                        continue
                    try:
                        rotation = kms.get_key_rotation_status(KeyId=key["KeyId"])
                    except ClientError as exc:
                        errors.append(f"KMS rotation status for {key['KeyId']}: {_error_code(exc)}")
                        continue
                    if not rotation.get("KeyRotationEnabled", False):
                        key_arn = metadata["Arn"]
                        findings.append(
                            {
                                "rule_id": "aws.kms.key-rotation",
                                "service_name": "KMS",
                                "resource_arn": key_arn,
                                "region": region,
                                "severity": "MEDIUM",
                                "title": "Customer-managed KMS key rotation is disabled",
                                "description": (
                                    "Automatic key rotation is disabled for this enabled "
                                    "customer-managed KMS key."
                                ),
                                "impact": (
                                    "Long-lived encryption keys increase the impact of "
                                    "key compromise."
                                ),
                                "controls": ["ISO 27001 A.8.24", "PCI DSS 3.6.1"],
                                "internet": False,
                                "privilege": False,
                                "evidence": {
                                    "key_id": metadata["KeyId"],
                                    "rotation_enabled": False,
                                    "redacted": True,
                                },
                                "remediation": {
                                    "explanation": (
                                        "Enable automatic rotation for this customer-managed "
                                        "symmetric KMS key where supported."
                                    ),
                                    "cli": (
                                        f"aws kms enable-key-rotation --key-id "
                                        f"{metadata['KeyId']} --region {region}"
                                    ),
                                    "terraform": (
                                        'resource "aws_kms_key" "example" { '
                                        "rotation_period_in_days = 365 }"
                                    ),
                                },
                            }
                        )
        except (ClientError, BotoCoreError) as exc:
            errors.append(f"KMS key rotation in {region}: {type(exc).__name__}")

    try:
        cloudtrail = _client(session, "cloudtrail", home_region)
        trails = cloudtrail.describe_trails(includeShadowTrails=True).get("trailList", [])
        multi_region_trails = [trail for trail in trails if trail.get("IsMultiRegionTrail")]
        active = False
        for trail in multi_region_trails:
            status = cloudtrail.get_trail_status(Name=trail["TrailARN"])
            if status.get("IsLogging"):
                active = True
                break
        result = evaluate_cloudtrail_logging(
            {
                "account_number": account_id,
                "is_logging": active,
                "is_multi_region": bool(multi_region_trails),
            }
        )
        if result:
            findings.append(_finding(result, "global"))
    except (ClientError, BotoCoreError) as exc:
        errors.append(f"CloudTrail inspection: {type(exc).__name__}")

    return findings, errors
