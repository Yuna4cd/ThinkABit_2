"""
app/api/v1/workflow.py
-----------------------
FastAPI router for saving and resuming user workflow state.

Endpoints
---------
POST /api/v1/sessions/{session_id}/workflow
    Save (or overwrite) the current workflow state for a session.
    The frontend calls this periodically and on key user actions
    (e.g. selecting a plot type, completing cleaning) so progress
    is checkpointed without the user having to do anything.

GET  /api/v1/sessions/{session_id}/workflow/latest
    Retrieve the most recently saved workflow state for a session.
    The frontend calls this on page load to restore the user's progress
    if they exited the site accidentally.

URL pattern follows the API contract convention:
    /api/v1/sessions/{session_id}/...
using session_id — the same identity token already present in the
upload flow — so no new auth concept is needed.
"""

from fastapi import APIRouter

from app.schemas.workflow import WorkflowResponse, WorkflowSaveRequest
from app.services.workflow_service import WorkflowService

router = APIRouter()
workflow_service = WorkflowService()


@router.post(
    "/sessions/{session_id}/workflow",
    response_model=WorkflowResponse,
    status_code=200,
)
def save_workflow(
    session_id: str,
    body: WorkflowSaveRequest,
) -> WorkflowResponse:
    """
    Save the current workflow state for a session.

    Overwrites any previously saved state for this session_id — only
    the most recent save is kept.

    The frontend should call this:
      - When the user selects a plot type
      - When the user changes a channel setting (color, shape, size, position)
      - When the user completes a cleaning step
      - When the user moves to a new stage of the analytics process
      - Periodically as an auto-save (e.g. every 30 seconds)

    Returns the saved state including the `saved_at` timestamp so the
    frontend can display "Last saved at HH:MM" to the user.
    """
    return workflow_service.save_workflow(session_id=session_id, body=body)


@router.get(
    "/sessions/{session_id}/workflow/latest",
    response_model=WorkflowResponse,
    status_code=200,
)
def get_latest_workflow(session_id: str) -> WorkflowResponse:
    """
    Retrieve the most recently saved workflow state for a session.

    The frontend calls this on page load. If a saved state exists the
    user is prompted to resume where they left off. If not (404) the
    frontend starts a fresh session normally.

    Raises 404 when no saved workflow exists for the given session_id.
    This is the expected response for a brand new session.
    """
    return workflow_service.get_latest_workflow(session_id=session_id)