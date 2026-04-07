"""
app/schemas/upload.py
----------------------
Pydantic schemas for the file upload resource.

This file defines the shape of all data that enters and leaves the upload
API. It is used by the upload router, upload service, and warnings router.

Schemas defined here:
    FileMeta             - Metadata about the uploaded file (name, type, size).
    Shape                - Row and column count of the parsed dataset.
    ColumnSchema         - Name, data type, and null count for a single column.
    ColumnMissingDetail  - Per-column missing value breakdown (count + percent).
                           Used to notify the user which columns have missing
                           values after upload.
    MissingSummary       - Overall missing value counts across the whole dataset.
    StorageRef           - Where the raw file is stored (MinIO/S3 bucket + key).
    UploadResponse       - Full response returned by POST /api/v1/upload.
                           Includes schema, preview, missing detail, warnings,
                           and storage reference.
    ErrorBody            - Shape of the error detail inside an error response.
    ErrorResponse        - Wrapper for all non-2xx API error responses.
                           Every endpoint in the project uses this same shape.
"""

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

DatasetStatus = Literal["uploaded", "ready", "failed"]
SourceType = Literal["user_upload", "sample"]
DataType = Literal["string", "int", "float", "bool", "datetime", "unknown"]


class FileMeta(BaseModel):
    original_filename: str
    extension: Literal["csv", "xlsx", "json"]
    mime_type: str
    size_bytes: int = Field(ge=0)


class Shape(BaseModel):
    rows: int = Field(ge=0)
    columns: int = Field(ge=0)


class ColumnSchema(BaseModel):
    name: str
    dtype: DataType
    null_count: int = Field(ge=0)


class MissingSummary(BaseModel):
    rows_with_missing: int = Field(ge=0)
    total_missing_cells: int = Field(ge=0)


# ── NEW: per-column missing detail ───────────────────────────────────────────
class ColumnMissingDetail(BaseModel):
    """
    Missing value breakdown for a single column.
    Returned in the upload response and the /warnings endpoint so the
    frontend can show the user exactly which columns have missing values
    and how severe the problem is.
    """
    column_name:    str
    missing_count:  int   = Field(ge=0)
    total_rows:     int   = Field(ge=0)
    missing_percent: float = Field(ge=0.0, le=100.0)


class StorageRef(BaseModel):
    provider: Literal["s3-compatible"]
    bucket: str
    object_key: str


class UploadResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    dataset_id:     str
    status:         DatasetStatus
    session_id:     str | None = None
    file_meta:      FileMeta
    shape:          Shape
    schema_:        list[ColumnSchema] = Field(alias="schema")
    preview:        list[dict[str, Any]]
    missing_summary: MissingSummary
    # ── NEW: per-column missing detail and warnings ───────────────────────────
    missing_detail: list[ColumnMissingDetail] = Field(
        default_factory=list,
        description=(
            "Per-column breakdown of missing values. Empty list when no "
            "missing values are present."
        ),
    )
    warnings:       list[str]
    # ─────────────────────────────────────────────────────────────────────────
    storage:        StorageRef


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any]
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorBody