from dataclasses import dataclass

from app.models import Finding
from app.schemas import ComplianceControl, FrameworkOut


@dataclass(frozen=True)
class ControlDefinition:
    control_id: str
    title: str
    mapped_rules: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class FrameworkDefinition:
    framework_id: str
    name: str
    version: str
    description: str
    controls: tuple[ControlDefinition, ...]


FRAMEWORK_CATALOG = (
    FrameworkDefinition(
        "cis-aws-foundations",
        "CIS AWS Foundations Benchmark",
        "v1.4.0",
        "AWS technical safeguards from the CIS Foundations Benchmark.",
        (
            ControlDefinition("1.5", "Root account MFA", ("aws.iam.root-mfa",), "Require MFA on the AWS root account."),
            ControlDefinition("1.14", "Access key rotation", ("aws.iam.stale-access-keys",), "Rotate IAM access keys within the required period."),
            ControlDefinition("1.16", "No wildcard administrator policies", ("aws.iam.wildcard-admin",), "Avoid unrestricted Action * and Resource * permissions."),
            ControlDefinition("2.1.1", "S3 Block Public Access", ("aws.s3.public-access-block",), "Enable all S3 public access block settings."),
            ControlDefinition("2.1.2", "S3 default encryption", ("aws.s3.default-encryption",), "Encrypt S3 data at rest by default."),
            ControlDefinition("3.1", "CloudTrail multi-region logging", ("aws.cloudtrail.logging-enabled",), "Maintain multi-region CloudTrail logging."),
            ControlDefinition("5.2", "Restrict unrestricted SSH", ("aws.ec2.security-group.open-admin",), "Do not expose SSH to the public internet."),
        ),
    ),
    FrameworkDefinition(
        "nist-800-53",
        "NIST SP 800-53",
        "Rev. 5",
        "Technical evidence mapped to selected NIST security and privacy controls.",
        (
            ControlDefinition("AC-6", "Least privilege", ("aws.iam.wildcard-admin",), "Limit access to the minimum necessary permissions."),
            ControlDefinition("AU-2", "Event logging", ("aws.cloudtrail.logging-enabled",), "Generate and retain auditable security events."),
            ControlDefinition("IA-2", "Identification and authentication", ("aws.iam.root-mfa",), "Use strong authentication for privileged access."),
            ControlDefinition("SC-28", "Protection of information at rest", ("aws.s3.default-encryption",), "Protect stored information with encryption."),
            ControlDefinition("CM-8", "System component inventory", (), "Maintain a complete system component inventory; requires real AWS discovery."),
        ),
    ),
    FrameworkDefinition(
        "nist-csf",
        "NIST Cybersecurity Framework",
        "2.0",
        "Posture evidence organized across Identify, Protect, Detect, Respond, and Recover.",
        (
            ControlDefinition("ID.AM", "Asset management", (), "Identify and manage assets; requires real resource inventory."),
            ControlDefinition("PR.AA", "Identity management and access control", ("aws.iam.wildcard-admin", "aws.iam.root-mfa"), "Manage identities and enforce appropriate access."),
            ControlDefinition("DE.CM", "Continuous monitoring", ("aws.cloudtrail.logging-enabled",), "Monitor systems and assets for anomalous events."),
            ControlDefinition("RS.MA", "Incident management", (), "Manage incident response workflows; requires response records."),
            ControlDefinition("RC.RP", "Incident recovery plan", (), "Execute recovery plans; requires organizational evidence."),
        ),
    ),
    FrameworkDefinition(
        "iso-27001",
        "ISO/IEC 27001",
        "2022",
        "Selected Annex A technical evidence supporting an Information Security Management System.",
        (
            ControlDefinition("A.5.15", "Access control", ("aws.iam.root-mfa", "aws.iam.wildcard-admin"), "Control access to information and systems."),
            ControlDefinition("A.8.12", "Data leakage prevention", ("aws.iam.stale-access-keys", "secrets.exposed-aws-access-key"), "Prevent credential and data leakage."),
            ControlDefinition("A.8.20", "Network security", ("aws.ec2.security-group.open-admin",), "Secure network services and boundaries."),
            ControlDefinition("A.8.24", "Use of cryptography", ("aws.s3.default-encryption",), "Use cryptography to protect information."),
            ControlDefinition("A.8.15", "Logging", ("aws.cloudtrail.logging-enabled",), "Produce and protect relevant logs."),
        ),
    ),
    FrameworkDefinition(
        "iso-27017",
        "ISO/IEC 27017",
        "2015",
        "Selected cloud-specific security practices for customer and provider responsibilities.",
        (
            ControlDefinition("9.5.1", "Cloud access control", ("aws.iam.root-mfa", "aws.iam.wildcard-admin"), "Manage cloud administrative access."),
            ControlDefinition("12.4.1", "Cloud activity logging", ("aws.cloudtrail.logging-enabled",), "Log cloud service activity."),
            ControlDefinition("13.1.1", "Network segregation", ("aws.ec2.security-group.open-admin",), "Protect cloud network boundaries."),
            ControlDefinition("10.1.1", "Cloud data encryption", ("aws.s3.default-encryption",), "Protect cloud data with cryptography."),
        ),
    ),
    FrameworkDefinition(
        "csa-ccm",
        "CSA Cloud Controls Matrix",
        "v4",
        "Cloud-specific control evidence aligned to CSA CCM domains.",
        (
            ControlDefinition("IAM-02", "Strong authentication", ("aws.iam.root-mfa",), "Apply strong authentication to cloud identities."),
            ControlDefinition("IAM-12", "Least privilege", ("aws.iam.wildcard-admin",), "Restrict cloud permissions to business need."),
            ControlDefinition("LOG-02", "Audit logging", ("aws.cloudtrail.logging-enabled",), "Collect and protect cloud audit logs."),
            ControlDefinition("DSP-04", "Data protection at rest", ("aws.s3.default-encryption",), "Protect stored cloud data."),
            ControlDefinition("IVS-09", "Network security", ("aws.ec2.security-group.open-admin",), "Restrict public network exposure."),
        ),
    ),
    FrameworkDefinition(
        "soc-2",
        "SOC 2 Type II Trust Services Criteria",
        "2017",
        "Technical security evidence supporting selected SOC 2 Security criteria; Type II requires time-based auditor evidence.",
        (
            ControlDefinition("CC6.1", "Logical access controls", ("aws.iam.root-mfa", "aws.iam.wildcard-admin"), "Restrict logical access to systems and data."),
            ControlDefinition("CC6.6", "External threat protection", ("aws.s3.public-access-block", "aws.ec2.security-group.open-admin"), "Protect against unauthorized external access."),
            ControlDefinition("CC7.2", "System monitoring", ("aws.cloudtrail.logging-enabled",), "Monitor systems for anomalies and security events."),
            ControlDefinition("CC8.1", "Change management", (), "Control changes; requires change-management evidence."),
        ),
    ),
    FrameworkDefinition(
        "pci-dss",
        "PCI DSS",
        "v4.0.1",
        "Technical evidence supporting selected payment-card security requirements.",
        (
            ControlDefinition("1.3", "Restrict inbound traffic", ("aws.ec2.security-group.open-admin",), "Restrict public inbound network traffic."),
            ControlDefinition("7.2", "Restrict access by need to know", ("aws.iam.wildcard-admin",), "Limit access to system components and data."),
            ControlDefinition("8.4", "Multi-factor authentication", ("aws.iam.root-mfa",), "Use MFA for privileged access."),
            ControlDefinition("10.2", "Audit logs", ("aws.cloudtrail.logging-enabled",), "Implement audit trails for system events."),
            ControlDefinition("3.5", "Protect stored account data", ("aws.s3.default-encryption",), "Protect stored sensitive data."),
        ),
    ),
    FrameworkDefinition(
        "hipaa-security-rule",
        "HIPAA Security Rule",
        "45 CFR 164",
        "Technical evidence supporting selected HIPAA Security Rule safeguards; healthcare scope requires organizational assessment.",
        (
            ControlDefinition("164.312(a)", "Access control", ("aws.iam.wildcard-admin",), "Limit access to electronic protected health information."),
            ControlDefinition("164.312(b)", "Audit controls", ("aws.cloudtrail.logging-enabled",), "Record and examine activity in systems containing ePHI."),
            ControlDefinition("164.312(c)", "Integrity controls", (), "Protect ePHI from improper alteration; requires workload evidence."),
            ControlDefinition("164.312(e)", "Transmission security", ("aws.ec2.security-group.open-admin",), "Protect ePHI transmitted over networks."),
            ControlDefinition("164.312(a)(2)(i)", "Unique user identification", ("aws.iam.root-mfa",), "Assign unique identification and authentication."),
        ),
    ),
    FrameworkDefinition(
        "gdpr",
        "GDPR",
        "EU 2016/679",
        "Technical security evidence supporting selected GDPR security obligations; not a legal compliance determination.",
        (
            ControlDefinition("Art. 32(1)(a)", "Encryption and confidentiality", ("aws.s3.default-encryption",), "Use encryption and confidentiality safeguards."),
            ControlDefinition("Art. 32(1)(b)", "Resilience and integrity", ("aws.s3.public-access-block",), "Protect confidentiality, integrity, availability, and resilience."),
            ControlDefinition("Art. 33", "Breach detection and notification support", ("aws.cloudtrail.logging-enabled",), "Support detection and investigation of personal-data breaches."),
            ControlDefinition("Art. 30", "Records of processing", (), "Maintain processing records; requires organizational evidence."),
            ControlDefinition("Art. 35", "Data protection impact assessment", (), "Assess high-risk processing; requires organizational evidence."),
        ),
    ),
    FrameworkDefinition(
        "dpdpa",
        "Digital Personal Data Protection Act",
        "2023",
        "Technical evidence supporting selected DPDPA security safeguard obligations.",
        (
            ControlDefinition("Sec. 8(4)", "Reasonable security safeguards", ("aws.iam.root-mfa",), "Protect personal data with reasonable safeguards."),
            ControlDefinition("Sec. 8(5)", "Data breach prevention", ("aws.s3.public-access-block", "secrets.exposed-aws-access-key"), "Reduce unauthorized exposure and breach risk."),
            ControlDefinition("Sec. 8(6)", "Unauthorized access prevention", ("aws.iam.wildcard-admin",), "Prevent unauthorized access and privilege escalation."),
            ControlDefinition("Sec. 8(7)", "Breach notification support", ("aws.cloudtrail.logging-enabled",), "Support breach detection and investigation."),
            ControlDefinition("Sec. 8(8)", "Data erasure governance", (), "Support erasure obligations; requires organizational evidence."),
        ),
    ),
    FrameworkDefinition(
        "fedramp",
        "FedRAMP",
        "Rev. 5 baseline alignment",
        "Selected technical evidence aligned to FedRAMP/NIST controls; authorization requires a formal package and assessment.",
        (
            ControlDefinition("AC-6", "Least privilege", ("aws.iam.wildcard-admin",), "Enforce least privilege for system access."),
            ControlDefinition("AU-2", "Event logging", ("aws.cloudtrail.logging-enabled",), "Generate and review audit events."),
            ControlDefinition("IA-2", "Identification and authentication", ("aws.iam.root-mfa",), "Authenticate organizational users and devices."),
            ControlDefinition("SC-28", "Protection at rest", ("aws.s3.default-encryption",), "Protect information at rest."),
            ControlDefinition("CA-7", "Continuous monitoring", (), "Perform continuous monitoring; requires recurring assessment evidence."),
        ),
    ),
)


