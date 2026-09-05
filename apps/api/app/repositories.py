from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AuditLog, CloudAccount, Finding, Scan

class TenantRepository:
    """Every product query includes tenant_id, even where PostgreSQL RLS also applies."""
    def __init__(self, session: AsyncSession, tenant_id: str) -> None: 
        self.session = session
        self.tenant_id = tenant_id

    async def setup_rls(self) -> None:
        from sqlalchemy import text
        await self.session.execute(text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"), {"tenant_id": self.tenant_id})

    async def accounts(self) -> Sequence[CloudAccount]:  return (await self.session.scalars(select(CloudAccount).where(CloudAccount.tenant_id == self.tenant_id).order_by(CloudAccount.created_at.desc()))).all()
    async def account(self, account_id: str) -> CloudAccount | None: return await self.session.scalar(select(CloudAccount).where(CloudAccount.id == account_id, CloudAccount.tenant_id == self.tenant_id))
    async def scan(self, scan_id: str) -> Scan | None: return await self.session.scalar(select(Scan).where(Scan.id == scan_id, Scan.tenant_id == self.tenant_id))
    async def scans(self) -> Sequence[Scan]: return (await self.session.scalars(select(Scan).where(Scan.tenant_id == self.tenant_id).order_by(Scan.created_at.desc()))).all()
    async def findings(self) -> Sequence[Finding]: return (await self.session.scalars(select(Finding).where(Finding.tenant_id == self.tenant_id).order_by(Finding.detected_at.desc()))).all()
    async def finding(self, finding_id: str) -> Finding | None: return await self.session.scalar(select(Finding).where(Finding.id == finding_id, Finding.tenant_id == self.tenant_id))
    async def add_audit_event(self, actor_id: str | None, event_type: str, details: dict[str, str]) -> None: self.session.add(AuditLog(tenant_id=self.tenant_id, actor_id=actor_id, event_type=event_type, details=details))
