"""
To aid in handling null values  in an uploaded data set
--------------------
app/api/v1/clean.py
--------------------
FastAPI router for the dataset cleaning resource.

Endpoint
--------
POST /api/v1/datasets/{dataset_id}/clean

    The user calls this after reviewing their uploaded dataset and deciding
    they want to remove rows with missing values. This is an explicit,
    user-triggered step — not automatic — so the user experiences data
    cleaning as part of the analytics learning process.

Registered in main.py under the /api/v1 prefix, matching the URL pattern
established in the API contract for dataset-scoped operations:
    /api/v1/datasets/{dataset_id}/...
"""

from fastapi import APIRouter

from app.schemas.clean import CleanResponse
from app.services.clean_service import CleanService

router = APIRouter()
clean_service = CleanService()


@router.post(
    "/datasets/{dataset_id}/clean",
    response_model=CleanResponse,
    status_code=200,
)
def clean_dataset(dataset_id: str) -> CleanResponse:
    """
    Drop all rows that contain at least one missing value from the dataset.

    This endpoint is intentionally separate from upload — the user first
    sees their raw data (nulls included) so they can understand what needs
    cleaning, then calls this endpoint to perform the cleaning step as part
    of learning the data analytics process.

    Returns a summary of what changed (rows dropped, rows remaining) and a
    preview of the cleaned dataset.

    Raises 422 if every row in the dataset contains a missing value and
    nothing would remain after cleaning.

    ---
    TODO (DB): When Supabase + MinIO are connected, replace the placeholder
    DataFrame below with a real lookup:
        1. Query Supabase for the dataset record using dataset_id.
           Raise 404 (DATASET_NOT_FOUND) if no record exists.
        2. Fetch the raw file bytes from MinIO using the stored object_key.
        3. Re-parse the bytes into a DataFrame (reuse UploadService parsers).
        4. Pass the DataFrame to clean_service.clean_dataset().
        5. Optionally persist the cleaned DataFrame back to MinIO and update
           the Supabase record status.
    """

    # ── Placeholder DataFrame (remove when DB is connected) ───────────────────
    # Simulates fetching and re-parsing the user's uploaded file.
    # Replace this entire block with the DB lookup described in the TODO above.
    import pandas as pd
    placeholder_dataframe = pd.DataFrame({
        "order_id":    ["A001", "A002", None,   "A004", "A005"],
        "order_date":  ["2025-01-01", "2025-01-02", "2025-01-03", None, "2025-01-05"],
        "total_amount": [31.25, None, 88.00, 45.50, 120.75],
    })
    # ─────────────────────────────────────────────────────────────────────────

    return clean_service.clean_dataset(
        dataset_id=dataset_id,
        dataframe=placeholder_dataframe,
    )