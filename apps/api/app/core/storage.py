import contextlib
import uuid
from functools import lru_cache

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.core.config import get_settings
from app.core.responses import AppError

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


@lru_cache
def get_s3_client():
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        region_name="us-east-1",
    )


def ensure_bucket_exists() -> None:
    settings = get_settings()
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=settings.s3_bucket_name)
    except ClientError:
        client.create_bucket(Bucket=settings.s3_bucket_name)


async def upload_image_file(file: UploadFile, key_prefix: str) -> str:
    """Validates and uploads an image (NFR: file type/size validation
    per SRS Part 3 §16), returning its public URL.

    Bucket-level public-read is set up by the `minio-init` service in
    docker-compose.yml for local dev; production would front this with
    a CDN, which is unaffected by this function's return shape (both
    are just a URL).
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise AppError(
            status_code=400,
            code="UNSUPPORTED_FILE_TYPE",
            message=f"Unsupported image type: {file.content_type}. Allowed: JPEG, PNG, WEBP.",
        )

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise AppError(
            status_code=400,
            code="FILE_TOO_LARGE",
            message=f"Image exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)}MB limit.",
        )

    settings = get_settings()
    extension = ALLOWED_CONTENT_TYPES[file.content_type]
    key = f"{key_prefix}/{uuid.uuid4()}.{extension}"

    ensure_bucket_exists()
    try:
        get_s3_client().put_object(
            Bucket=settings.s3_bucket_name, Key=key, Body=content, ContentType=file.content_type
        )
    except ClientError as exc:
        raise AppError(
            status_code=500, code="STORAGE_ERROR", message="Could not store image."
        ) from exc

    return f"{settings.s3_endpoint_url}/{settings.s3_bucket_name}/{key}"


def delete_image_url(url: str) -> None:
    """Best-effort delete — a missing/unparseable object is not an error
    worth failing the caller's request over."""
    settings = get_settings()
    prefix = f"{settings.s3_endpoint_url}/{settings.s3_bucket_name}/"
    if not url.startswith(prefix):
        return

    key = url[len(prefix) :]
    with contextlib.suppress(ClientError):
        get_s3_client().delete_object(Bucket=settings.s3_bucket_name, Key=key)
