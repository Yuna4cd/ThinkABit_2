"""
app/services/security_service.py
----------------------------------
Implements four security measures for stored datasets:

1. SESSION-BASED ACCESS CONTROL
   Only the session that originally uploaded a dataset can access it.
   Any request from a different session_id is rejected with 403.

2. DATASET EXPIRY
   Datasets are retained for 7 days (DATASET_EXPIRY_DAYS in config.py).
   After that window they are marked expired and access is blocked with 410.

3. SENSITIVE COLUMN MASKING
   Column names are checked against a list of known sensitive patterns
   (e.g. "email", "ssn", "password", "salary") defined in config.py.
   Matching column values are replaced with "***MASKED***" in any preview
   returned to the client so raw sensitive values are never exposed.

4. INPUT SANITIZATION
   Cell values in the dataset are scanned for patterns that could indicate
   injection attempts or formula injection (a common spreadsheet attack).
   Flagged values are neutralised by prefixing with a single quote so
   they are treated as plain text rather than executable expressions.
   A warning is added to the response when sanitization occurs.

DATABASE INTEGRATION
--------------------
Each method has a TODO block. When Supabase is connected:
  - Replace DATASET_REGISTRY with a real DB query on the `datasets` table.
  - session_id and created_at are already columns in the contract schema.
  - expires_at can be computed as created_at + DATASET_EXPIRY_DAYS.
"""

import re
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.config import DATASET_EXPIRY_DAYS, SENSITIVE_COLUMN_PATTERNS
from app.errors import APIError
from app.schemas.security import (
    DatasetAccessResponse,
    SanitizedPreviewResponse,
    SecuritySummaryResponse,
)

# Patterns that indicate a possible formula injection attempt in a cell value.
# These are common spreadsheet formula prefixes that should never appear as
# raw cell values when uploaded as data.
_FORMULA_INJECTION_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


