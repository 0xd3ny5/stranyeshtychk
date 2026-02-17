import re
import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{1,118}[a-z0-9]$")


class WorkBase(BaseModel):
    title: str
    slug: str
    description: str | None = None
    year: int | None = None
    tags: list[str] = []
    span_class: str = "span-4"
    is_tall: bool = False
    sort_order: int = 0

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.strip().lower()
        if not SLUG_RE.match(v):
            raise ValueError(
                "Slug must be 3-120 chars, only a-z 0-9 and hyphens, "
                "must start/end with alphanumeric"
            )
        return v

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int | None) -> int | None:
        if v is not None and (v < 1900 or v > 2100):
            raise ValueError("Year must be between 1900 and 2100")
        return v


class WorkCreate(WorkBase):
    cover_url: str = ""
    gallery_urls: list[str] = []


class WorkUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    year: int | None = None
    tags: list[str] | None = None
    cover_url: str | None = None
    gallery_urls: list[str] | None = None
    span_class: str | None = None
    is_tall: bool | None = None
    sort_order: int | None = None


class WorkListItem(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    cover_url: str
    tags: list[str]
    year: int | None
    span_class: str
    is_tall: bool
    sort_order: int

    model_config = {"from_attributes": True}


class WorkDetail(WorkListItem):
    description: str | None
    gallery_urls: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

