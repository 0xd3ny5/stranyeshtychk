import uuid

import boto3
from botocore.config import Config

from app.core.config import get_settings

settings = get_settings()


def _get_s3_client():
    kwargs = {
        "region_name": settings.S3_REGION or "auto",
        "config": Config(signature_version="s3v4"),
    }
    # If explicit keys provided, use them; otherwise boto3 reads AWS_* env vars
    if settings.S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
    if settings.S3_ACCESS_KEY_ID:
        kwargs["aws_access_key_id"] = settings.S3_ACCESS_KEY_ID
    if settings.S3_SECRET_ACCESS_KEY:
        kwargs["aws_secret_access_key"] = settings.S3_SECRET_ACCESS_KEY

    return boto3.client("s3", **kwargs)


def upload_file_to_s3(
    file_data: bytes,
    filename: str,
    content_type: str,
    folder: str = "works/",
) -> dict:
    """
    Upload file through the server to S3/bucket.
    Returns: {"public_url": ..., "key": ...}
    """
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()

    unique_name = f"{uuid.uuid4().hex}{ext}"
    key = f"{folder}{unique_name}"

    client = _get_s3_client()
    client.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=key,
        Body=file_data,
        ContentType=content_type,
    )

    cdn_base = settings.CDN_BASE_URL.rstrip("/")
    public_url = f"{cdn_base}/{key}"

    return {"public_url": public_url, "key": key}


def delete_s3_object(key: str) -> None:
    client = _get_s3_client()
    client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
