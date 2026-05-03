"""
app/services/mahalanobis_service.py
-------------------------------------
Business logic for Mahalanobis outlier detection.

Wraps the original mahalanobis algorithm and integrates it into the
project following the same pattern as upload_service.py:
  - One service class per domain.
  - Raises APIError (never HTTPException) so the shared handler in
    errors.py formats every error response consistently.
  - _build_error() has the same signature as every other service.
  - All return values are plain Python types — JSON serializable by FastAPI.

ORIGINAL ALGORITHM (unchanged)
-------------------------------
  1. Select only numeric columns from the dataset.
  2. Compute the mean vector and covariance matrix.
  3. Invert the covariance matrix.
  4. Compute Mahalanobis distance for each row.
  5. Flag rows whose distance exceeds the chi-square threshold.

DATABASE INTEGRATION
--------------------
Currently receives a DataFrame directly via a placeholder in the router.
When Supabase + MinIO are connected, replace the placeholder with:
  1. Query Supabase datasets table for the record by dataset_id.
  2. Fetch raw file bytes from MinIO using object_key.
  3. Re-parse bytes into a DataFrame using UploadService parsers.
  4. Pass DataFrame into detect_outliers() below.
"""

import numpy as np
import pandas as pd
from scipy.stats import chi2
from uuid import uuid4

from app.errors import APIError
from app.schemas.mahalanobis import MahalanobisResponse, OutlierRow


class MahalanobisService:

    def detect_outliers(
        self,
        dataset_id: str,
        dataframe: pd.DataFrame,
        alpha: float = 0.01,
    ) -> MahalanobisResponse:
        """
        Run Mahalanobis outlier detection on a dataset.

        Parameters
        ----------
        dataset_id : ID of the dataset being analysed.
        dataframe  : The parsed dataset as a pandas DataFrame.
        alpha      : Significance level for the chi-square threshold.
                     Default 0.01 (1% significance level).

        Returns
        -------
        MahalanobisResponse — fully JSON-serializable result.

        Raises
        ------
        APIError 422 — fewer than 2 numeric columns present.
        APIError 422 — not enough rows relative to number of features.
        APIError 422 — covariance matrix is singular (e.g. perfectly
                       correlated columns). Suggest running feature
                       selection first.
        """
        warnings: list[str] = []

        # ── Select numeric columns only ───────────────────────────────────────
        numeric_df   = dataframe.select_dtypes(include="number")
        dropped_cols = [c for c in dataframe.columns if c not in numeric_df.columns]
        if dropped_cols:
            warnings.append(
                f"Non-numeric column(s) excluded from the calculation: {dropped_cols}."
            )

        if numeric_df.empty:
            raise self._build_error(
                code="NO_NUMERIC_COLUMNS",
                message="No numeric columns found in the dataset.",
                details={},
                status_code=422,
            )

        # ── Drop rows with nulls ───────────────────────────────────────────────
        null_count = int(numeric_df.isna().sum().sum())
        if null_count > 0:
            numeric_df = numeric_df.dropna()
            warnings.append(
                f"{null_count} missing value(s) were excluded before "
                f"calculating distances. Run the cleaning step first for "
                f"best results."
            )

        X    = numeric_df.values
        n, k = X.shape

        if k < 2:
            raise self._build_error(
                code="INSUFFICIENT_FEATURES",
                message="Mahalanobis distance requires at least 2 numeric features.",
                details={"numeric_columns": list(numeric_df.columns)},
                status_code=422,
            )

        if n <= k:
            raise self._build_error(
                code="INSUFFICIENT_ROWS",
                message=(
                    f"Number of rows ({n}) must be greater than number of "
                    f"numeric features ({k})."
                ),
                details={"n_rows": n, "n_features": k},
                status_code=422,
            )

        # ── Step 1: Mean vector ───────────────────────────────────────────────
        mean = np.mean(X, axis=0)

        # ── Step 2: Covariance matrix ─────────────────────────────────────────
        cov = np.cov(X, rowvar=False)

        # ── Step 3: Invert covariance matrix ──────────────────────────────────
        try:
            inv_cov = np.linalg.inv(cov)
        except np.linalg.LinAlgError:
            raise self._build_error(
                code="SINGULAR_COVARIANCE",
                message=(
                    "Covariance matrix is singular and cannot be inverted. "
                    "This usually means two or more columns are perfectly "
                    "correlated. Try removing redundant columns using the "
                    "feature selection tool first."
                ),
                details={"numeric_columns": list(numeric_df.columns)},
                status_code=422,
            )

        # ── Step 4: Mahalanobis distance for each row ─────────────────────────
        centered  = X - mean
        left      = centered @ inv_cov
        d_squared = np.sum(left * centered, axis=1)
        distances = np.sqrt(d_squared)

        # ── Step 5: Chi-square threshold ──────────────────────────────────────
        threshold = float(np.sqrt(chi2.ppf(1 - alpha, df=k)))

        # ── Step 6: Flag outliers ─────────────────────────────────────────────
        is_outlier      = distances > threshold
        outlier_indices = [int(i) for i in numeric_df.index[is_outlier]]

        # Build OutlierRow objects — fully JSON serializable
        outliers: list[OutlierRow] = []
        for idx in outlier_indices:
            row_values = {
                col: self._to_python(numeric_df.loc[idx, col])
                for col in numeric_df.columns
            }
            outliers.append(OutlierRow(
                row_index=idx,
                distance=round(float(distances[numeric_df.index.get_loc(idx)]), 6),
                values=row_values,
            ))

        return MahalanobisResponse(
            dataset_id=dataset_id,
            n_rows=n,
            n_features=k,
            threshold=round(threshold, 6),
            n_outliers=int(np.sum(is_outlier)),
            outliers=outliers,
            outlier_indices=outlier_indices,
            distances=[round(float(d), 6) for d in distances],
            warnings=warnings,
        )

    def _to_python(self, value: object) -> object:
        """Convert numpy scalar to plain Python int or float for JSON safety."""
        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, np.floating):
            return float(value)
        return value

    def _build_error(
        self,
        *,
        code: str,
        message: str,
        details: dict,
        status_code: int,
    ) -> APIError:
        return APIError(
            status_code=status_code,
            code=code,
            message=message,
            details=details,
            request_id=f"req_{uuid4().hex[:8]}",
        )