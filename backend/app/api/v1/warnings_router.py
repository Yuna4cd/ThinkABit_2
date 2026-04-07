"""
app/api/v1/warnings.py
-----------------------
FastAPI router for the dataset warnings resource.

Endpoint
--------
GET /api/v1/datasets/{dataset_id}/warnings

    Returns the missing value warnings for a dataset at any point after
    upload. The frontend can call this on page load, after the user resumes
    a session, or whenever it needs to re-display the notification without
    re-uploading the file.

    The upload response already includes warnings and missing_detail
    directly — this endpoint exists so the frontend can retrieve them
    again later without needing to re-parse or re-upload anything.

Registered in main.py under the /api/v1 prefix, following the
dataset-scoped URL pattern from the API contract:
    /api/v1/datasets/{dataset_id}/...
"""

from fastapi import APIRouter
from uuid import uuid4

from app.errors import APIError
from app.schemas.upload import MissingSummary
from app.schemas.warnings import DatasetWarningsResponse
from app.services.upload_service import WARNINGS_STORE

router = APIRouter()


@router.get(
    "/datasets/{dataset_id}/warnings",
    response_model=DatasetWarningsResponse,
    status_code=200,
)
def get_dataset_warnings(dataset_id: str) -> DatasetWarningsResponse:
    """
    Retrieve missing value warnings for a dataset.

    Returns the same missing_summary, missing_detail, and warnings that
    were generated during upload — no re-parsing needed.

    has_missing is True when any missing values were found, False when
    the dataset was completely clean. The frontend uses this flag to
    decide whether to show a notification at all.

    Raises 404 when no warnings record exists for the given dataset_id
    (i.e. the dataset has not been uploaded yet).

    ---
    TODO (DB): Replace WARNINGS_STORE lookup with a Supabase query:
        row = db.execute(
            "SELECT missing_summary, missing_detail, warnings
             FROM datasets WHERE dataset_id = :id",
            {"id": dataset_id}
        ).fetchone()
        if row is None:
            raise APIError(code="DATASET_NOT_FOUND", status_code=404, ...)
        return DatasetWarningsResponse(
            dataset_id=dataset_id,
            has_missing=row.missing_summary["total_missing_cells"] > 0,
            missing_summary=MissingSummary(**row.missing_summary),
            missing_detail=row.missing_detail,
            warnings=row.warnings,
        )
    """
    record = WARNINGS_STORE.get(dataset_id)
    if record is None:
        raise APIError(
            status_code=404,
            code="DATASET_NOT_FOUND",
            message=f"No warnings record found for dataset '{dataset_id}'. "
                    f"Ensure the dataset has been uploaded successfully.",
            details={"dataset_id": dataset_id},
            request_id=f"req_{uuid4().hex[:8]}",
        )

    missing_summary: MissingSummary = record["missing_summary"]

    return DatasetWarningsResponse(
        dataset_id=dataset_id,
        has_missing=missing_summary.total_missing_cells > 0,
        missing_summary=missing_summary,
        missing_detail=record["missing_detail"],
        warnings=record["warnings"],
    )