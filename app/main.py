from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.limiter import limiter
from app.core.security import _RedirectException
from app.services.s3 import get_presigned_read_url
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.database import async_session_factory
    from app.core.security import hash_password
    from app.models.user import AdminUser
    from sqlalchemy import select

    async with async_session_factory() as session:
        stmt = select(AdminUser).where(AdminUser.email == settings.ADMIN_EMAIL)
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            admin = AdminUser(
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            print(f"✓ Seeded admin user: {settings.ADMIN_EMAIL}")
        else:
            print(f"✓ Admin user exists: {settings.ADMIN_EMAIL}")

    yield


app = FastAPI(
    title="Artist Portfolio",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
)

# ── Rate limiter ────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Auth redirect handler ──────────────────────────────────
@app.exception_handler(_RedirectException)
async def redirect_to_login(request: Request, exc: _RedirectException):
    return RedirectResponse(url="/admin/login", status_code=303)

# ── CORS ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── Static files ────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ── Routers ─────────────────────────────────────────────────
from app.api.works import router as works_api_router
from app.api.admin_api import router as admin_api_router
from app.admin.pages import router as admin_pages_router
from app.api.pages import router as pages_router

app.include_router(works_api_router)
app.include_router(admin_api_router)
app.include_router(admin_pages_router)
app.include_router(pages_router)


# ── Custom 404 ──────────────────────────────────────────────
@app.exception_handler(404)
async def custom_404(request: Request, exc):
    from app.core.templates import templates
    return templates.TemplateResponse(
        "public/404.html", {"request": request}, status_code=404,
    )
