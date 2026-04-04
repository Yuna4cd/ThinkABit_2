from typing import Any, Literal
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


DatasetStatus = Literal["uploaded", "parsing", "ready", "failed"]
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


class StorageRef(BaseModel):
    provider: Literal["s3-compatible"]
    bucket: str
    object_key: str


class UploadResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dataset_id: str
    status: DatasetStatus
    session_id: str | None = None
    file_meta: FileMeta
    shape: Shape
    schema_: list[ColumnSchema] = Field(alias="schema")
    preview: list[dict[str, Any]]
    missing_summary: MissingSummary
    storage: StorageRef
    warnings: list[str]


class DatasetMetadataResponse(BaseModel):
    dataset_id: str
    status: DatasetStatus
    session_id: str | None = None
    file_meta: FileMeta
    shape: Shape
    created_at: datetime
    updated_at: datetime


class DatasetSchemaResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dataset_id: str
    schema_: list[ColumnSchema] = Field(alias="schema")


class DatasetPreviewResponse(BaseModel):
    dataset_id: str
    limit: int = Field(ge=1, le=200)
    offset: int = Field(ge=0)
    rows: list[dict[str, Any]]


class DatasetContentResponse(BaseModel):
    dataset_id: str
    rows: list[dict[str, Any]]


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any]
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorBody
