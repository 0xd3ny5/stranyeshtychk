from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import SiteSettings


async def get_site_settings(db: AsyncSession) -> SiteSettings:
    """Get the single SiteSettings row, creating it if it doesn't exist."""
    result = await db.execute(select(SiteSettings).where(SiteSettings.id == 1))
    settings = result.scalar_one_or_none()

    if not settings:
        settings = SiteSettings(id=1)
        db.add(settings)
        await db.flush()
        await db.refresh(settings)

    return settings
