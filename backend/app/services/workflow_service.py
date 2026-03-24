"""
app/services/workflow_service.py
---------------------------------
Business logic for saving and retrieving user workflow state.

PURPOSE
-------
When a user exits the website accidentally, their progress is preserved
so they can resume in a short period of time. The frontend calls
POST /workflow periodically (or on key actions) to checkpoint the state,
and GET /workflow on page load to restore it.

WHAT IS SAVED
-------------
  - dataset_id       : which dataset they uploaded
  - current_stage    : which step of the analytics process they were on
                       (upload → cleaning → visualization → analysis)
  - plot_type        : which chart type they selected
  - channel_settings : color / shape / size / position choices
  - cleaning_state   : which cleaning steps they have completed
  - extra            : free-form bucket for any additional frontend state

DESIGN
------
Only the most recent save per session_id is kept — each POST overwrites
the previous state. This matches the "resume from last known position"
use case without building a full history/versioning system.

DATABASE INTEGRATION
--------------------
Each method has a TODO block showing the Supabase/PostgreSQL query to
drop in when the DB is ready. The in-memory store at the bottom of this
file is the only thing that gets deleted on integration.

Suggested `workflow` table schema (add to your Supabase migration):
    session_id       TEXT PRIMARY KEY
    dataset_id       TEXT NULLABLE
    current_stage    TEXT NULLABLE
    plot_type        TEXT NULLABLE
    channel_settings JSONB NOT NULL DEFAULT '{}'
    cleaning_state   JSONB NOT NULL DEFAULT '{}'
    extra            JSONB NOT NULL DEFAULT '{}'
    saved_at         TIMESTAMPTZ NOT NULL
"""

from datetime import UTC, datetime
from uuid import uuid4

from app.errors import APIError
from app.schemas.workflow import (
    ChannelSettings,
    CleaningState,
    WorkflowResponse,
    WorkflowSaveRequest,
)


class WorkflowService:

    def save_workflow(
        self,
        session_id: str,
        body: WorkflowSaveRequest,
    ) -> WorkflowResponse:
        """
        Save (or overwrite) the workflow state for a session.

        Creates a new record if this session_id has never saved before,
        otherwise replaces the existing record entirely.

        TODO (DB):
            now = datetime.now(UTC)
            record = {
                "session_id":       session_id,
                "dataset_id":       body.dataset_id,
                "current_stage":    body.current_stage,
                "plot_type":        body.plot_type,
                "channel_settings": body.channel_settings.model_dump(),
                "cleaning_state":   body.cleaning_state.model_dump(),
                "extra":            body.extra,
                "saved_at":         now,
            }
            db.execute(
                \"\"\"
                INSERT INTO workflow (session_id, dataset_id, current_stage,
                    plot_type, channel_settings, cleaning_state, extra, saved_at)
                VALUES (:session_id, :dataset_id, :current_stage,
                    :plot_type, :channel_settings, :cleaning_state, :extra, :saved_at)
                ON CONFLICT (session_id)
                DO UPDATE SET
                    dataset_id       = EXCLUDED.dataset_id,
                    current_stage    = EXCLUDED.current_stage,
                    plot_type        = EXCLUDED.plot_type,
                    channel_settings = EXCLUDED.channel_settings,
                    cleaning_state   = EXCLUDED.cleaning_state,
                    extra            = EXCLUDED.extra,
                    saved_at         = EXCLUDED.saved_at
                \"\"\",
                record,
            )
            db.commit()
            return WorkflowResponse(session_id=session_id, saved_at=now, **record)
        """
        now = datetime.now(UTC)
        record = {
            "session_id":       session_id,
            "dataset_id":       body.dataset_id,
            "current_stage":    body.current_stage,
            "plot_type":        body.plot_type,
            "channel_settings": body.channel_settings,
            "cleaning_state":   body.cleaning_state,
            "extra":            body.extra,
            "saved_at":         now,
        }
        WORKFLOW_STORE[session_id] = record
        return WorkflowResponse(**record)

    def get_latest_workflow(self, session_id: str) -> WorkflowResponse:
        """
        Retrieve the most recently saved workflow state for a session.

        Raises APIError 404 when no saved state exists for the session —
        this is the normal case for a brand new session.

        TODO (DB):
            row = db.execute(
                "SELECT * FROM workflow WHERE session_id = :session_id",
                {"session_id": session_id},
            ).fetchone()
            if row is None:
                raise self._build_error(
                    code="WORKFLOW_NOT_FOUND", ...
                )
            return WorkflowResponse(
                session_id=row.session_id,
                dataset_id=row.dataset_id,
                current_stage=row.current_stage,
                plot_type=row.plot_type,
                channel_settings=ChannelSettings(**row.channel_settings),
                cleaning_state=CleaningState(**row.cleaning_state),
                extra=row.extra,
                saved_at=row.saved_at,
            )
        """
        record = WORKFLOW_STORE.get(session_id)
        if record is None:
            raise self._build_error(
                code="WORKFLOW_NOT_FOUND",
                message=f"No saved workflow found for session '{session_id}'.",
                details={"session_id": session_id},
                status_code=404,
            )
        return WorkflowResponse(**record)

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
# In-memory store — DELETE when database is connected
# Maps session_id -> most recent workflow record dict
# =============================================================================
WORKFLOW_STORE: dict[str, dict] = {}