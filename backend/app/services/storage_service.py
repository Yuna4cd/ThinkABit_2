from __future__ import annotations

import boto3
from botocore.exceptions import ClientError


class S3StorageService:
    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool,
        auto_create_bucket: bool,
    ) -> None:
        self.bucket = bucket
        self.auto_create_bucket = auto_create_bucket
        self._bucket_ready = False
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            use_ssl=secure,
        )

    def put_object(self, *, file_bytes: bytes, key: str, content_type: str) -> None:
        self._ensure_bucket()
        self._client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
        )

    def _ensure_bucket(self) -> None:
        if self._bucket_ready:
            return

        try:
            self._client.head_bucket(Bucket=self.bucket)
            self._bucket_ready = True
            return
        except ClientError as exc:
            if not self.auto_create_bucket:
                raise

            status_code = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            error_code = str(exc.response.get("Error", {}).get("Code", ""))
            if status_code not in {404, 400} and error_code not in {
                "404",
                "NoSuchBucket",
                "NotFound",
            }:
                raise

        self._client.create_bucket(Bucket=self.bucket)
        self._bucket_ready = True
