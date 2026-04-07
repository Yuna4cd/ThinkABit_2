"""
Aids in handling null values in a data set
------------------------------
app/services/null_service.py
------------------------------
Business logic for the dataset cleaning resource.

Mirrors the pattern established in upload_service.py:
  - One service class per domain.
  - Raises APIError (never HTTPException) so the shared handler in
    errors.py formats every error response consistently.
  - _build_error() has the same signature as in UploadService.

WHAT THIS SERVICE DOES
----------------------
Receives a parsed DataFrame, drops every row that contains at least one
null value, and returns a CleanResponse the router hands back to the
frontend.

The frontend uses this response to show the user:
  - how many rows were removed
  - what the cleaned data looks like (preview)

This is intentionally a separate step from upload so the user can first
SEE their raw data (nulls included) and then actively choose to clean it
as part of learning the data analytics process.

DATABASE INTEGRATION
--------------------
Right now the service receives a DataFrame directly from the router (which
reconstructs it from the in-memory store). When Supabase + MinIO are
connected, replace the DataFrame parameter with a dataset_id lookup:
  1. Fetch raw object bytes from MinIO using dataset_id.
  2. Parse bytes back into a DataFrame.
  3. Run _drop_null_rows().
  4. Optionally persist the cleaned version to MinIO / update Supabase status.
"""

from datetime import UTC, date, datetime
from uuid import uuid4

import pandas as pd

from app.errors import APIError
from app.schemas.clean import CleanResponse


class CleanService:

    def clean_dataset(
        self,
        dataset_id: str,
        dataframe: pd.DataFrame,
        preview_rows: int = 100,
    ) -> CleanResponse:
        """
        Drop all rows that contain at least one null value and return a
        CleanResponse summarising what changed.

        Parameters
        ----------
        dataset_id  : ID of the dataset being cleaned — passed through to
                      the response so the frontend can correlate it.
        dataframe   : Parsed DataFrame representing the user's uploaded data.
        preview_rows: How many rows to include in the response preview.
                      Defaults to 100, consistent with the upload default.

        Raises
        ------
        APIError 422 – when every row contains a null (nothing would remain).
        """
        rows_before = len(dataframe)

        cleaned, null_rows_dropped = self._drop_null_rows(dataframe)

        # If every row was removed the dataset is unusable — tell the user
        if len(cleaned) == 0:
            raise self._build_error(
                code="EMPTY_FILE",
                message=(
                    "No rows remain after removing rows with missing values. "
                    "Every row in this dataset contains at least one missing value."
                ),
                details={
                    "rows_before": rows_before,
                    "null_rows_dropped": null_rows_dropped,
                },
                status_code=422,
            )

        preview = self._build_preview(cleaned, preview_rows)

        return CleanResponse(
            dataset_id=dataset_id,
            rows_before=rows_before,
            rows_after=len(cleaned),
            null_rows_dropped=null_rows_dropped,
            columns=list(cleaned.columns),
            preview=preview,
        )

    # ── Null handling ──────────────────────────────────────────────────────────

    def _drop_null_rows(self, dataframe: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        """
        Drop every row that contains at least one null value.

        Returns the cleaned DataFrame (with a reset index) and the number
        of rows that were removed.
        """
        original_count = len(dataframe)
        cleaned = dataframe.dropna().reset_index(drop=True)
        return cleaned, original_count - len(cleaned)

    # ── Preview builder ────────────────────────────────────────────────────────

    def _build_preview(self, dataframe: pd.DataFrame, preview_rows: int) -> list[dict]:
        """
        Build a serializable preview of the first `preview_rows` rows.

        Matches the serialization format used in UploadService._build_preview()
        so the frontend can handle both responses the same way.
        """
        preview_frame = dataframe.head(preview_rows)
        preview: list[dict] = []
        for _, row in preview_frame.iterrows():
            serialized = {
                str(col): self._serialize_value(row[col])
                for col in preview_frame.columns
            }
            preview.append(serialized)
        return preview

    def _serialize_value(self, value: object) -> object:
        """
        Serialize a single cell value to a JSON-safe type.

        Mirrors UploadService._serialize_preview_value() exactly so
        datetime and numpy scalar handling is consistent across the API.
        """
        if pd.isna(value):
            return None
        if isinstance(value, pd.Timestamp):
            dt = value.to_pydatetime()
            if dt.tzinfo is None:
                return dt.isoformat() + "Z"
            return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.isoformat() + "Z"
            return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
        if isinstance(value, date):
            return value.isoformat()
        if hasattr(value, "item"):
            return value.item()
        return value

    # ── Error builder ──────────────────────────────────────────────────────────

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