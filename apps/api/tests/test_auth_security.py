import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import desc, select

from app.db import SessionLocal
from app.main import app
from app.models import Session, User

pytestmark = pytest.mark.usefixtures("clean_database_fixture")


@pytest.mark.asyncio
async def test_login_lockout_persists_and_remember_me_is_session_scoped():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        registered = await client.post(
            "/api/v1/auth/register",
            json={
                "organization_name": "__CLOUDGUARD_TEST__:auth-lockout",
                "full_name": "Auth Test",
                "email": "auth-lockout@example.com",
                "password": "SecurePassword123!",
            },
        )
        assert registered.status_code == 201

        login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "auth-lockout@example.com",
                "password": "SecurePassword123!",
                "remember_me": False,
            },
        )
        assert login.status_code == 200
        set_cookie = login.headers.get_list("set-cookie")
        assert any("access_token=" in cookie and "Max-Age" not in cookie for cookie in set_cookie)
        assert any("refresh_token=" in cookie and "Max-Age" not in cookie for cookie in set_cookie)

        for _ in range(5):
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "auth-lockout@example.com", "password": "wrong-password"},
            )
            assert response.status_code == 401

        correct_password = await client.post(
            "/api/v1/auth/login",
            json={"email": "auth-lockout@example.com", "password": "SecurePassword123!"},
        )
        assert correct_password.status_code == 401

    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.email == "auth-lockout@example.com"))
        saved_session = await session.scalar(
            select(Session)
            .where(Session.user_id == user.id)
            .order_by(desc(Session.created_at))
        )
        assert user is not None
        assert user.locked_until is not None
        assert saved_session is not None
        assert saved_session.remember_me is False
