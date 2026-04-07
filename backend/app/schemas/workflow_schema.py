from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field

# The stages of the analytics process the user can be on
WorkflowStage = Literal[
    "upload",
    "cleaning",
    "visualization",
    "analysis",
]


class ChannelSettings(BaseModel):
    """
    The four visualization customization channels the user has configured.
    All fields are optional — the user may not have set all of them yet.
    """
    color:    str | None = None   # e.g. "#DC143C"
    shape:    str | None = None   # e.g. "circle"
    size:     str | None = None   # e.g. "large"
    position: str | None = None   # e.g. "x=age, y=salary"


class CleaningState(BaseModel):
    """
    Tracks which cleaning steps the user has completed so far.
    New cleaning step types can be added here in future sprints.
    """
    null_rows_dropped: bool = False   # True once POST /clean has been called


class WorkflowSaveRequest(BaseModel):
    """
    Body the frontend sends to POST /api/v1/sessions/{session_id}/workflow.
    Every field except session_id is optional so the frontend can do a
    partial save — only sending what has changed.
    """
    dataset_id:       str | None = None
    current_stage:    WorkflowStage | None = None
    plot_type:        str | None = Field(None, example="scatter")
    channel_settings: ChannelSettings = Field(default_factory=ChannelSettings)
    cleaning_state:   CleaningState   = Field(default_factory=CleaningState)
    extra:            dict[str, Any]  = Field(
        default_factory=dict,
        description="Free-form bucket for any additional frontend state.",
    )


class WorkflowResponse(BaseModel):
    """
    Shape returned by both POST (save) and GET (resume) endpoints.
    Includes a saved_at timestamp so the frontend can show the user
    when their work was last saved.
    """
    session_id:       str
    dataset_id:       str | None
    current_stage:    WorkflowStage | None
    plot_type:        str | None
    channel_settings: ChannelSettings
    cleaning_state:   CleaningState
    extra:            dict[str, Any]
    saved_at:         datetime