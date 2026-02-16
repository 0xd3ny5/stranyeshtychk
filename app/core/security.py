from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import AdminUser

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

SESSION_COOKIE = "session"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_session_token(user_id: int) -> str:
    return serializer.dumps({"uid": user_id})


def decode_session_token(token: str) -> dict | None:
    try:
        return serializer.loads(token, max_age=settings.SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


async def get_current_admin(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    """Dependency: extracts admin user from session cookie.
    Redirects to login page if not authenticated."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise _redirect_to_login()

    payload = decode_session_token(token)
    if not payload:
        raise _redirect_to_login()

    stmt = select(AdminUser).where(
        AdminUser.id == payload["uid"],
        AdminUser.is_active.is_(True),
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise _redirect_to_login()

    return user


class _RedirectException(Exception):
    pass


def _redirect_to_login():
    """We use a custom exception + handler so the browser actually redirects."""
    return _RedirectException()
