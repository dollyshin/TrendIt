from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.settings import settings


# ── User DB dependency ────────────────────────────────────────────────────────

async def get_user_db(session: AsyncSession = Depends(get_db)) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    yield SQLAlchemyUserDatabase(session, User)


# ── User manager ──────────────────────────────────────────────────────────────

class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = settings.auth_secret
    verification_token_secret = settings.auth_secret

    async def on_after_register(self, user: User, request=None) -> None:
        print(f"[auth] User {user.id} ({user.email}) registered.")

    async def on_after_forgot_password(self, user: User, token: str, request=None) -> None:
        print(f"[auth] Password reset token for {user.email}: {token}")

    async def on_after_request_verify(self, user: User, token: str, request=None) -> None:
        print(f"[auth] Verification token for {user.email}: {token}")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)


# ── JWT auth backend ──────────────────────────────────────────────────────────

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.auth_secret,
        lifetime_seconds=60 * 60 * 24 * 7,  # 7 days
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


# ── FastAPIUsers instance & reusable dependency ───────────────────────────────

fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
