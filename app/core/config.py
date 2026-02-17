import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me"
    ALLOWED_ORIGINS: str = "http://localhost:8000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/portfolio"

    # S3 / Bucket — reads S3_* first, falls back to AWS_* (Railway auto-injects)
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "portfolio-media"
    S3_REGION: str = "auto"
    CDN_BASE_URL: str = ""

    # Admin seed
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "changeme123"

    # Session
    SESSION_MAX_AGE: int = 60 * 60 * 24 * 7  # 7 days

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Fallback: if S3_* empty, try AWS_* env vars (Railway bucket auto-injects these)
        if not self.S3_ENDPOINT_URL:
            self.S3_ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL", "")
        if not self.S3_ACCESS_KEY_ID:
            self.S3_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
        if not self.S3_SECRET_ACCESS_KEY:
            self.S3_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
        if not self.S3_BUCKET_NAME or self.S3_BUCKET_NAME == "portfolio-media":
            self.S3_BUCKET_NAME = os.environ.get("AWS_S3_BUCKET_NAME", self.S3_BUCKET_NAME)
        if not self.S3_REGION or self.S3_REGION == "auto":
            self.S3_REGION = os.environ.get("AWS_DEFAULT_REGION", "auto")

    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
