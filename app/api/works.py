from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.limiter import limiter
from app.models.work import Work
from app.schemas.work import WorkDetail, WorkListItem

router = APIRouter(prefix="/api/works", tags=["works"])


@router.get("", response_model=list[WorkListItem])
@limiter.limit("60/minute")
async def list_works(
    request: Request,
    tag: str | None = Query(None, description="Filter by tag"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Work).order_by(Work.sort_order, Work.created_at.desc())

    if tag:
        stmt = stmt.where(Work.tags.any(tag))

    result = await db.execute(stmt)
    works = result.scalars().all()
    return works


@router.get("/{slug}", response_model=WorkDetail)
@limiter.limit("60/minute")
async def get_work(request: Request, slug: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Work).where(Work.slug == slug)
    result = await db.execute(stmt)
    work = result.scalar_one_or_none()

    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    return work
