from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.db import get_session
from app.models import User
bearer = HTTPBearer(auto_error=False)
async def current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)], session: Annotated[AsyncSession, Depends(get_session)]) -> User:
    if credentials is None: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try: claims = decode_token(credentials.credentials)
    except jwt.PyJWTError as exc: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token") from exc
    user = await session.get(User, claims["sub"])
    if user is None or not user.is_active or user.tenant_id != claims.get("tenant_id"): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session is no longer valid")
    return user
def require_roles(*roles: str):
    async def role_guard(user: Annotated[User, Depends(current_user)]) -> User:
        if user.role not in roles: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user
    return role_guard

async def get_tenant_repo(user: Annotated[User, Depends(current_user)], session: Annotated[AsyncSession, Depends(get_session)]):
    from app.repositories import TenantRepository
    repo = TenantRepository(session, user.tenant_id)
    await repo.setup_rls()
    return repo
