import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.limiter import limiter
from app.core.security import get_current_admin
from app.models.user import AdminUser
from app.models.work import Work
from app.schemas.work import WorkCreate, WorkDetail, WorkUpdate
from app.schemas.settings import SiteSettingsResponse, SiteSettingsUpdate
from app.services.s3 import upload_file_to_s3
from app.services.settings import get_site_settings

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin)],
)


# ── Works CRUD ──────────────────────────────────────────────

@router.get("/works", response_model=list[WorkDetail])
async def admin_list_works(db: AsyncSession = Depends(get_db)):
    stmt = select(Work).order_by(Work.sort_order, Work.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/works", response_model=WorkDetail, status_code=201)
async def admin_create_work(data: WorkCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Work).where(Work.slug == data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Slug already exists")
    work = Work(**data.model_dump())
    db.add(work)
    await db.flush()
    await db.refresh(work)
    return work


@router.get("/works/{work_id}", response_model=WorkDetail)
async def admin_get_work(work_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    work = await db.get(Work, work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    return work


@router.patch("/works/{work_id}", response_model=WorkDetail)
async def admin_update_work(
    work_id: uuid.UUID, data: WorkUpdate, db: AsyncSession = Depends(get_db),
):
    work = await db.get(Work, work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(work, field, value)
    await db.flush()
    await db.refresh(work)
    return work


@router.delete("/works/{work_id}", status_code=204)
async def admin_delete_work(work_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    work = await db.get(Work, work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    await db.delete(work)
    return None


# ── Server-side upload ──────────────────────────────────────

@router.post("/upload")
@limiter.limit("30/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    folder: str = Form("works/"),
):
    """Upload file through the server to S3 bucket."""
    # Validate content type
    allowed = {
        "image/jpeg", "image/png", "image/webp", "image/gif",
        "image/heic", "image/heif",
        "video/mp4", "video/webm", "video/quicktime",
    }
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail=f"Content type {file.content_type!r} not allowed")

    # Validate folder
    folder = folder.strip().strip("/") + "/"
    if ".." in folder:
        raise HTTPException(status_code=400, detail="Invalid folder path")

    # Read and upload
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(status_code=400, detail="File too large (max 20MB)")

    result = upload_file_to_s3(
        file_data=data,
        filename=file.filename or "upload",
        content_type=file.content_type,
        folder=folder,
    )
    return result


# ── Site Settings ───────────────────────────────────────────

@router.get("/settings", response_model=SiteSettingsResponse)
async def admin_get_settings(db: AsyncSession = Depends(get_db)):
    return await get_site_settings(db)


@router.patch("/settings", response_model=SiteSettingsResponse)
async def admin_update_settings(
    data: SiteSettingsUpdate, db: AsyncSession = Depends(get_db),
):
    settings = await get_site_settings(db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    await db.flush()
    await db.refresh(settings)
    return settings
