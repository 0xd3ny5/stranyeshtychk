from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.templates import templates
from app.models.work import Work
from app.services.settings import get_site_settings

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: AsyncSession = Depends(get_db)):
    stmt = select(Work).order_by(Work.sort_order, Work.created_at.desc())
    result = await db.execute(stmt)
    works = result.scalars().all()
    site = await get_site_settings(db)
    return templates.TemplateResponse(
        "public/index.html",
        {"request": request, "works": works, "site": site},
    )


@router.get("/work/{slug}", response_class=HTMLResponse)
async def work_detail_page(
    request: Request, slug: str, db: AsyncSession = Depends(get_db),
):
    stmt = select(Work).where(Work.slug == slug)
    result = await db.execute(stmt)
    work = result.scalar_one_or_none()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    site = await get_site_settings(db)
    return templates.TemplateResponse(
        "public/work_detail.html",
        {"request": request, "work": work, "site": site},
    )
