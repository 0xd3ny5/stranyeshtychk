from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SiteSettings(Base):
    __tablename__ = "site_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    # Header
    artist_name: Mapped[str] = mapped_column(String(100), default="Ekateryna")
    artist_subtitle: Mapped[str] = mapped_column(String(255), default="Illustrator, Amsterdam")
    artist_email: Mapped[str] = mapped_column(String(255), default="hello@ekateryna.art")

    # About page
    about_text: Mapped[str] = mapped_column(Text, default="")
    about_photo_url: Mapped[str] = mapped_column(String(512), default="")

    # Contact page
    contact_text: Mapped[str] = mapped_column(
        Text, default="For commissions, collaborations, or just to say hello:"
    )
    contact_email: Mapped[str] = mapped_column(String(255), default="hello@ekateryna.art")

    # Social links — dynamic: [{"label": "Instagram", "url": "https://..."}, ...]
    social_links: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<SiteSettings artist_name={self.artist_name!r}>"
