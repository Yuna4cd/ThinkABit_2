from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.v1.upload import router as upload_router
from app.errors import APIError, api_error_handler, request_validation_error_handler


app = FastAPI(
    title="ThinkABit File Upload API",
    version="1.0.0",
    description="Sprint 1 backend skeleton for file upload.",
)

app.include_router(upload_router, prefix="/api/v1")
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(RequestValidationError, request_validation_error_handler)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
