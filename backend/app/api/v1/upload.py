from fastapi import APIRouter, File, Form, UploadFile

from app.core.config import DEFAULT_PREVIEW_ROWS
from app.schemas.upload import SourceType, UploadResponse
from app.services.upload_service import UploadService
from app.services.upload_validator import UploadValidator


router = APIRouter()
upload_service = UploadService()
upload_validator = UploadValidator()


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=201,
)
async def upload_dataset(
    file: UploadFile = File(...),
    session_id: str | None = Form(default=None, max_length=128),
    source: SourceType = Form(default="user_upload"),
    preview_rows: int = Form(default=DEFAULT_PREVIEW_ROWS),
) -> UploadResponse:
    upload_validator.validate(file=file, preview_rows=preview_rows)

    _ = source
    return await upload_service.handle_upload(
        file=file,
        session_id=session_id,
        preview_rows=preview_rows,
    )
