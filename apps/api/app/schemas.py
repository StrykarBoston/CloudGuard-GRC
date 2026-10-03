from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
class UserOut(ORMModel):
    id: str; tenant_id: str; email: EmailStr; full_name: str; role: str; is_active: bool
class OrganizationOut(ORMModel):
    id: str; name: str; created_at: datetime
class RegisterIn(BaseModel):
    organization_name: str = Field(min_length=2, max_length=160); full_name: str = Field(min_length=2, max_length=160); email: EmailStr; password: str = Field(min_length=12, max_length=128)
class LoginIn(BaseModel):
    email: EmailStr; password: str = Field(min_length=1, max_length=128); remember_me: bool = True
class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=30)
class TokenOut(BaseModel):
    token_type: str = "bearer"; user: UserOut
class AccountOnboardIn(BaseModel):
    account_alias: str = Field(min_length=2, max_length=160); account_number: str = Field(pattern=r"^\d{12}$"); role_arn: str = Field(pattern=r"^arn:aws:iam::\d{12}:role/.+"); external_id: str = Field(min_length=12, max_length=128)
class AccountOut(ORMModel):
    id: str; tenant_id: str; provider: str; account_number: str; account_alias: str; role_arn: str; external_id: str; connection_status: str; validation_mode: str; created_at: datetime
class ScanStartIn(BaseModel): cloud_account_id: str
class ScanOut(ORMModel):
    id: str; cloud_account_id: str; status: str; progress: int; partial: bool; error_summary: str | None; started_at: datetime | None; completed_at: datetime | None; created_at: datetime
class FindingOut(ORMModel):
    id: str; scan_id: str; tenant_id: str; rule_id: str; service_name: str; resource_arn: str; region: str; severity: str; risk_score: int; status: str; title: str; description: str; impact: str; evidence: dict[str, Any]; remediation_json: dict[str, Any]; compliance_controls: list[str]; assigned_to_user_id: str | None; due_at: datetime | None; detected_at: datetime
class FindingUpdateIn(BaseModel):
    status: str | None = Field(default=None, pattern="^(OPEN|RESOLVED|SUPPRESSED)$")
    assigned_to_user_id: str | None = None
    due_at: datetime | None = None

class AuditLogOut(ORMModel):
    id: str; tenant_id: str; actor_id: str | None; event_type: str; details: dict[str, Any]; created_at: datetime

class TenantSettingsOut(BaseModel):
    daily_scans_enabled: bool
    daily_scan_hour_utc: int
    slack_alerts_enabled: bool
    slack_webhook_configured: bool
    scheduled_scans_available: bool = True

class TenantSettingsUpdate(BaseModel):
    daily_scans_enabled: bool | None = None
    daily_scan_hour_utc: int | None = Field(default=None, ge=0, le=23)
    slack_alerts_enabled: bool | None = None
class DashboardOut(BaseModel):
    threat_score: int; risk_level: str; total_findings: int; findings_delta: str | None = None; resources_with_findings: int; high_severity_findings: int; severity_breakdown: dict[str, int]
class ComplianceControl(BaseModel):
    id: str; control_id: str; title: str; status: str; mapped_rules: list[str]; description: str
class FrameworkOut(BaseModel):
    id: str; name: str; version: str; description: str; score: int; score_type: str; assurance_status: str; active_accounts: int; passed_controls: int; total_controls: int; status: str; controls: list[ComplianceControl]
