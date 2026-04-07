from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class DatasetAccessResponse(BaseModel):
    """
    Response returned when checking whether a session is allowed to
    access a dataset and whether the dataset is still within its expiry window.
    """
    dataset_id:   str
    session_id:   str
    access_granted: bool
    reason:       str | None = None   # populated when access_granted is False
    expires_at:   datetime
    is_expired:   bool


class SanitizedPreviewResponse(BaseModel):
    """
    A preview of the dataset with sensitive column values masked.
    Returned alongside flagged column names so the frontend can
    inform the user which columns were masked and why.
    """
    dataset_id:        str
    columns:           list[str]
    sensitive_columns: list[str]   # columns whose values were masked
    preview:           list[dict[str, Any]]


class SecuritySummaryResponse(BaseModel):
    """
    Full security summary for a dataset — combines access control,
    expiry status, and sensitive column detection in one response.
    Used by the frontend to display a security overview to the user.
    """
    dataset_id:        str
    session_id:        str
    access_granted:    bool
    is_expired:        bool
    expires_at:        datetime
    sensitive_columns: list[str]
    warnings:          list[str]