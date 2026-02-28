from uuid import uuid4

from fastapi import UploadFile

from app.core.config import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_PREVIEW_ROWS,
)
from app.errors import APIError


class UploadValidator:
    def validate(self, file: UploadFile, preview_rows: int) -> None:
        if preview_rows < 1 or preview_rows > MAX_PREVIEW_ROWS:
            raise self._build_error(
                code="INVALID_REQUEST",
                message="preview_rows must be between 1 and 200.",
                details={"field": "preview_rows"},
                status_code=400,
            )

        if not file.filename:
            raise self._build_error(
                code="INVALID_REQUEST",
                message="file must include a filename.",
                details={"field": "file"},
                status_code=400,
            )

        if any(char in file.filename for char in ("../", "..\\", "/", "\\")):
            raise self._build_error(
                code="UNSAFE_FILENAME",
                message="Filename contains unsafe path characters.",
                details={"field": "file.filename"},
                status_code=400,
            )

        extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if extension not in ALLOWED_EXTENSIONS:
            raise self._build_error(
                code="UNSUPPORTED_FILE_TYPE",
                message="Only csv, xlsx, json are allowed.",
                details={"allowed_extensions": sorted(ALLOWED_EXTENSIONS)},
                status_code=415,
            )

        if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
            raise self._build_error(
                code="MIME_TYPE_NOT_ALLOWED",
                message="MIME type is not allowed.",
                details={"mime_type": file.content_type},
                status_code=415,
            )

    def _build_error(
        self,
        *,
        code: str,
        message: str,
        details: dict[str, object],
        status_code: int,
    ) -> APIError:
        return APIError(
            status_code=status_code,
            code=code,
            message=message,
            details=details,
            request_id=f"req_{uuid4().hex[:8]}",
        )
