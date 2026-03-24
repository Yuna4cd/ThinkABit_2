from typing import Any
from pydantic import BaseModel, Field


class CleanResponse(BaseModel):
    """
    Response returned after a user triggers null-row cleaning on their dataset.

    Fields
    ------
    dataset_id        : ID of the dataset that was cleaned.
    rows_before       : Total row count before cleaning.
    rows_after        : Total row count after null rows were dropped.
    null_rows_dropped : Number of rows removed because they contained at
                        least one missing value.
    columns           : Ordered list of column names in the cleaned dataset.
    preview           : First rows of the cleaned dataset so the frontend
                        can show the user what their data looks like after
                        cleaning. Same serialization format as the upload
                        preview (nulls -> None, datetimes -> ISO-8601 string).
    """
    dataset_id:        str
    rows_before:       int = Field(ge=0)
    rows_after:        int = Field(ge=0)
    null_rows_dropped: int = Field(ge=0)
    columns:           list[str]
    preview:           list[dict[str, Any]]