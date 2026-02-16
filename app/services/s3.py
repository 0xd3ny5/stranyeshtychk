import uuid
from urllib.parse import urljoin

import boto3
from botocore.config import Config

from app.core.config import get_settings

settings = get_settings()


def _get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL or None,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION,
        config=Config(signature_version="s3v4"),
    )


def generate_presigned_upload(
    filename: str,
    content_type: str,
    folder: str = "works/",
) -> dict:
    """
    Generate a presigned PUT URL for direct browser upload to S3/B2.

    Returns: {"upload_url": ..., "public_url": ..., "key": ...}
    """
    # Sanitise filename: keep extension, replace name with uuid
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()

    unique_name = f"{uuid.uuid4().hex}{ext}"
    key = f"{folder}{unique_name}"

    client = _get_s3_client()
    upload_url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=600,  # 10 minutes
    )

    # Public URL via CDN
    cdn_base = settings.CDN_BASE_URL.rstrip("/")
    public_url = f"{cdn_base}/{key}"

    return {
        "upload_url": upload_url,
        "public_url": public_url,
        "key": key,
    }


def delete_s3_object(key: str) -> None:
    """Delete an object from S3/B2 by key."""
    client = _get_s3_client()
    client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
