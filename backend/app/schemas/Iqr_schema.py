"""
app/schemas/iqr.py
-------------------
Pydantic schemas for the IQR (Interquartile Range) outlier detection tool.

IQR outlier detection works by finding the middle 50% of values in a column
(between Q1 and Q3), calculating the spread (IQR = Q3 - Q1), and flagging
any value that falls too far outside that range as an outlier.

Schemas defined here:
    IQRRequest  - Parameters the frontend sends when triggering IQR detection.
                  Includes which column to analyse and the sensitivity multiplier.
    OutlierRow  - A single row flagged as an outlier, including its value
                  and original row index.
    IQRResponse - Full result returned to the frontend including the Q1, Q3,
                  IQR, bounds, outlier rows, and the rule used to flag them.
"""

from typing import Any
from pydantic import BaseModel, Field


class IQRRequest(BaseModel):
    """
    Parameters for the IQR outlier detection request.

    Fields
    ------
    column       : Name of the numeric column to analyse.
    multiplier   : Controls how sensitive the detection is.
                   Standard value is 1.5 — higher means less sensitive
                   (fewer outliers flagged), lower means more sensitive.
                   Must be greater than 0.
    include_bounds: When True (default), values must strictly exceed the
                    bounds to be flagged (< lower or > upper).
                    When False, values exactly on the boundary are also
                    flagged (<= lower or >= upper).
    """
    column:        str
    multiplier:    float = Field(default=1.5, gt=0.0)
    include_bounds: bool = True


class OutlierRow(BaseModel):
    """
    A single row identified as an outlier.

    Fields
    ------
    row_index   : Original row index in the dataset.
    column_value: The value in the analysed column for this row.
    values      : All column values for this row as a JSON-safe dict.
    """
    row_index:    int
    column_value: float
    values:       dict[str, Any]


class IQRResponse(BaseModel):
    """
    Full IQR outlier detection result returned to the frontend.

    Fields
    ------
    dataset_id  : ID of the dataset that was analysed.
    column      : Name of the column that was analysed.
    multiplier  : The multiplier value used in this run.
    q1          : 25th percentile of the column.
    q3          : 75th percentile of the column.
    iqr         : Interquartile range (Q3 - Q1).
    lower_bound : Values below this are flagged as outliers.
    upper_bound : Values above this are flagged as outliers.
    rule        : Plain-English description of the rule used to flag outliers.
    n_outliers  : Number of outlier rows detected.
    outliers    : Full detail for each outlier row.
    outlier_indices: Row indices of all outliers (for quick frontend lookup).
    warnings    : Messages about any issues encountered during processing.
    """
    dataset_id:      str
    column:          str
    multiplier:      float
    q1:              float
    q3:              float
    iqr:             float
    lower_bound:     float
    upper_bound:     float
    rule:            str
    n_outliers:      int   = Field(ge=0)
    outliers:        list[OutlierRow]
    outlier_indices: list[int]
    warnings:        list[str] = Field(default_factory=list)