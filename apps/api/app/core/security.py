import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_token(subject: str, tenant_id: str, role: str, kind: str, minutes: int) -> str:
    settings = get_settings()
    payload: dict[str, Any] = {"sub": subject, "tenant_id": tenant_id, "role": role, "kind": kind, "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes)}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_kind: str = "access") -> dict[str, Any]:
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("kind") != expected_kind:
        raise jwt.InvalidTokenError("incorrect token kind")
    return payload


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
