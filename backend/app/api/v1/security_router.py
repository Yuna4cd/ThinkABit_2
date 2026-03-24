"""
app/api/v1/security.py
-----------------------
FastAPI router for dataset security.

Endpoints
---------
GET  /api/v1/datasets/{dataset_id}/access
    Check whether the requesting session owns the dataset and whether
    it is still within its 7-day expiry window.

GET  /api/v1/datasets/{dataset_id}/preview/safe
    Return a preview of the dataset with sensitive column values masked.
    Only accessible by the session that uploaded the dataset.

GET  /api/v1/datasets/{dataset_id}/security
    Full security summary — access control, expiry status, sensitive
    column detection, and input sanitization warnings in one response.
    Useful for the frontend to display a security overview to the user.
"""

from fastapi import APIRouter, Query

from app.schemas.security import (
    DatasetAccessResponse,
    SanitizedPreviewResponse,
    SecuritySummaryResponse,
)
from app.services.security_service import SecurityService

import pandas as pd

router = APIRouter()
security_service = SecurityService()


@router.get(
    "/datasets/{dataset_id}/access",
    response_model=DatasetAccessResponse,
    status_code=200,
)
def check_dataset_access(
    dataset_id: str,
    session_id: str = Query(..., description="Session ID of the requesting user."),
) -> DatasetAccessResponse:
    """
    Verify that the requesting session owns this dataset and that it
    has not expired.

    Raises 403 if the session does not own the dataset.
    Raises 404 if the dataset does not exist.
    Raises 410 if the dataset has expired (older than 7 days).
    """
    return security_service.check_access(
        dataset_id=dataset_id,
        session_id=session_id,
    )


@router.get(
    "/datasets/{dataset_id}/preview/safe",
    response_model=SanitizedPreviewResponse,
    status_code=200,
)
def get_safe_preview(
    dataset_id: str,
    session_id: str = Query(..., description="Session ID of the requesting user."),
) -> SanitizedPreviewResponse:
    """
    Return a preview of the dataset with sensitive column values masked.

    Column names matching known sensitive patterns (email, ssn, password,
    salary, etc.) have their values replaced with "***MASKED***" so raw
    sensitive data is never exposed in the response.

    Raises 403 if the session does not own the dataset.
    Raises 404 if the dataset does not exist.
    Raises 410 if the dataset has expired.

    ---
    TODO (DB): Replace the placeholder DataFrame with a real fetch:
        1. Query datasets table for the record by dataset_id.
        2. Fetch raw file bytes from MinIO using object_key.
        3. Re-parse into a DataFrame using UploadService parsers.
    """
    # ── Placeholder (remove when DB is connected) ─────────────────────────────
    placeholder_df = pd.DataFrame({
        "order_id":  ["A001", "A002", "A003"],
        "email":     ["alice@example.com", "bob@example.com", "carol@example.com"],
        "salary":    [75000, 82000, 91000],
        "total":     [31.25, 88.00, 45.50],
    })
    columns = list(placeholder_df.columns)
    preview = placeholder_df.to_dict(orient="records")
    # ─────────────────────────────────────────────────────────────────────────

    return security_service.get_sanitized_preview(
        dataset_id=dataset_id,
        session_id=session_id,
        columns=columns,
        preview=preview,
    )


@router.get(
    "/datasets/{dataset_id}/security",
    response_model=SecuritySummaryResponse,
    status_code=200,
)
def get_security_summary(
    dataset_id: str,
    session_id: str = Query(..., description="Session ID of the requesting user."),
) -> SecuritySummaryResponse:
    """
    Full security summary for a dataset.

    Combines all four security checks into one response:
      - Session-based access control (owns the dataset?)
      - Expiry status (still within 7-day window?)
      - Sensitive column detection (email, ssn, password, salary, etc.)
      - Input sanitization warnings (formula injection attempts detected?)

    The frontend can use this to display a security overview to the user
    before they proceed with analysis.

    Raises 403, 404, or 410 same as the other security endpoints.

    ---
    TODO (DB): Same placeholder replacement as /preview/safe above.
    """
    # ── Placeholder (remove when DB is connected) ─────────────────────────────
    placeholder_df = pd.DataFrame({
        "order_id":  ["A001", "A002", "A003"],
        "email":     ["alice@example.com", "bob@example.com", "carol@example.com"],
        "salary":    [75000, 82000, 91000],
        "total":     [31.25, 88.00, 45.50],
    })
    columns = list(placeholder_df.columns)
    preview = placeholder_df.to_dict(orient="records")
    # ─────────────────────────────────────────────────────────────────────────

    return security_service.get_security_summary(
        dataset_id=dataset_id,
        session_id=session_id,
        columns=columns,
        preview=preview,
    )