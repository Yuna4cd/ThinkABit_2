"""
app/api/v1/mahalanobis.py
---------------------------
FastAPI router for Mahalanobis outlier detection.

Registered in main.py under the /api/v1 prefix, following the
dataset-scoped URL pattern from the API contract:

    POST /api/v1/datasets/{dataset_id}/mahalanobis

The user calls this after uploading and optionally cleaning their dataset
to detect rows that are statistical outliers — an important step in the
data analytics teaching workflow before visualization or analysis.
"""

import pandas as pd
from fastapi import APIRouter

from app.schemas.mahalanobis import MahalanobisRequest, MahalanobisResponse
from app.services.mahalanobis_service import MahalanobisService

router = APIRouter()
mahalanobis_service = MahalanobisService()


@router.post(
    "/datasets/{dataset_id}/mahalanobis",
    response_model=MahalanobisResponse,
    status_code=200,
)
def detect_outliers(
    dataset_id: str,
    body: MahalanobisRequest,
) -> MahalanobisResponse:
    """
    Detect statistical outliers in a dataset using Mahalanobis distance.

    Each row is scored by how far it sits from the center of the dataset,
    accounting for correlations between columns. Rows whose distance
    exceeds the chi-square threshold (controlled by `alpha`) are flagged
    as outliers.

    Non-numeric columns are automatically excluded.
    Rows with missing values are automatically excluded with a warning
    — run the cleaning step first for best results.

    Returns the distance score for every row, the threshold used, and
    full detail on every outlier row including its index and values.

    Raises 422 if:
      - Fewer than 2 numeric columns are present.
      - Not enough rows relative to the number of features.
      - Two or more columns are perfectly correlated (singular covariance).
        In that case run feature selection first to remove redundant columns.

    ---
    TODO (DB): Replace the placeholder DataFrame with a real fetch:
        1. Query Supabase datasets table for the record by dataset_id.
           Raise 404 (DATASET_NOT_FOUND) if not found.
        2. Fetch raw file bytes from MinIO using object_key.
        3. Re-parse bytes into a DataFrame using UploadService parsers.
        4. Pass DataFrame into mahalanobis_service.detect_outliers().
    """
    # ── Placeholder (remove when DB is connected) ─────────────────────────────
    placeholder_df = pd.DataFrame({
        "height": [170, 172, 168, 175, 171, 174, 169, 500],
        "weight": [65,  70,  63,  80,  68,  72,  66,  65],
        "age":    [25,  30,  22,  35,  28,  31,  24,  27],
    })
    # ─────────────────────────────────────────────────────────────────────────

    return mahalanobis_service.detect_outliers(
        dataset_id=dataset_id,
        dataframe=placeholder_df,
        alpha=body.alpha,
    )