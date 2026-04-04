from uuid import uuid4

from fastapi import APIRouter, File, Form, UploadFile

from app.core.config import DATABASE_URL, DEFAULT_PREVIEW_ROWS
from app.errors import APIError
from app.schemas.upload import (
    ColumnSchema,
    DatasetMetadataResponse,
    DatasetSchemaResponse,
    FileMeta,
    Shape,
    SourceType,
    UploadResponse,
)
from app.services.metastore_service import MetastoreService
from app.services.upload_service import UploadService
from app.services.upload_validator import UploadValidator


router = APIRouter()
upload_service = UploadService()
upload_validator = UploadValidator()
metastore_service = MetastoreService(database_url=DATABASE_URL)


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=201,
)
async def upload_dataset(
    file: UploadFile = File(...),
    session_id: str | None = Form(default=None, max_length=128),
    source: SourceType = Form(default="user_upload"),
    preview_rows: int = Form(default=DEFAULT_PREVIEW_ROWS),
) -> UploadResponse:
    await upload_validator.validate(file=file, preview_rows=preview_rows)

    _ = source
    return await upload_service.handle_upload(
        file=file,
        session_id=session_id,
        preview_rows=preview_rows,
    )


@router.get(
    "/datasets/{dataset_id}",
    response_model=DatasetMetadataResponse,
    status_code=200,
)
def get_dataset(dataset_id: str) -> DatasetMetadataResponse:
    try:
        record = metastore_service.get_dataset_metadata(dataset_id)
    except Exception as exc:
        raise APIError(
            status_code=500,
            code="METASTORE_ERROR",
            message="Failed to read metadata from metastore backend.",
            details={"reason": str(exc)[:200]},
            request_id=f"req_{uuid4().hex[:8]}",
        ) from exc

    if record is None:
        raise APIError(
            status_code=404,
            code="DATASET_NOT_FOUND",
            message="Dataset not found.",
            details={"dataset_id": dataset_id},
            request_id=f"req_{uuid4().hex[:8]}",
        )

    return DatasetMetadataResponse(
        dataset_id=record.dataset_id,
        status=record.parse_status,
        session_id=record.session_id,
        file_meta=FileMeta(
            original_filename=record.original_filename,
            extension=record.extension,
            mime_type=record.mime_type,
            size_bytes=record.size_bytes,
        ),
        shape=Shape(rows=record.row_count, columns=record.column_count),
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get(
    "/datasets/{dataset_id}/schema",
    response_model=DatasetSchemaResponse,
    status_code=200,
)
def get_dataset_schema(dataset_id: str) -> DatasetSchemaResponse:
    try:
        record = metastore_service.get_dataset_schema(dataset_id)
    except Exception as exc:
        raise APIError(
            status_code=500,
            code="METASTORE_ERROR",
            message="Failed to read metadata from metastore backend.",
            details={"reason": str(exc)[:200]},
            request_id=f"req_{uuid4().hex[:8]}",
        ) from exc

    if record is None:
        raise APIError(
            status_code=404,
            code="DATASET_NOT_FOUND",
            message="Dataset not found.",
            details={"dataset_id": dataset_id},
            request_id=f"req_{uuid4().hex[:8]}",
        )

    return DatasetSchemaResponse(
        dataset_id=record.dataset_id,
        schema_=[ColumnSchema(**column) for column in record.schema_json],
    )
