import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
import secrets

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_token, new_refresh_token, password_hash, token_digest, verify_password
from app.db import engine, get_session
from app.dependencies import current_user, require_roles, get_tenant_repo
from app.models import AuditLog, CloudAccount, Finding, PasswordResetToken, Scan, Session, Tenant, TenantSettings, User
from app.queue import enqueue_scan, get_queue
from app.repositories import TenantRepository
from app.schemas import (
    AccountOnboardIn,
    AccountOut,
    AuditLogOut,
    DashboardOut,
    FindingOut,
    FindingUpdateIn,
    ForgotPasswordIn,
    ForgotPasswordOut,
    FrameworkOut,
    LoginIn,
    OrganizationOut,
    RefreshIn,
    RegisterIn,
    ResetPasswordIn,
    ResetPasswordOut,
    ScanOut,
    ScanStartIn,
    TenantSettingsOut,
    TenantSettingsUpdate,
    TokenOut,
    UserOut,
    VerifyResetTokenOut,
)
from app.services.aws_auditor import AwsAuditError, validate_aws_account
from app.services.compliance import build_frameworks, framework_rule_ids
from app.services.pdf_reporter import generate_audit_pdf
from app.services.reporter import generate_executive_html_report
from app.services.secret_scanner import scan_content, scan_local_path

settings = get_settings()

@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await engine.dispose()

class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str

app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])

limiter = Limiter(key_func=get_remote_address, storage_uri=settings.redis_url)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' fonts.googleapis.com; font-src fonts.gstatic.com; img-src 'self' data:;"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

async def issue_session(
    session: AsyncSession, user: User, response: Response, remember_me: bool = True
) -> TokenOut:
    refresh = new_refresh_token()
    session.add(Session(
        user_id=user.id,
        refresh_token_hash=token_digest(refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days),
        remember_me=remember_me,
    ))
    await session.commit()
    access = create_token(user.id, user.tenant_id, user.role, "access", settings.access_token_minutes)
    response.set_cookie(
        "access_token", access, httponly=True, secure=settings.app_env == "production",
        samesite="lax", max_age=settings.access_token_minutes * 60 if remember_me else None,
    )
    response.set_cookie(
        "refresh_token", refresh, httponly=True, path="/api/v1/auth/refresh",
        secure=settings.app_env == "production", samesite="lax",
        max_age=settings.refresh_token_days * 86400 if remember_me else None,
    )
    return TokenOut(user=UserOut.model_validate(user))

