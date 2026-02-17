from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.limiter import limiter
from app.models.work import Work
from app.schemas.work import WorkDetail, WorkListItem
from app.services.s3 import get_presigned_read_url

router = APIRouter(prefix="/api/works", tags=["works"])


def _resolve_urls(work_dict: dict) -> dict:
    """Convert S3 keys to presigned read URLs in API response."""
    if work_dict.get("cover_url"):
        work_dict["cover_url"] = get_presigned_read_url(work_dict["cover_url"])
    if work_dict.get("gallery_urls"):
        work_dict["gallery_urls"] = [get_presigned_read_url(u) for u in work_dict["gallery_urls"]]
    return work_dict


@router.get("", response_model=list[WorkListItem])
@limiter.limit("60/minute")
async def list_works(
    request: Request,
    tag: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Work).order_by(Work.sort_order, Work.created_at.desc())
    if tag:
        stmt = stmt.where(Work.tags.any(tag))
    result = await db.execute(stmt)
    works = result.scalars().all()
    return [_resolve_urls(WorkListItem.model_validate(w).model_dump()) for w in works]


@router.get("/{slug}", response_model=WorkDetail)
@limiter.limit("60/minute")
async def get_work(request: Request, slug: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Work).where(Work.slug == slug)
    result = await db.execute(stmt)
    work = result.scalar_one_or_none()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    return _resolve_urls(WorkDetail.model_validate(work).model_dump())
