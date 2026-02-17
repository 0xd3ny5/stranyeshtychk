from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.security import (
    SESSION_COOKIE,
    create_session_token,
    decode_session_token,
    get_current_admin,
    verify_password,
)
from app.models.user import AdminUser
from app.models.work import Work
from app.services.settings import get_site_settings
from app.services.s3 import get_presigned_read_url

settings = get_settings()
router = APIRouter(prefix="/admin", tags=["admin-pages"])
templates = Jinja2Templates(directory="app/templates")

# Register s3url filter for admin templates too
templates.env.filters["s3url"] = get_presigned_read_url


# ── Auth pages ──────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request})


@router.post("/login")
@limiter.limit("5/minute")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AdminUser).where(AdminUser.email == email, AdminUser.is_active.is_(True))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": "Invalid email or password"},
            status_code=400,
        )

    token = create_session_token(user.id)
    response = RedirectResponse(url="/admin/", status_code=303)
    response.set_cookie(
        SESSION_COOKIE, token,
        max_age=settings.SESSION_MAX_AGE,
        httponly=True, samesite="lax",
        secure=settings.APP_ENV == "production",
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response


# ── Dashboard ───────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Work).order_by(Work.sort_order, Work.created_at.desc())
    result = await db.execute(stmt)
    works = result.scalars().all()

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "works": works, "admin": admin, "settings": settings},
    )


@router.get("/works/new", response_class=HTMLResponse)
async def new_work_page(
    request: Request, admin: AdminUser = Depends(get_current_admin),
):
    return templates.TemplateResponse(
        "admin/work_form.html",
        {"request": request, "work": None, "admin": admin, "settings": settings},
    )


@router.get("/works/{work_id}/edit", response_class=HTMLResponse)
async def edit_work_page(
    request: Request, work_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    import uuid as _uuid
    work = await db.get(Work, _uuid.UUID(work_id))
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    return templates.TemplateResponse(
        "admin/work_form.html",
        {"request": request, "work": work, "admin": admin, "settings": settings},
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    site = await get_site_settings(db)
    return templates.TemplateResponse(
        "admin/settings.html",
        {"request": request, "site": site, "admin": admin, "settings": settings},
    )