@app.get("/health", response_model=HealthResponse, tags=["system"])
@app.get("/api/v1/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="cloudguard-api", environment=settings.app_env)

@app.get("/api/v1/ready", response_model=HealthResponse, tags=["system"])
async def ready(session: AsyncSession = Depends(get_session)) -> HealthResponse:
    await session.execute(select(1))
    return HealthResponse(status="ready", service="cloudguard-api", environment=settings.app_env)

@app.post("/api/v1/auth/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, response: Response, payload: RegisterIn, session: AsyncSession = Depends(get_session)) -> TokenOut:
    if await session.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(status_code=409, detail="An account with that email already exists")
    tenant = Tenant(name=payload.organization_name.strip())
    session.add(tenant)
    await session.flush()
    user = User(tenant_id=tenant.id, email=payload.email.lower(), full_name=payload.full_name.strip(), password_hash=password_hash(payload.password), role="ACCOUNT_ADMIN")
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Organization or email already exists") from exc
    return await issue_session(session, user, response, remember_me=True)

@app.post("/api/v1/auth/login", response_model=TokenOut)
@limiter.limit("10/minute")
async def login(request: Request, response: Response, payload: LoginIn, session: AsyncSession = Depends(get_session)) -> TokenOut:
    user = await session.scalar(select(User).where(User.email == payload.email.lower()))
    now = datetime.now(timezone.utc)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.locked_until and user.locked_until > now:
        remaining_mins = max(1, int((user.locked_until - now).total_seconds() / 60))
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account is temporarily locked. Please try again in {remaining_mins} minute(s) or use 'Forgot password' to reset.",
        )
    if not verify_password(payload.password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.failed_login_attempts = 0
            user.locked_until = now + timedelta(minutes=15)
            await session.commit()
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account temporarily locked for 15 minutes due to 5 failed attempts. Please reset your password to unlock immediately.",
            )
        await session.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user.failed_login_attempts = 0
    user.locked_until = None
    return await issue_session(session, user, response, remember_me=payload.remember_me)

@app.post("/api/v1/auth/refresh", response_model=TokenOut)
@limiter.limit("20/minute")
async def refresh(request: Request, response: Response, payload: RefreshIn | None = None, session: AsyncSession = Depends(get_session)) -> TokenOut:
    token = (payload.refresh_token if payload else None) or request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    saved = await session.scalar(select(Session).where(Session.refresh_token_hash == token_digest(token), Session.revoked.is_(False)))
    if saved is None or saved.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user = await session.get(User, saved.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Session is no longer valid")
    saved.revoked = True
    return await issue_session(session, user, response, remember_me=saved.remember_me)

@app.post("/api/v1/auth/logout")
async def logout(request: Request, response: Response, session: AsyncSession = Depends(get_session)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        saved = await session.scalar(
            select(Session).where(Session.refresh_token_hash == token_digest(refresh_token))
        )
        if saved:
            saved.revoked = True
            await session.commit()
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/api/v1/auth/refresh")
    return {"status": "ok"}

@app.post("/api/v1/auth/forgot-password", response_model=ForgotPasswordOut)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    payload: ForgotPasswordIn,
    session: AsyncSession = Depends(get_session),
) -> ForgotPasswordOut:
    user = await session.scalar(select(User).where(User.email == payload.email.lower()))
    generic_msg = "If an account exists with this email address, password reset instructions have been generated."

    if user is None or not user.is_active:
        return ForgotPasswordOut(message=generic_msg)

    # Invalidate previous unused reset tokens for this user
    previous_tokens = await session.scalars(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used.is_(False),
        )
    )
    for pt in previous_tokens:
        pt.used = True

    # Generate secure random reset token
    raw_token = secrets.token_urlsafe(32)
    reset_entry = PasswordResetToken(
        user_id=user.id,
        token_hash=token_digest(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        used=False,
    )
    session.add(reset_entry)

    # Record in audit log
    session.add(AuditLog(
        tenant_id=user.tenant_id,
        actor_id=user.id,
        event_type="auth.password_reset_requested",
        details={"email": user.email, "ip": request.client.host if request.client else "unknown"},
    ))

    await session.commit()

    return ForgotPasswordOut(
        message=generic_msg,
        reset_token=raw_token if settings.app_env != "production" else None,
    )

@app.get("/api/v1/auth/reset-password/verify", response_model=VerifyResetTokenOut)
async def verify_reset_token(
    token: str = Query(..., min_length=10),
    session: AsyncSession = Depends(get_session),
) -> VerifyResetTokenOut:
    hashed = token_digest(token)
    token_entry = await session.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == hashed,
            PasswordResetToken.used.is_(False),
        )
    )
    now = datetime.now(timezone.utc)
    if token_entry is None or token_entry.expires_at.replace(tzinfo=timezone.utc) < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset link is invalid or has expired. Please request a new one.",
        )

    user = await session.get(User, token_entry.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account associated with this token is no longer active.",
        )

    return VerifyResetTokenOut(valid=True, email=user.email)