class SecurityService:

    # ── 1. Session-based access control ──────────────────────────────────────

    def check_access(self, dataset_id: str, session_id: str) -> DatasetAccessResponse:
        """
        Verify that the requesting session owns the dataset and that
        the dataset has not expired.

        Raises
        ------
        APIError 404 – dataset not found.
        APIError 403 – session does not own this dataset.
        APIError 410 – dataset has expired (older than DATASET_EXPIRY_DAYS).

        TODO (DB):
            row = db.execute(
                "SELECT session_id, created_at FROM datasets WHERE dataset_id = :id",
                {"id": dataset_id}
            ).fetchone()
            if row is None:
                raise self._build_error(code="DATASET_NOT_FOUND", status_code=404, ...)
            expires_at = row.created_at + timedelta(days=DATASET_EXPIRY_DAYS)
            is_expired = datetime.now(UTC) > expires_at
            if row.session_id != session_id:
                raise self._build_error(code="ACCESS_DENIED", status_code=403, ...)
            if is_expired:
                raise self._build_error(code="DATASET_EXPIRED", status_code=410, ...)
        """
        record = DATASET_REGISTRY.get(dataset_id)
        if record is None:
            raise self._build_error(
                code="DATASET_NOT_FOUND",
                message=f"Dataset '{dataset_id}' not found.",
                details={"dataset_id": dataset_id},
                status_code=404,
            )

        expires_at = record["created_at"] + timedelta(days=DATASET_EXPIRY_DAYS)
        is_expired = datetime.now(UTC) > expires_at

        # Wrong session
        if record["session_id"] != session_id:
            raise self._build_error(
                code="ACCESS_DENIED",
                message="You do not have permission to access this dataset.",
                details={"dataset_id": dataset_id},
                status_code=403,
            )

        # Expired
        if is_expired:
            raise self._build_error(
                code="DATASET_EXPIRED",
                message=(
                    f"This dataset has expired and is no longer available. "
                    f"Datasets are retained for {DATASET_EXPIRY_DAYS} days."
                ),
                details={"dataset_id": dataset_id, "expired_at": expires_at.isoformat()},
                status_code=410,
            )

        return DatasetAccessResponse(
            dataset_id=dataset_id,
            session_id=session_id,
            access_granted=True,
            reason=None,
            expires_at=expires_at,
            is_expired=False,
        )

    def register_dataset(self, dataset_id: str, session_id: str) -> None:
        """
        Register a newly uploaded dataset with its owning session and
        creation timestamp so access control and expiry checks work.

        Call this inside UploadService.handle_upload() after a successful
        upload, passing the dataset_id and session_id.

        TODO (DB):
            The `datasets` table already stores session_id and created_at
            per the API contract schema — no extra insert needed.
            Remove this method entirely and point check_access() at the
            existing datasets table query instead.
        """
        DATASET_REGISTRY[dataset_id] = {
            "session_id": session_id,
            "created_at": datetime.now(UTC),
        }

    # ── 2 & 3. Sensitive column masking ──────────────────────────────────────

    def get_sanitized_preview(
        self,
        dataset_id: str,
        session_id: str,
        columns: list[str],
        preview: list[dict],
    ) -> SanitizedPreviewResponse:
        """
        Return a preview with sensitive column values masked.

        Detects columns whose names match known sensitive patterns
        (defined in config.py SENSITIVE_COLUMN_PATTERNS) and replaces
        their values with "***MASKED***" so raw sensitive data is never
        exposed in API responses.

        Access control and expiry are checked first — raises the same
        errors as check_access().
        """
        self.check_access(dataset_id=dataset_id, session_id=session_id)

        sensitive_columns = self._detect_sensitive_columns(columns)
        masked_preview = self._mask_preview(preview, sensitive_columns)

        return SanitizedPreviewResponse(
            dataset_id=dataset_id,
            columns=columns,
            sensitive_columns=sensitive_columns,
            preview=masked_preview,
        )

    def _detect_sensitive_columns(self, columns: list[str]) -> list[str]:
        """
        Return the subset of column names that match any sensitive pattern.
        Matching is case-insensitive and checks for substring presence.
        """
        sensitive: list[str] = []
        for col in columns:
            col_lower = col.lower()
            if any(pattern in col_lower for pattern in SENSITIVE_COLUMN_PATTERNS):
                sensitive.append(col)
        return sensitive

    def _mask_preview(
        self,
        preview: list[dict],
        sensitive_columns: list[str],
    ) -> list[dict]:
        """
        Replace every value in a sensitive column with "***MASKED***".
        Non-sensitive columns are passed through unchanged.
        """
        if not sensitive_columns:
            return preview
        sensitive_set = set(sensitive_columns)
        masked: list[dict] = []
        for row in preview:
            masked_row = {
                col: ("***MASKED***" if col in sensitive_set else val)
                for col, val in row.items()
            }
            masked.append(masked_row)
        return masked

    # ── 4. Input sanitization ─────────────────────────────────────────────────

    def sanitize_dataframe_values(
        self,
        preview: list[dict],
    ) -> tuple[list[dict], list[str]]:
        """
        Scan cell values for formula injection patterns and neutralise them.

        Spreadsheet formula injection is a known attack vector where cell
        values beginning with =, +, -, @, tab, or carriage return can be
        executed as formulas by spreadsheet applications. This method
        prefixes any such value with a single quote so it is treated as
        plain text.

        Returns the sanitized preview rows and a list of warning messages
        describing any values that were altered, so the frontend can
        inform the user.

        Parameters
        ----------
        preview : list[dict]
            The raw preview rows from the uploaded dataset.

        Returns
        -------
        tuple[list[dict], list[str]]
            - sanitized preview rows
            - list of warning strings (empty if nothing was altered)
        """
        sanitized: list[dict] = []
        warnings: list[str] = []
        flagged_columns: set[str] = set()

        for row in preview:
            sanitized_row: dict = {}
            for col, val in row.items():
                if isinstance(val, str) and val.startswith(_FORMULA_INJECTION_PREFIXES):
                    sanitized_row[col] = f"'{val}"
                    flagged_columns.add(col)
                else:
                    sanitized_row[col] = val
            sanitized.append(sanitized_row)

        if flagged_columns:
            warnings.append(
                f"Potentially unsafe values were detected and neutralised in "
                f"column(s): {sorted(flagged_columns)}. "
                f"Values beginning with formula characters (=, +, -, @) have "
                f"been prefixed with a quote to prevent formula injection."
            )

        return sanitized, warnings

    # ── Full security summary ─────────────────────────────────────────────────

    def get_security_summary(
        self,
        dataset_id: str,
        session_id: str,
        columns: list[str],
        preview: list[dict],
    ) -> SecuritySummaryResponse:
        """
        Run all four security checks and return a consolidated summary.

        The frontend can call this to display a security overview to the
        user showing:
          - whether their session owns the dataset
          - when the dataset expires
          - which columns contain sensitive data
          - whether any cell values were sanitized

        Raises the same access/expiry errors as check_access().
        """
        access = self.check_access(dataset_id=dataset_id, session_id=session_id)
        sensitive_columns = self._detect_sensitive_columns(columns)
        _, sanitization_warnings = self.sanitize_dataframe_values(preview)

        warnings: list[str] = []
        if sensitive_columns:
            warnings.append(
                f"Sensitive column(s) detected: {sensitive_columns}. "
                f"Values are masked in previews."
            )
        warnings.extend(sanitization_warnings)

        return SecuritySummaryResponse(
            dataset_id=dataset_id,
            session_id=session_id,
            access_granted=access.access_granted,
            is_expired=access.is_expired,
            expires_at=access.expires_at,
            sensitive_columns=sensitive_columns,
            warnings=warnings,
        )

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


# =============================================================================
# In-memory dataset registry — DELETE when database is connected
# Maps dataset_id -> { session_id, created_at }
# =============================================================================
DATASET_REGISTRY: dict[str, dict] = {}