def build_frameworks(findings: list[Finding], account_count: int) -> list[FrameworkOut]:
    open_rules = {finding.rule_id for finding in findings if finding.status == "OPEN"}
    frameworks: list[FrameworkOut] = []
    for definition in FRAMEWORK_CATALOG:
        controls = []
        for control in definition.controls:
            if not control.mapped_rules:
                status = "NEEDS_REVIEW"
            elif any(rule in open_rules for rule in control.mapped_rules):
                status = "FAIL"
            else:
                status = "PASS"
            controls.append(ComplianceControl(
                id=f"{definition.framework_id}-{control.control_id}",
                control_id=control.control_id,
                title=control.title,
                status=status,
                mapped_rules=list(control.mapped_rules),
                description=control.description,
            ))
        passed = sum(control.status == "PASS" for control in controls)
        score = round(100 * passed / len(controls)) if controls else 0
        frameworks.append(FrameworkOut(
            id=definition.framework_id,
            name=definition.name,
            version=definition.version,
            description=definition.description,
            score=score,
            score_type="TECHNICAL_POSTURE",
            assurance_status="NOT_A_CERTIFICATION",
            active_accounts=account_count,
            passed_controls=passed,
            total_controls=len(controls),
            status="ACTIVE",
            controls=controls,
        ))
    return frameworks