@app.post("/api/v1/auth/reset-password", response_model=ResetPasswordOut)
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    payload: ResetPasswordIn,
    session: AsyncSession = Depends(get_session),
) -> ResetPasswordOut:
    hashed = token_digest(payload.token)
    token_entry = await session.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == hashed,
            PasswordResetToken.used.is_(False),
        )
    )
    now = datetime.now(timezone.utc)
    if token_entry is None or token_entry.expires_at.replace(tzinfo=timezone.utc) < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset link is invalid or has expired. Please request a new one.",
        )

    user = await session.get(User, token_entry.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account associated with this token is no longer active.",
        )

    # Set new password hash and unlock account
    user.password_hash = password_hash(payload.new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    token_entry.used = True

    # Invalidate all existing sessions
    active_sessions = await session.scalars(
        select(Session).where(
            Session.user_id == user.id,
            Session.revoked.is_(False),
        )
    )
    for s in active_sessions:
        s.revoked = True

    # Record in audit log
    session.add(AuditLog(
        tenant_id=user.tenant_id,
        actor_id=user.id,
        event_type="auth.password_reset_completed",
        details={"email": user.email, "ip": request.client.host if request.client else "unknown"},
    ))

    await session.commit()

    return ResetPasswordOut(
        status="ok",
        message="Your password has been successfully updated. You may now sign in.",
    )

@app.get("/api/v1/auth/me", response_model=UserOut)
async def me(user: User = Depends(current_user)) -> User: return user

@app.get("/api/v1/organization", response_model=OrganizationOut)
async def organization(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> Tenant:
    tenant = await session.get(Tenant, user.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return tenant

@app.get("/api/v1/cloud-accounts", response_model=list[AccountOut])
async def accounts(repo: TenantRepository = Depends(get_tenant_repo)): return await repo.accounts()

@app.delete("/api/v1/cloud-accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(account_id: str, user: User = Depends(require_roles("SUPER_ADMIN", "ACCOUNT_ADMIN")), repo: TenantRepository = Depends(get_tenant_repo), session: AsyncSession = Depends(get_session)) -> Response:
    account = await repo.account(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Cloud account not found")
    await repo.add_audit_event(user.id, "cloud_account.deleted", {"account_id": account.id})
    await session.delete(account)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/api/v1/organization/users", response_model=list[UserOut])
async def organization_users(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> list[User]:
    return list((await session.scalars(select(User).where(User.tenant_id == user.tenant_id, User.is_active.is_(True)).order_by(User.full_name))).all())

@app.get("/api/v1/settings", response_model=TenantSettingsOut)
async def get_tenant_settings(user: User = Depends(current_user), repo: TenantRepository = Depends(get_tenant_repo), session: AsyncSession = Depends(get_session)) -> TenantSettingsOut:
    stored = await session.get(TenantSettings, user.tenant_id)
    return TenantSettingsOut(
        daily_scans_enabled=stored.daily_scans_enabled if stored else False,
        daily_scan_hour_utc=stored.daily_scan_hour_utc if stored else 2,
        slack_alerts_enabled=stored.slack_alerts_enabled if stored else False,
        slack_webhook_configured=bool(settings.slack_webhook_url),
    )

@app.put("/api/v1/settings", response_model=TenantSettingsOut)
async def update_tenant_settings(payload: TenantSettingsUpdate, user: User = Depends(require_roles("SUPER_ADMIN", "ACCOUNT_ADMIN")), repo: TenantRepository = Depends(get_tenant_repo), session: AsyncSession = Depends(get_session)) -> TenantSettingsOut:
    stored = await session.get(TenantSettings, user.tenant_id)
    if stored is None:
        stored = TenantSettings(tenant_id=user.tenant_id)
        session.add(stored)
    if payload.slack_alerts_enabled and not settings.slack_webhook_url:
        raise HTTPException(status_code=400, detail="Configure SLACK_WEBHOOK_URL on the server before enabling alerts")
    for field in ("daily_scans_enabled", "daily_scan_hour_utc", "slack_alerts_enabled"):
        value = getattr(payload, field)
        if value is not None:
            setattr(stored, field, value)
    await repo.add_audit_event(user.id, "tenant.settings_updated", {
        "daily_scans_enabled": str(stored.daily_scans_enabled),
        "daily_scan_hour_utc": str(stored.daily_scan_hour_utc),
        "slack_alerts_enabled": str(stored.slack_alerts_enabled),
    })
    await session.commit()
    return TenantSettingsOut(
        daily_scans_enabled=stored.daily_scans_enabled,
        daily_scan_hour_utc=stored.daily_scan_hour_utc,
        slack_alerts_enabled=stored.slack_alerts_enabled,
        slack_webhook_configured=bool(settings.slack_webhook_url),
    )

@app.get("/api/v1/audit-logs", response_model=list[AuditLogOut])
async def audit_logs(limit: int = Query(default=100, ge=1, le=500), user: User = Depends(require_roles("SUPER_ADMIN", "ACCOUNT_ADMIN", "AUDITOR")), repo: TenantRepository = Depends(get_tenant_repo), session: AsyncSession = Depends(get_session)) -> list[AuditLog]:
    statement = (
        select(AuditLog)
        .where(AuditLog.tenant_id == user.tenant_id)
        .order_by(desc(AuditLog.created_at))
        .limit(limit)
    )
    return list((await session.scalars(statement)).all())

@app.post("/api/v1/cloud-accounts/onboard", response_model=AccountOut, status_code=201)
async def onboard_account(payload: AccountOnboardIn, user: User = Depends(require_roles("SUPER_ADMIN", "ACCOUNT_ADMIN")), repo: TenantRepository = Depends(get_tenant_repo), session: AsyncSession = Depends(get_session)) -> CloudAccount:
    if payload.role_arn.split(":")[4] != payload.account_number: raise HTTPException(status_code=422, detail="Account number must match the IAM role ARN")
    try:
        await asyncio.to_thread(validate_aws_account, payload.role_arn, payload.external_id, payload.account_number)
    except AwsAuditError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    account = CloudAccount(tenant_id=user.tenant_id, account_alias=payload.account_alias, account_number=payload.account_number, role_arn=payload.role_arn, external_id=payload.external_id, connection_status="ACTIVE", validation_mode="aws_sts_readonly")
    session.add(account)
    try:
        await session.flush()
        await repo.add_audit_event(user.id, "cloud_account.onboarded", {"account_id": account.id, "validation": "aws_sts_readonly"})
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="This role is already connected for the current tenant") from exc
    return account

@app.post("/api/v1/scans", response_model=ScanOut, status_code=202)
async def start_scan(payload: ScanStartIn, user: User = Depends(require_roles("SUPER_ADMIN", "ACCOUNT_ADMIN", "ANALYST")), repo: TenantRepository = Depends(get_tenant_repo), session: AsyncSession = Depends(get_session)) -> Scan:
    if await repo.account(payload.cloud_account_id) is None: raise HTTPException(status_code=404, detail="Cloud account not found")
    scan = Scan(tenant_id=user.tenant_id, cloud_account_id=payload.cloud_account_id)
    session.add(scan); await session.flush()
    await repo.add_audit_event(user.id, "scan.started", {"scan_id": scan.id, "account_id": payload.cloud_account_id})
    await session.commit()
    redis = await get_queue()
    try:
        enqueued = await enqueue_scan(redis, scan.id, user.tenant_id)
        if not enqueued:
            scan.status, scan.partial = "failed", True
            scan.error_summary = "Scan job was not accepted by the queue."
            await session.commit()
            raise HTTPException(status_code=503, detail=scan.error_summary)
    except HTTPException:
        raise
    except Exception as exc:
        scan.status, scan.partial = "failed", True
        scan.error_summary = "Scan queue is unavailable; retry after Redis/worker recovery."
        await session.commit()
        raise HTTPException(status_code=503, detail=scan.error_summary) from exc
    finally:
        await redis.aclose()
    return scan

@app.get("/api/v1/scans", response_model=list[ScanOut])
async def scans(repo: TenantRepository = Depends(get_tenant_repo)): return await repo.scans()

@app.get("/api/v1/scans/{scan_id}", response_model=ScanOut)
async def get_scan(scan_id: str, repo: TenantRepository = Depends(get_tenant_repo)) -> Scan:
    scan = await repo.scan(scan_id)
    if scan is None: raise HTTPException(status_code=404, detail="Scan not found")
    return scan

@app.get("/api/v1/findings", response_model=list[FindingOut])
async def findings(repo: TenantRepository = Depends(get_tenant_repo)): return await repo.findings()

@app.patch("/api/v1/findings/{finding_id}", response_model=FindingOut)
async def set_finding_status(finding_id: str, payload: FindingUpdateIn, user: User = Depends(require_roles("SUPER_ADMIN", "ACCOUNT_ADMIN", "ANALYST")), repo: TenantRepository = Depends(get_tenant_repo), session: AsyncSession = Depends(get_session)) -> Finding:
    finding = await repo.finding(finding_id)
    if finding is None: raise HTTPException(status_code=404, detail="Finding not found")
    changes: dict[str, str] = {}
    if payload.status is not None:
        finding.status = payload.status
        changes["status"] = payload.status
    if "assigned_to_user_id" in payload.model_fields_set:
        if payload.assigned_to_user_id is not None:
            assignee = await session.scalar(
                select(User).where(
                    User.id == payload.assigned_to_user_id,
                    User.tenant_id == user.tenant_id,
                    User.is_active.is_(True),
                )
            )
            if assignee is None:
                raise HTTPException(status_code=404, detail="Assignee not found in this organization")
        finding.assigned_to_user_id = payload.assigned_to_user_id
        changes["assigned_to_user_id"] = payload.assigned_to_user_id or ""
    if "due_at" in payload.model_fields_set:
        if payload.due_at is not None and payload.due_at.tzinfo is None:
            raise HTTPException(status_code=422, detail="Due dates must include a timezone")
        finding.due_at = payload.due_at
        changes["due_at"] = payload.due_at.isoformat() if payload.due_at else ""
    if not changes:
        raise HTTPException(status_code=422, detail="Provide at least one finding field to update")
    await repo.add_audit_event(user.id, "finding.updated", {"finding_id": finding_id, **changes})
    await session.commit()
    return finding

@app.get("/api/v1/dashboard", response_model=DashboardOut)
async def dashboard(user: User = Depends(current_user), repo: TenantRepository = Depends(get_tenant_repo), session: AsyncSession = Depends(get_session)) -> DashboardOut:
    rows = (await session.execute(select(Finding.severity, func.count(Finding.id)).where(Finding.tenant_id == user.tenant_id, Finding.status == "OPEN").group_by(Finding.severity))).all()
    breakdown = {severity.lower(): count for severity, count in rows}
    for severity in ("critical", "high", "medium", "low"): breakdown.setdefault(severity, 0)
    total = sum(breakdown.values()); score = min(100, breakdown["critical"] * 25 + breakdown["high"] * 12 + breakdown["medium"] * 5 + breakdown["low"] * 2)
    level = "Critical" if score >= 75 else "High" if score >= 45 else "Medium" if score >= 20 else "Low Risk"
    affected_resources = await session.scalar(select(func.count(func.distinct(Finding.resource_arn))).where(Finding.tenant_id == user.tenant_id, Finding.status == "OPEN")) or 0
    return DashboardOut(threat_score=score, risk_level=level, total_findings=total, findings_delta="+0 from last scan", resources_with_findings=affected_resources, high_severity_findings=breakdown["high"] + breakdown["critical"], severity_breakdown=breakdown)

@app.get("/api/v1/compliance", response_model=list[FrameworkOut])
async def compliance(user: User = Depends(current_user), repo: TenantRepository = Depends(get_tenant_repo)) -> list[FrameworkOut]:
    records = await repo.findings()
    accounts = list(await repo.accounts())
    scans = list(await repo.scans())
    return build_frameworks(list(records), accounts, scans)

@app.get("/api/v1/reports/summary")
async def report_summary(user: User = Depends(current_user), repo: TenantRepository = Depends(get_tenant_repo), session: AsyncSession = Depends(get_session)) -> Response:
    summary = await dashboard(user, repo, session)
    return Response(content=f"CloudGuard GRC audit summary\nOpen findings: {summary.total_findings}\nRisk score: {summary.threat_score}\n", media_type="text/plain", headers={"Content-Disposition": "attachment; filename=cloudguard-audit-summary.txt"})

@app.get("/api/v1/reports/export")
@app.get("/api/v1/reports/compliance/{framework_id}/export")
async def export_audit_report(framework_id: str | None = None, user: User = Depends(current_user), repo: TenantRepository = Depends(get_tenant_repo), session: AsyncSession = Depends(get_session)) -> Response:
    accounts = await repo.accounts()
    framework_list = await compliance(user, repo)
    findings = await repo.findings()
    selected_framework_id = framework_id if framework_id and framework_id != "all" else None
    if selected_framework_id:
        rule_ids = framework_rule_ids(selected_framework_id)
        if rule_ids is None:
            raise HTTPException(status_code=404, detail="Compliance framework not found")
        framework_list = [item for item in framework_list if item.id == selected_framework_id]
        findings = [finding for finding in findings if finding.rule_id in rule_ids]
    open_findings = [finding for finding in findings if finding.status == "OPEN"]
    severity_counts = {severity: sum(finding.severity == severity for finding in open_findings) for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW")}
    threat_score = min(100, severity_counts["CRITICAL"] * 25 + severity_counts["HIGH"] * 12 + severity_counts["MEDIUM"] * 5 + severity_counts["LOW"] * 2)
    risk_level = "Critical" if threat_score >= 75 else "High" if threat_score >= 45 else "Medium" if threat_score >= 20 else "Low Risk"

    tenant = await session.get(Tenant, user.tenant_id)
    org_name = tenant.name if tenant else "Enterprise Organization"

    html_content = generate_executive_html_report(
        organization_name=org_name,
        threat_score=threat_score,
        risk_level=risk_level,
        accounts=accounts,
        frameworks=framework_list,
        findings=open_findings
    )
    return Response(content=html_content, media_type="text/html", headers={"Content-Disposition": "inline; filename=cloudguard-audit-report.html"})

@app.get("/api/v1/reports/export.pdf")
@app.get("/api/v1/reports/compliance/{framework_id}/export.pdf")
async def export_audit_pdf(
    framework_id: str | None = None,
    user: User = Depends(current_user),
    repo: TenantRepository = Depends(get_tenant_repo),
    session: AsyncSession = Depends(get_session),
) -> Response:
    framework_list = await compliance(user, repo)
    all_findings = await repo.findings()
    selected_framework_id = framework_id if framework_id and framework_id != "all" else None

    if selected_framework_id:
        rule_ids = framework_rule_ids(selected_framework_id)
        if rule_ids is None:
            raise HTTPException(status_code=404, detail="Compliance framework not found")
        frameworks = [item for item in framework_list if item.id == selected_framework_id]
        findings = [finding for finding in all_findings if finding.status == "OPEN" and finding.rule_id in rule_ids]
        severity_counts = {
            severity: sum(f.severity == severity for f in findings)
            for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
        }
        threat_score = min(
            100,
            severity_counts["CRITICAL"] * 25
            + severity_counts["HIGH"] * 12
            + severity_counts["MEDIUM"] * 5
            + severity_counts["LOW"] * 2,
        )
        risk_level = (
            "Critical"
            if threat_score >= 75
            else "High"
            if threat_score >= 45
            else "Medium"
            if threat_score >= 20
            else "Low Risk"
        )
        filename = f"cloudguard-audit-report-{selected_framework_id}.pdf"
    else:
        summary = await dashboard(user, repo, session)
        frameworks = framework_list
        findings = [finding for finding in all_findings if finding.status == "OPEN"]
        threat_score = summary.threat_score
        risk_level = summary.risk_level
        filename = "cloudguard-audit-report.pdf"

    tenant = await session.get(Tenant, user.tenant_id)
    pdf_bytes = generate_audit_pdf(
        organization_name=tenant.name if tenant else "CloudGuard Organization",
        threat_score=threat_score,
        risk_level=risk_level,
        frameworks=frameworks,
        findings=findings,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

class SecretScanRequest(BaseModel):
    target_path: str = "."
    content: str | None = None

@app.post("/api/v1/scans/secrets")
async def scan_secrets_endpoint(payload: SecretScanRequest, user: User = Depends(current_user), repo: TenantRepository = Depends(get_tenant_repo)) -> list[dict]:
    if payload.content:
        return scan_content(payload.content, filename="manual_input.txt")
    root = Path(settings.secret_scan_root).resolve()
    target = (root / payload.target_path).resolve()
    if not target.is_relative_to(root):
        raise HTTPException(status_code=403, detail="The scan path must be inside the configured scan root")
    return scan_local_path(str(target))
