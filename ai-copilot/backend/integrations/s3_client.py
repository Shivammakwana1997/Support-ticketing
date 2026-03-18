from __future__ import annotations

from typing import Any

import aiobotocore.session

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class S3Client:
    def __init__(self) -> None:
        self._session = aiobotocore.session.get_session()

    def _get_client(self) -> Any:
        return self._session.create_client(
            "s3",
            region_name=settings.AWS_REGION,
        )

    async def upload_file(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        bucket: str | None = None,
    ) -> str:
        bucket = bucket or settings.S3_BUCKET
        logger.info("S3 upload", extra={"extra_fields": {"bucket": bucket, "key": key}})
        async with self._get_client() as client:
            await client.put_object(
                Bucket=bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        return f"s3://{bucket}/{key}"

    async def get_presigned_url(
        self,
        key: str,
        *,
        bucket: str | None = None,
        expires_in: int = 3600,
    ) -> str:
        bucket = bucket or settings.S3_BUCKET
        async with self._get_client() as client:
            url = await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )
        return url

    async def delete_file(self, key: str, *, bucket: str | None = None) -> None:
        bucket = bucket or settings.S3_BUCKET
        logger.info("S3 delete", extra={"extra_fields": {"bucket": bucket, "key": key}})
        async with self._get_client() as client:
            await client.delete_object(Bucket=bucket, Key=key)


s3_client = S3Client()
