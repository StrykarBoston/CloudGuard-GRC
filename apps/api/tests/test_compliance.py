from datetime import UTC, datetime
from types import SimpleNamespace

from app.services.compliance import build_frameworks


def test_frameworks_require_complete_live_scan_before_pass():
    account = SimpleNamespace(id="account-1", validation_mode="aws_sts_readonly")
    frameworks = build_frameworks([], [account], [])

    assert len(frameworks) == 12
    assert all(
        control.status == "NEEDS_REVIEW"
        for framework in frameworks
        for control in framework.controls
        if control.mapped_rules
    )


def test_framework_status_uses_latest_complete_scan_evidence():
    account = SimpleNamespace(id="account-1", validation_mode="aws_sts_readonly")
    scan = SimpleNamespace(
        id="scan-1",
        cloud_account_id="account-1",
        status="completed",
        partial=False,
        created_at=datetime.now(UTC),
    )
    finding = SimpleNamespace(
        account_id="account-1",
        rule_id="aws.iam.root-mfa",
        scan_id="scan-1",
        status="OPEN",
    )

    frameworks = build_frameworks([finding], [account], [scan])
    cis = next(framework for framework in frameworks if framework.id == "cis-aws-foundations")
    root_mfa = next(control for control in cis.controls if control.control_id == "1.5")
    assert root_mfa.status == "FAIL"

    clean_frameworks = build_frameworks([], [account], [scan])
    clean_cis = next(
        framework for framework in clean_frameworks if framework.id == "cis-aws-foundations"
    )
    clean_root_mfa = next(control for control in clean_cis.controls if control.control_id == "1.5")
    assert clean_root_mfa.status == "PASS"


def test_partial_scan_never_reports_a_pass():
    account = SimpleNamespace(id="account-1", validation_mode="aws_sts_readonly")
    partial_scan = SimpleNamespace(
        id="scan-1",
        cloud_account_id="account-1",
        status="completed",
        partial=True,
        created_at=datetime.now(UTC),
    )

    frameworks = build_frameworks([], [account], [partial_scan])
    assert all(
        control.status == "NEEDS_REVIEW"
        for framework in frameworks
        for control in framework.controls
        if control.mapped_rules
    )


def test_resolved_finding_needs_a_later_clean_scan():
    account = SimpleNamespace(id="account-1", validation_mode="aws_sts_readonly")
    scan = SimpleNamespace(
        id="scan-1",
        cloud_account_id="account-1",
        status="completed",
        partial=False,
        created_at=datetime.now(UTC),
    )
    finding = SimpleNamespace(
        account_id="account-1",
        rule_id="aws.iam.root-mfa",
        scan_id="scan-1",
        status="RESOLVED",
    )

    frameworks = build_frameworks([finding], [account], [scan])
    cis = next(framework for framework in frameworks if framework.id == "cis-aws-foundations")
    root_mfa = next(control for control in cis.controls if control.control_id == "1.5")
    assert root_mfa.status == "NEEDS_REVIEW"


def test_iso_data_leakage_control_is_evaluable_after_complete_scan():
    account = SimpleNamespace(id="account-1", validation_mode="aws_sts_readonly")
    scan = SimpleNamespace(
        id="scan-1",
        cloud_account_id="account-1",
        status="completed",
        partial=False,
        created_at=datetime.now(UTC),
    )

    frameworks = build_frameworks([], [account], [scan])
    iso = next(framework for framework in frameworks if framework.id == "iso-27001")
    data_leakage = next(control for control in iso.controls if control.control_id == "A.8.12")
    assert data_leakage.status == "PASS"
