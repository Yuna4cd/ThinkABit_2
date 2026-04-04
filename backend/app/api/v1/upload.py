from uuid import uuid4

from fastapi import APIRouter, File, Form, Query, UploadFile

from app.core.config import DATABASE_URL, DEFAULT_PREVIEW_ROWS
from app.errors import APIError
from app.schemas.upload import (
    ColumnSchema,
    DatasetContentResponse,
    DatasetDeleteResponse,
    DatasetMetadataResponse,
    DatasetPreviewResponse,
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


def _get_dataset_preview_source_record(dataset_id: str):
    try:
        record = metastore_service.get_dataset_preview_source(dataset_id)
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

    return record


def _get_dataset_storage_content(storage_key: str) -> bytes:
    try:
        return upload_service.storage_service.get_object(key=storage_key)
    except Exception as exc:
        raise APIError(
            status_code=500,
            code="STORAGE_ERROR",
            message="Failed to read object from storage backend.",
            details={"reason": str(exc)[:200]},
            request_id=f"req_{uuid4().hex[:8]}",
        ) from exc


def _delete_dataset_storage_object(storage_key: str) -> None:
    try:
        upload_service.storage_service.delete_object(key=storage_key)
    except Exception as exc:
        raise APIError(
            status_code=500,
            code="STORAGE_ERROR",
            message="Failed to delete object from storage backend.",
            details={"reason": str(exc)[:200]},
            request_id=f"req_{uuid4().hex[:8]}",
        ) from exc


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


@router.delete(
    "/datasets/{dataset_id}",
    response_model=DatasetDeleteResponse,
    status_code=200,
)
def delete_dataset(dataset_id: str) -> DatasetDeleteResponse:
    record = _get_dataset_preview_source_record(dataset_id)
    _delete_dataset_storage_object(record.storage_key_raw)

    try:
        deleted = metastore_service.delete_dataset_metadata(dataset_id)
    except Exception as exc:
        raise APIError(
            status_code=500,
            code="METASTORE_ERROR",
            message="Failed to delete metadata from metastore backend.",
            details={"reason": str(exc)[:200]},
            request_id=f"req_{uuid4().hex[:8]}",
        ) from exc

    if not deleted:
        raise APIError(
            status_code=500,
            code="METASTORE_ERROR",
            message="Failed to delete metadata from metastore backend.",
            details={"dataset_id": dataset_id},
            request_id=f"req_{uuid4().hex[:8]}",
        )

    return DatasetDeleteResponse(
        dataset_id=dataset_id,
        deleted=True,
        message="Dataset deleted successfully.",
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


@router.get(
    "/datasets/{dataset_id}/content",
    response_model=DatasetContentResponse,
    status_code=200,
)
def get_dataset_content(dataset_id: str) -> DatasetContentResponse:
    record = _get_dataset_preview_source_record(dataset_id)
    content = _get_dataset_storage_content(record.storage_key_raw)
    rows = upload_service.build_content_rows(
        content=content,
        extension=record.extension,
    )

    return DatasetContentResponse(
        dataset_id=record.dataset_id,
        rows=rows,
    )


@router.get(
    "/datasets/{dataset_id}/preview",
    response_model=DatasetPreviewResponse,
    status_code=200,
)
def get_dataset_preview(
    dataset_id: str,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> DatasetPreviewResponse:
    record = _get_dataset_preview_source_record(dataset_id)
    content = _get_dataset_storage_content(record.storage_key_raw)

    rows = upload_service.build_preview_rows(
        content=content,
        extension=record.extension,
        limit=limit,
        offset=offset,
    )

    return DatasetPreviewResponse(
        dataset_id=record.dataset_id,
        limit=limit,
        offset=offset,
        rows=rows,
    )
