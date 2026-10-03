import pytest
from app.services import aws_auditor


class FakeSts:
    def __init__(self, account_id: str):
        self.account_id = account_id

    def assume_role(self, **kwargs):
        return {
            "Credentials": {
                "AccessKeyId": "temporary-access-key",
                "SecretAccessKey": "temporary-secret-key",
                "SessionToken": "temporary-session-token",
            }
        }

    def get_caller_identity(self):
        return {"Account": self.account_id}


class FakeBaseSession:
    region_name = "us-east-1"

    def client(self, service: str, **kwargs):
        assert service == "sts"
        return FakeSts("111122223333")


class FakeAssumedSession:
    def __init__(self, attached_policies, inline_policies=None):
        self.attached_policies = attached_policies
        self.inline_policies = inline_policies or []

    def client(self, service: str, **kwargs):
        if service == "sts":
            return FakeSts("444455556666")
        return FakeIam(self.attached_policies, self.inline_policies)


class FakeIam:
    def __init__(self, attached_policies, inline_policies):
        self.attached_policies = attached_policies
        self.inline_policies = inline_policies

    def list_attached_role_policies(self, **kwargs):
        return {"AttachedPolicies": [{"PolicyArn": arn} for arn in self.attached_policies]}

    def list_role_policies(self, **kwargs):
        return {"PolicyNames": self.inline_policies}


def test_assume_role_rejects_unexpected_account(monkeypatch):
    monkeypatch.setattr(aws_auditor.boto3, "Session", lambda **kwargs: FakeAssumedSession([]))
    with pytest.raises(aws_auditor.AwsAuditError, match="different AWS account"):
        aws_auditor.assume_readonly_role(
            "arn:aws:iam::444455556666:role/CloudGuardReadOnlyAuditRole",
            "cg-ext-test-123456",
            "777788889999",
            base_session=FakeBaseSession(),
        )


def test_assume_role_rejects_unapproved_permissions(monkeypatch):
    policies = ["arn:aws:iam::444455556666:policy/AdministratorAccessCopy"]
    monkeypatch.setattr(aws_auditor.boto3, "Session", lambda **kwargs: FakeAssumedSession(policies))
    with pytest.raises(aws_auditor.AwsAuditError, match="approved read-only allowlist"):
        aws_auditor.assume_readonly_role(
            "arn:aws:iam::444455556666:role/CloudGuardReadOnlyAuditRole",
            "cg-ext-test-123456",
            "444455556666",
            base_session=FakeBaseSession(),
        )


def test_assume_role_rejects_inline_policies(monkeypatch):
    monkeypatch.setattr(
        aws_auditor.boto3,
        "Session",
        lambda **kwargs: FakeAssumedSession(
            ["arn:aws:iam::aws:policy/SecurityAudit"], ["ExtraPolicy"]
        ),
    )
    with pytest.raises(aws_auditor.AwsAuditError, match="approved read-only allowlist"):
        aws_auditor.assume_readonly_role(
            "arn:aws:iam::444455556666:role/CloudGuardReadOnlyAuditRole",
            "cg-ext-test-123456",
            "444455556666",
            base_session=FakeBaseSession(),
        )


def test_wildcard_policy_document_creates_a_finding():
    findings: list[dict] = []

    aws_auditor._check_policy_document(
        {"Statement": {"Effect": "Allow", "Action": "*", "Resource": "*"}},
        "UnsafeAdministratorPolicy",
        "arn:aws:iam::444455556666:policy/UnsafeAdministratorPolicy",
        "444455556666",
        "global",
        findings,
    )

    assert len(findings) == 1
    assert findings[0]["rule_id"] == "aws.iam.wildcard-admin"
