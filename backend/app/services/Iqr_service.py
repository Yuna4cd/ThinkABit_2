"""
app/services/iqr_service.py
-----------------------------
Business logic for IQR outlier detection.

Wraps the original iqr_outliers_one_column algorithm and integrates it
into the project following the same pattern as upload_service.py and
mahalanobis_service.py:
  - One service class per domain.
  - Raises APIError (never HTTPException) so the shared handler in
    errors.py formats every error response consistently.
  - _build_error() has the same signature as every other service.
  - All return values are plain Python types — JSON serializable by FastAPI.

ORIGINAL ALGORITHM (unchanged)
-------------------------------
  Q1  = 25th percentile of the column
  Q3  = 75th percentile of the column
  IQR = Q3 - Q1
  lower = Q1 - multiplier * IQR
  upper = Q3 + multiplier * IQR
  Flag as outlier if: value < lower OR value > upper
  (or <= / >= when include_bounds=False)

DATABASE INTEGRATION
--------------------
Currently receives a DataFrame directly via a placeholder in the router.
When Supabase + MinIO are connected, replace the placeholder with:
  1. Query Supabase datasets table for the record by dataset_id.
  2. Fetch raw file bytes from MinIO using object_key.
  3. Re-parse bytes into a DataFrame using UploadService parsers.
  4. Pass DataFrame into detect_outliers() below.
"""

import pandas as pd
from uuid import uuid4

from app.errors import APIError
from app.schemas.iqr import IQRResponse, IQRRequest, OutlierRow


class IQRService:

    def detect_outliers(
        self,
        dataset_id: str,
        dataframe: pd.DataFrame,
        body: IQRRequest,
    ) -> IQRResponse:
        """
        Run IQR outlier detection on a single column of a dataset.

        Parameters
        ----------
        dataset_id : ID of the dataset being analysed.
        dataframe  : The parsed dataset as a pandas DataFrame.
        body       : Request containing the column name, multiplier,
                     and include_bounds setting.

        Returns
        -------
        IQRResponse — fully JSON-serializable result.

        Raises
        ------
        APIError 400 — column not found in the dataset.
        APIError 400 — column is not numeric.
        APIError 400 — multiplier is not greater than 0 (caught by schema).
        APIError 422 — column contains missing values (run cleaning first).
        APIError 422 — fewer than 4 rows (too few to compute quartiles).
        """
        warnings: list[str] = []

        # ── Validate column exists ────────────────────────────────────────────
        if body.column not in dataframe.columns:
            raise self._build_error(
                code="COLUMN_NOT_FOUND",
                message=f"Column '{body.column}' not found in the dataset.",
                details={"available_columns": list(dataframe.columns)},
                status_code=400,
            )

        series = dataframe[body.column]

        # ── Validate column is numeric ────────────────────────────────────────
        if not pd.api.types.is_numeric_dtype(series):
            raise self._build_error(
                code="INVALID_COLUMN_TYPE",
                message=f"Column '{body.column}' must be numeric for IQR outlier detection.",
                details={"column": body.column, "dtype": str(series.dtype)},
                status_code=400,
            )

        # ── Handle missing values ─────────────────────────────────────────────
        if series.isna().any():
            null_count = int(series.isna().sum())
            raise self._build_error(
                code="MISSING_VALUES",
                message=(
                    f"Column '{body.column}' contains {null_count} missing value(s). "
                    f"Run the cleaning step first before detecting outliers."
                ),
                details={"column": body.column, "null_count": null_count},
                status_code=422,
            )

        # ── Validate enough rows ──────────────────────────────────────────────
        if len(series) < 4:
            raise self._build_error(
                code="INSUFFICIENT_ROWS",
                message="Too few rows to compute quartiles reliably (need at least 4).",
                details={"n_rows": len(series)},
                status_code=422,
            )

        # ── Step 1: Compute quartiles and IQR ────────────────────────────────
        q1  = float(series.quantile(0.25, interpolation="linear"))
        q3  = float(series.quantile(0.75, interpolation="linear"))
        iqr = q3 - q1

        # Warn when IQR is zero — bounds collapse and detection may be unreliable
        if iqr == 0:
            warnings.append(
                f"Column '{body.column}' has an IQR of 0 — all middle values are "
                f"identical. Outlier detection may not be meaningful."
            )

        # ── Step 2: Compute bounds ────────────────────────────────────────────
        lower = q1 - body.multiplier * iqr
        upper = q3 + body.multiplier * iqr

        # ── Step 3: Flag outliers ─────────────────────────────────────────────
        if body.include_bounds:
            mask = (series < lower) | (series > upper)
            rule = f"value < {round(lower, 6)} OR value > {round(upper, 6)}"
        else:
            mask = (series <= lower) | (series >= upper)
            rule = f"value <= {round(lower, 6)} OR value >= {round(upper, 6)}"

        outlier_indices = [int(i) for i in dataframe.index[mask]]

        # ── Step 4: Build OutlierRow objects ──────────────────────────────────
        outliers: list[OutlierRow] = []
        for idx in outlier_indices:
            row_values = {
                col: self._to_python(dataframe.loc[idx, col])
                for col in dataframe.columns
            }
            outliers.append(OutlierRow(
                row_index=idx,
                column_value=float(dataframe.loc[idx, body.column]),
                values=row_values,
            ))

        return IQRResponse(
            dataset_id=dataset_id,
            column=body.column,
            multiplier=float(body.multiplier),
            q1=round(q1, 6),
            q3=round(q3, 6),
            iqr=round(iqr, 6),
            lower_bound=round(lower, 6),
            upper_bound=round(upper, 6),
            rule=rule,
            n_outliers=int(mask.sum()),
            outliers=outliers,
            outlier_indices=outlier_indices,
            warnings=warnings,
        )

    def _to_python(self, value: object) -> object:
        """Convert numpy scalar to plain Python int or float for JSON safety."""
        import numpy as np
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