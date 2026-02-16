"""
Seed script — run once to populate DB with demo data.
Usage: python -m scripts.seed
"""
import asyncio
import sys
import os

# Allow running as script from scripts start directory
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import async_session_factory, engine
from app.core.security import hash_password
from app.models import Base, AdminUser, Work

settings = get_settings()

DEMO_WORKS = [
    {"slug": "midnight-garden", "title": "Midnight Garden", "tags": ["illustration"], "year": 2026, "span_class": "span-3", "is_tall": True, "sort_order": 0},
    {"slug": "urban-fragments", "title": "Urban Fragments", "tags": ["photography"], "year": 2026, "span_class": "span-2", "is_tall": True, "sort_order": 1},
    {"slug": "copper-light", "title": "Copper Light", "tags": ["illustration", "digital"], "year": 2026, "span_class": "span-4", "is_tall": False, "sort_order": 2},
    {"slug": "silent-waters", "title": "Silent Waters", "tags": ["painting"], "year": 2026, "span_class": "span-3", "is_tall": True, "sort_order": 3},
    {"slug": "folktale-series", "title": "Folktale Series", "tags": ["illustration"], "year": 2024, "span_class": "span-4", "is_tall": False, "sort_order": 4},
    {"slug": "the-wanderer", "title": "The Wanderer", "tags": ["digital"], "year": 2026, "span_class": "span-3", "is_tall": True, "sort_order": 5},
    {"slug": "neon-botanical", "title": "Neon Botanical", "tags": ["illustration", "experimental"], "year": 2026, "span_class": "span-5", "is_tall": False, "sort_order": 6},
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # Admin user
        result = await session.execute(select(AdminUser).where(AdminUser.email == settings.ADMIN_EMAIL))
        if not result.scalar_one_or_none():
            session.add(AdminUser(
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                is_active=True,
            ))
            print(f"✓ Created admin: {settings.ADMIN_EMAIL}")

        # Demo works
        for w in DEMO_WORKS:
            existing = await session.execute(select(Work).where(Work.slug == w["slug"]))
            if not existing.scalar_one_or_none():
                session.add(Work(
                    **w,
                    description="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                    cover_url="",  # Set via admin upload
                    gallery_urls=[],
                ))
                print(f"  + Work: {w['slug']}")

        await session.commit()
        print("✓ Seed complete")


if __name__ == "__main__":
    asyncio.run(seed())
