import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(160), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(500))
    role: Mapped[str] = mapped_column(String(32), default="ACCOUNT_ADMIN")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(128), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class CloudAccount(Base):
    __tablename__ = "cloud_accounts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(16), default="AWS")
    account_number: Mapped[str] = mapped_column(String(12))
    account_alias: Mapped[str] = mapped_column(String(160))
    role_arn: Mapped[str] = mapped_column(String(512))
    external_id: Mapped[str] = mapped_column(String(128))
    connection_status: Mapped[str] = mapped_column(String(24), default="ACTIVE")
    validation_mode: Mapped[str] = mapped_column(String(32), default="local_mock")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (UniqueConstraint("tenant_id", "role_arn", name="uq_tenant_role_arn"),)


class Scan(Base):
    __tablename__ = "scans"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    cloud_account_id: Mapped[str] = mapped_column(ForeignKey("cloud_accounts.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(24), default="queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    partial: Mapped[bool] = mapped_column(Boolean, default=False)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Finding(Base):
    __tablename__ = "findings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("cloud_accounts.id", ondelete="CASCADE"), index=True)
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    rule_id: Mapped[str] = mapped_column(String(100), index=True)
    service_name: Mapped[str] = mapped_column(String(32))
    resource_arn: Mapped[str] = mapped_column(String(512))
    region: Mapped[str] = mapped_column(String(32), default="us-east-1")
    severity: Mapped[str] = mapped_column(String(16), index=True)
    risk_score: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="OPEN")
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    impact: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    remediation_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    compliance_controls: Mapped[list[str]] = mapped_column(JSON, default=list)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(80))
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
