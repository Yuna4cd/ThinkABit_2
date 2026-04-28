"""
app/schemas/mahalanobis.py
---------------------------
Pydantic schemas for the Mahalanobis outlier detection tool.

Mahalanobis distance measures how far each row is from the center of
the dataset, accounting for correlations between columns. Rows whose
distance exceeds a chi-square threshold are flagged as outliers.

Schemas defined here:
    MahalanobisRequest  - Optional parameters the frontend sends when
                          triggering outlier detection (alpha significance level).
    OutlierRow          - A single row flagged as an outlier, including its
                          distance score and original column values.
    MahalanobisResponse - Full result returned to the frontend including
                          outlier rows, all distances, threshold used,
                          and any warnings generated during processing.
"""

from typing import Any
from pydantic import BaseModel, Field


class MahalanobisRequest(BaseModel):
    """
    Optional parameters for the outlier detection request.

    Fields
    ------
    alpha : Significance level for the chi-square threshold.
            Lower = stricter (fewer rows flagged as outliers).
            Default 0.01 (1% significance level).
    """
    alpha: float = Field(default=0.01, gt=0.0, lt=1.0)


class OutlierRow(BaseModel):
    """
    A single row identified as an outlier.

    Fields
    ------
    row_index : Original row index in the dataset.
    distance  : Mahalanobis distance score for this row.
    values    : The column values for this row as a JSON-safe dict.
    """
    row_index: int
    distance:  float
    values:    dict[str, Any]


class MahalanobisResponse(BaseModel):
    """
    Full outlier detection result returned to the frontend.

    Fields
    ------
    dataset_id      : ID of the dataset that was analysed.
    n_rows          : Total number of rows analysed.
    n_features      : Number of numeric columns used in the calculation.
    threshold       : Distance cutoff above which a row is flagged as an outlier.
    n_outliers      : Number of outlier rows detected.
    outliers        : Full detail for each outlier row.
    outlier_indices : Row indices of all outliers (for quick frontend lookup).
    distances       : Mahalanobis distance for every row in order.
    warnings        : Messages about columns or rows excluded during processing.
    """
    dataset_id:      str
    n_rows:          int   = Field(ge=0)
    n_features:      int   = Field(ge=0)
    threshold:       float
    n_outliers:      int   = Field(ge=0)
    outliers:        list[OutlierRow]
    outlier_indices: list[int]
    distances:       list[float]
    warnings:        list[str] = Field(default_factory=list)