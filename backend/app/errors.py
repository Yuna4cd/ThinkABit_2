from uuid import uuid4

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.upload import ErrorBody, ErrorResponse


class APIError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict,
        request_id: str,
    ) -> None:
        self.status_code = status_code
        self.payload = ErrorResponse(
            error=ErrorBody(
                code=code,
                message=message,
                details=details,
                request_id=request_id,
            )
        ).model_dump()


async def api_error_handler(_: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.payload)


async def request_validation_error_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorBody(
            code="INVALID_REQUEST",
            message="Request validation failed.",
            details={"errors": exc.errors()},
            request_id=f"req_{uuid4().hex[:8]}",
        )
    ).model_dump()
    return JSONResponse(status_code=400, content=payload)
