from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
class UserOut(ORMModel):
    id: str; tenant_id: str; email: EmailStr; full_name: str; role: str; is_active: bool
class RegisterIn(BaseModel):
    organization_name: str = Field(min_length=2, max_length=160); full_name: str = Field(min_length=2, max_length=160); email: EmailStr; password: str = Field(min_length=12, max_length=128)
class LoginIn(BaseModel):
    email: EmailStr; password: str = Field(min_length=1, max_length=128)
class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=30)
class TokenOut(BaseModel):
    access_token: str; refresh_token: str; token_type: str = "bearer"; user: UserOut
class AccountOnboardIn(BaseModel):
    account_alias: str = Field(min_length=2, max_length=160); account_number: str = Field(pattern=r"^\d{12}$"); role_arn: str = Field(pattern=r"^arn:aws:iam::\d{12}:role/.+"); external_id: str = Field(min_length=12, max_length=128); validation_mode: str = "local_mock"
class AccountOut(ORMModel):
    id: str; tenant_id: str; provider: str; account_number: str; account_alias: str; role_arn: str; external_id: str; connection_status: str; validation_mode: str; created_at: datetime
class ScanStartIn(BaseModel): cloud_account_id: str
class ScanOut(ORMModel):
    id: str; cloud_account_id: str; status: str; progress: int; partial: bool; error_summary: str | None; started_at: datetime | None; completed_at: datetime | None; created_at: datetime
class FindingOut(ORMModel):
    id: str; scan_id: str; tenant_id: str; rule_id: str; service_name: str; resource_arn: str; severity: str; risk_score: int; status: str; title: str; description: str; impact: str; remediation_json: dict[str, Any]; compliance_controls: list[str]; detected_at: datetime
class FindingStatusIn(BaseModel): status: str = Field(pattern="^(OPEN|RESOLVED|SUPPRESSED)$")
class DashboardOut(BaseModel):
    threat_score: int; risk_level: str; total_findings: int; scanned_resources: str; active_policies: int; severity_breakdown: dict[str, int]
class ComplianceControl(BaseModel):
    id: str; control_id: str; title: str; status: str; mapped_rules: list[str]; description: str
class FrameworkOut(BaseModel):
    id: str; name: str; version: str; description: str; score: int; score_type: str; assurance_status: str; active_accounts: int; passed_controls: int; total_controls: int; status: str; controls: list[ComplianceControl]
