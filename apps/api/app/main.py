import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_token, new_refresh_token, password_hash, token_digest, verify_password
from app.db import engine, get_session
from app.dependencies import current_user, require_roles, get_tenant_repo
from app.models import Base, CloudAccount, Finding, Scan, Session, Tenant, User
from app.repositories import TenantRepository
from app.schemas import AccountOnboardIn, AccountOut, ComplianceControl, DashboardOut, FindingOut, FindingStatusIn, FrameworkOut, LoginIn, RefreshIn, RegisterIn, ScanOut, ScanStartIn, TokenOut, UserOut
from app.services.compliance import build_frameworks
from app.services.reporter import generate_executive_html_report
from app.services.scanner import run_scan
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
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])

def token_response(user: User, refresh: str) -> TokenOut:
    return TokenOut(access_token=create_token(user.id, user.tenant_id, user.role, "access", settings.access_token_minutes), refresh_token=refresh, user=UserOut.model_validate(user))

async def issue_session(session: AsyncSession, user: User) -> TokenOut:
    refresh = new_refresh_token()
    session.add(Session(user_id=user.id, refresh_token_hash=token_digest(refresh), expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days)))
    await session.commit()
    return token_response(user, refresh)

@app.get("/health", response_model=HealthResponse, tags=["system"])
@app.get("/api/v1/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="cloudguard-api", environment=settings.app_env)

@app.get("/api/v1/ready", response_model=HealthResponse, tags=["system"])
async def ready(session: AsyncSession = Depends(get_session)) -> HealthResponse:
    await session.execute(select(1))
    return HealthResponse(status="ready", service="cloudguard-api", environment=settings.app_env)

@app.post("/api/v1/auth/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterIn, session: AsyncSession = Depends(get_session)) -> TokenOut:
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
    return await issue_session(session, user)

@app.post("/api/v1/auth/login", response_model=TokenOut)
async def login(payload: LoginIn, session: AsyncSession = Depends(get_session)) -> TokenOut:
    user = await session.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return await issue_session(session, user)

@app.post("/api/v1/auth/refresh", response_model=TokenOut)
async def refresh(payload: RefreshIn, session: AsyncSession = Depends(get_session)) -> TokenOut:
    saved = await session.scalar(select(Session).where(Session.refresh_token_hash == token_digest(payload.refresh_token), Session.revoked.is_(False)))
    if saved is None or saved.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user = await session.get(User, saved.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Session is no longer valid")
    saved.revoked = True
    return await issue_session(session, user)

@app.get("/api/v1/auth/me", response_model=UserOut)
async def me(user: User = Depends(current_user)) -> User: return user

@app.get("/api/v1/cloud-accounts", response_model=list[AccountOut])
async def accounts(repo: TenantRepository = Depends(get_tenant_repo)): return await repo.accounts()

@app.post("/api/v1/cloud-accounts/onboard", response_model=AccountOut, status_code=201)
async def onboard_account(payload: AccountOnboardIn, user: User = Depends(require_roles("SUPER_ADMIN", "ACCOUNT_ADMIN")), repo: TenantRepository = Depends(get_tenant_repo), session: AsyncSession = Depends(get_session)) -> CloudAccount:
    if payload.role_arn.split(":")[4] != payload.account_number: raise HTTPException(status_code=422, detail="Account number must match the IAM role ARN")
    if payload.validation_mode != "local_mock" or not settings.local_aws_simulation: raise HTTPException(status_code=400, detail="This local build only permits explicit local_mock STS validation; no live AWS calls are made")
    account = CloudAccount(tenant_id=user.tenant_id, account_alias=payload.account_alias, account_number=payload.account_number, role_arn=payload.role_arn, external_id=payload.external_id, connection_status="ACTIVE", validation_mode="local_mock")
    session.add(account)
    try:
        await session.flush()
        await repo.add_audit_event(user.id, "cloud_account.onboarded", {"account_id": account.id, "validation": "local_mock_sts"})
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
    await session.commit(); asyncio.create_task(run_scan(scan.id, user.tenant_id))
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
async def set_finding_status(finding_id: str, payload: FindingStatusIn, user: User = Depends(require_roles("SUPER_ADMIN", "ACCOUNT_ADMIN", "ANALYST")), repo: TenantRepository = Depends(get_tenant_repo), session: AsyncSession = Depends(get_session)) -> Finding:
    finding = await repo.finding(finding_id)
    if finding is None: raise HTTPException(status_code=404, detail="Finding not found")
    finding.status = payload.status; await repo.add_audit_event(user.id, "finding.status_changed", {"finding_id": finding_id, "status": payload.status}); await session.commit()
    return finding

@app.get("/api/v1/dashboard", response_model=DashboardOut)
async def dashboard(user: User = Depends(current_user), repo: TenantRepository = Depends(get_tenant_repo), session: AsyncSession = Depends(get_session)) -> DashboardOut:
    rows = (await session.execute(select(Finding.severity, func.count(Finding.id)).where(Finding.tenant_id == user.tenant_id, Finding.status == "OPEN").group_by(Finding.severity))).all()
    breakdown = {severity.lower(): count for severity, count in rows}
    for severity in ("critical", "high", "medium", "low"): breakdown.setdefault(severity, 0)
    total = sum(breakdown.values()); score = min(100, breakdown["critical"] * 25 + breakdown["high"] * 12 + breakdown["medium"] * 5 + breakdown["low"] * 2)
    level = "Critical" if score >= 75 else "High" if score >= 45 else "Medium" if score >= 20 else "Low Risk"
    return DashboardOut(threat_score=score, risk_level=level, total_findings=total, scanned_resources=str(total * 3), active_policies=breakdown["high"], severity_breakdown=breakdown)

@app.get("/api/v1/compliance", response_model=list[FrameworkOut])
async def compliance(user: User = Depends(current_user), repo: TenantRepository = Depends(get_tenant_repo)) -> list[FrameworkOut]:
    records = await repo.findings()
    account_count = len(await repo.accounts())
    return build_frameworks(list(records), account_count)

@app.get("/api/v1/reports/summary")
async def report_summary(user: User = Depends(current_user), repo: TenantRepository = Depends(get_tenant_repo), session: AsyncSession = Depends(get_session)) -> Response:
    summary = await dashboard(user, repo, session)
    return Response(content=f"CloudGuard GRC audit summary\nOpen findings: {summary.total_findings}\nRisk score: {summary.threat_score}\n", media_type="text/plain", headers={"Content-Disposition": "attachment; filename=cloudguard-audit-summary.txt"})

@app.get("/api/v1/reports/export")
@app.get("/api/v1/reports/compliance/{framework_id}/export")
async def export_audit_report(framework_id: str | None = None, user: User = Depends(current_user), repo: TenantRepository = Depends(get_tenant_repo), session: AsyncSession = Depends(get_session)) -> Response:
    summary = await dashboard(user, repo, session)
    accounts = await repo.accounts()
    framework_list = await compliance(user, repo)
    findings = await repo.findings()
    open_findings = [f for f in findings if f.status == "OPEN"]

    tenant = await session.get(Tenant, user.tenant_id)
    org_name = tenant.name if tenant else "Enterprise Organization"

    html_content = generate_executive_html_report(
        organization_name=org_name,
        threat_score=summary.threat_score,
        risk_level=summary.risk_level,
        accounts=accounts,
        frameworks=framework_list,
        findings=open_findings
    )
    return Response(content=html_content, media_type="text/html", headers={"Content-Disposition": "inline; filename=cloudguard-audit-report.html"})

class SecretScanRequest(BaseModel):
    target_path: str = "."
    content: str | None = None

@app.post("/api/v1/scans/secrets")
async def scan_secrets_endpoint(payload: SecretScanRequest, user: User = Depends(current_user), repo: TenantRepository = Depends(get_tenant_repo)) -> list[dict]:
    if payload.content:
        return scan_content(payload.content, filename="manual_input.txt")
    root = Path(settings.secret_scan_root).resolve()
    target = (root / payload.target_path).resolve() if not Path(payload.target_path).is_absolute() else Path(payload.target_path).resolve()
    if target != root and root not in target.parents:
        raise HTTPException(status_code=403, detail="The scan path must be inside the configured scan root")
    return scan_local_path(str(target))
