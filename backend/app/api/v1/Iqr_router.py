"""
app/api/v1/iqr.py
------------------
FastAPI router for IQR outlier detection.

Registered in main.py under the /api/v1 prefix, following the
dataset-scoped URL pattern from the API contract:

    POST /api/v1/datasets/{dataset_id}/iqr

The user calls this after uploading and cleaning their dataset to detect
outliers in a specific numeric column — an important step in the data
analytics teaching workflow before visualization or analysis.

Unlike Mahalanobis distance (which analyses all numeric columns together),
IQR analyses one column at a time — making it easier for learners to
understand since they can see exactly which values fall outside the bounds.
"""

import pandas as pd
from fastapi import APIRouter

from app.schemas.iqr import IQRRequest, IQRResponse
from app.services.iqr_service import IQRService

router = APIRouter()
iqr_service = IQRService()


@router.post(
    "/datasets/{dataset_id}/iqr",
    response_model=IQRResponse,
    status_code=200,
)
def detect_outliers(
    dataset_id: str,
    body: IQRRequest,
) -> IQRResponse:
    """
    Detect outliers in one numeric column using the Interquartile Range method.

    Computes Q1 (25th percentile), Q3 (75th percentile), and IQR = Q3 - Q1.
    Any value that falls below Q1 - (multiplier × IQR) or above
    Q3 + (multiplier × IQR) is flagged as an outlier.

    The standard multiplier is 1.5. Use a higher value (e.g. 3.0) to flag
    only extreme outliers, or a lower value to be more sensitive.

    Returns Q1, Q3, IQR, the exact bounds, and full detail on every outlier
    row so the frontend can show the user exactly what was flagged and why.

    Raises 400 if the column does not exist or is not numeric.
    Raises 422 if the column has missing values (run cleaning step first)
    or if there are fewer than 4 rows.

    ---
    TODO (DB): Replace the placeholder DataFrame with a real fetch:
        1. Query Supabase datasets table for the record by dataset_id.
           Raise 404 (DATASET_NOT_FOUND) if not found.
        2. Fetch raw file bytes from MinIO using object_key.
        3. Re-parse bytes into a DataFrame using UploadService parsers.
        4. Pass DataFrame into iqr_service.detect_outliers().
    """
    # ── Placeholder (remove when DB is connected) ─────────────────────────────
    placeholder_df = pd.DataFrame({
        "order_id":     ["A001", "A002", "A003", "A004", "A005",
                         "A006", "A007", "A008", "A009", "A010"],
        "total_amount": [31.25, 88.00, 45.50, 120.75, 67.00,
                         55.00, 49.00, 999.99, 72.50, 38.00],
        "quantity":     [1, 3, 2, 5, 2, 2, 1, 1, 3, 1],
    })
    # ─────────────────────────────────────────────────────────────────────────

    return iqr_service.detect_outliers(
        dataset_id=dataset_id,
        dataframe=placeholder_df,
        body=body,
    )