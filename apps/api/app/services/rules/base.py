from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class RemediationTemplate:
    explanation: str
    cli: str
    terraform: str


@dataclass
class RuleResult:
    rule_id: str
    service_name: str
    resource_arn: str
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    title: str
    description: str
    impact: str
    compliance_controls: List[str]
    remediation: RemediationTemplate
    evidence: Dict[str, Any] = field(default_factory=dict)
    internet_exposed: bool = False
    privilege_scope: bool = False
    region: str = "us-east-1"


@dataclass
class SecurityRule:
    rule_id: str
    service_name: str
    category: str
    severity: str
    title: str
    description: str
    impact: str
    compliance_controls: List[str]
    remediation: RemediationTemplate
    evaluator: Callable[[Any], Optional[RuleResult]]

