from pydantic import BaseModel, Field
from app.schemas.upload import ColumnMissingDetail, MissingSummary


class DatasetWarningsResponse(BaseModel):
    """
    Response returned by GET /api/v1/datasets/{dataset_id}/warnings.

    Gives the frontend everything it needs to display a missing value
    notification to the user at any point after upload — not just
    immediately when the file was uploaded.

    Fields
    ------
    dataset_id      : ID of the dataset being described.
    has_missing     : True when any missing values exist. The frontend
                      uses this as the simple flag to decide whether to
                      show a notification at all.
    missing_summary : Overall counts — total missing cells and rows
                      affected. Same object already present in UploadResponse
                      so the frontend can handle it the same way.
    missing_detail  : Per-column breakdown — which columns have missing
                      values, how many, and what percentage. Empty list
                      when has_missing is False.
    warnings        : Human-readable notification messages ready to display
                      directly in the UI. Empty list when has_missing is False.
    """
    dataset_id:      str
    has_missing:     bool
    missing_summary: MissingSummary
    missing_detail:  list[ColumnMissingDetail] = Field(default_factory=list)
    warnings:        list[str]               = Field(default_factory=list)