import csv
import io
import json
import zipfile
from urllib.parse import unquote
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE_BYTES,
    MAX_PREVIEW_ROWS,
    MIME_TYPES_BY_EXTENSION,
)
from app.errors import APIError


class UploadValidator:
    async def validate(self, file: UploadFile, preview_rows: int) -> None:
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

        decoded_filename = unquote(file.filename)
        if any(
            token in file.filename or token in decoded_filename
            for token in ("../", "..\\", "/", "\\")
        ):
            raise self._build_error(
                code="UNSAFE_FILENAME",
                message="Filename contains unsafe path characters.",
                details={"field": "file.filename"},
                status_code=400,
            )
        if any(
            ord(char) < 32 or ord(char) == 127
            for char in f"{file.filename}{decoded_filename}"
        ):
            raise self._build_error(
                code="UNSAFE_FILENAME",
                message="Filename contains control characters.",
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
        if not file.content_type:
            raise self._build_error(
                code="MIME_TYPE_NOT_ALLOWED",
                message="MIME type is required.",
                details={"mime_type": file.content_type},
                status_code=415,
            )

        if file.content_type and file.content_type not in MIME_TYPES_BY_EXTENSION[extension]:
            raise self._build_error(
                code="MIME_EXTENSION_MISMATCH",
                message="MIME type does not match file extension.",
                details={"extension": extension, "mime_type": file.content_type},
                status_code=415,
            )

        content = await file.read(MAX_FILE_SIZE_BYTES + 1)
        if len(content) == 0:
            raise self._build_error(
                code="EMPTY_FILE",
                message="Uploaded file is empty.",
                details={},
                status_code=422,
            )
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise self._build_error(
                code="FILE_TOO_LARGE",
                message="File size exceeds 25MB limit.",
                details={"max_bytes": MAX_FILE_SIZE_BYTES},
                status_code=413,
            )

        if not self._is_content_consistent_with_extension(extension, content):
            raise self._build_error(
                code="MIME_EXTENSION_MISMATCH",
                message="File content does not match the declared extension.",
                details={"extension": extension},
                status_code=415,
            )

        await file.seek(0)

    def _is_content_consistent_with_extension(self, extension: str, content: bytes) -> bool:
        if extension == "xlsx":
            if not content.startswith(b"PK\x03\x04"):
                return False
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as archive:
                    names = set(archive.namelist())
            except zipfile.BadZipFile:
                return False
            return "[Content_Types].xml" in names and any(
                name.startswith("xl/") for name in names
            )
        if extension == "json":
            if not content.strip():
                return False
            try:
                parsed = json.loads(content.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return False
            return isinstance(parsed, (dict, list))
        if extension == "csv":
            if b"\x00" in content:
                return False
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                return False
            stripped = text.strip()
            if not stripped:
                return False
            sample = text[:4096]
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
                delimiter = dialect.delimiter
            except csv.Error:
                delimiter = None
            first_line = text.splitlines()[0] if text.splitlines() else text
            if delimiter:
                return delimiter in first_line or len(text.splitlines()) > 1
            return "\n" in text or "\r" in text
        return False

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
