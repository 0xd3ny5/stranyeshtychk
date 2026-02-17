"""Shared Jinja2 templates instance with custom filters."""
from fastapi.templating import Jinja2Templates
from app.services.s3 import get_presigned_read_url


def _safe_s3url(key: str, expires: int = 3600) -> str:
    """Jinja2 filter: convert S3 key to presigned read URL. Never raises."""
    try:
        if not key:
            return ""
        return get_presigned_read_url(key, expires)
    except Exception:
        return key  # fallback to raw key


templates = Jinja2Templates(directory="app/templates")
templates.env.filters["s3url"] = _safe_s3url
