from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.schemas.upload import (
    ColumnSchema,
    FileMeta,
    MissingSummary,
    Shape,
    StorageRef,
    UploadResponse,
)


class UploadService:
    def __init__(self, raw_bucket: str = "thinkabit-raw") -> None:
        self.raw_bucket = raw_bucket

    async def handle_upload(
        self,
        file: UploadFile,
        session_id: str | None,
        preview_rows: int,
    ) -> UploadResponse:
        dataset_id = f"ds_{uuid4().hex}"
        extension = Path(file.filename or "").suffix.lower().lstrip(".")
        now = datetime.now(UTC)

        object_key = (
            f"raw/{now.year:04d}/{now.month:02d}/{now.day:02d}/{dataset_id}/{file.filename}"
        )

        file_size = await self._estimate_file_size(file)
        await file.seek(0)

        return UploadResponse(
            dataset_id=dataset_id,
            status="uploaded",
            session_id=session_id,
            file_meta=FileMeta(
                original_filename=file.filename or "unknown",
                extension=extension,
                mime_type=file.content_type or "application/octet-stream",
                size_bytes=file_size,
            ),
            shape=Shape(rows=0, columns=0),
            schema_=[],
            preview=[],
            missing_summary=MissingSummary(rows_with_missing=0, total_missing_cells=0),
            storage=StorageRef(
                provider="s3-compatible",
                bucket=self.raw_bucket,
                object_key=object_key,
            ),
            warnings=[
                "Validation, storage write, and dataframe parsing are not implemented yet.",
                f"Requested preview_rows={preview_rows} will be applied after parser integration.",
            ],
        )

    async def _estimate_file_size(self, file: UploadFile) -> int:
        content = await file.read()
        return len(content)
