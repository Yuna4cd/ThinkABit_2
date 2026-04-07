from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.v1.upload import router as upload_router
from app.api.v1.visualization import router as visualization_router
from app.api.v1.clean import router as null_router
from app.api.v1.workflow import router as workflow_router
from app.api.v1.security import router as security_router
from app.errors import APIError, api_error_handler, request_validation_error_handler
from app.api.v1.warnings import router as warnings_router


app = FastAPI(
    title="ThinkABit File Upload API",
    version="1.0.0",
    description="Sprint 1 backend skeleton for file upload.",
)

app.include_router(upload_router, prefix="/api/v1")
app.include_router(visualization_router, prefix="/api/v1")
app.include_router(null_router, prefix="/api/v1")
app.include_router(workflow_router, prefix="/api/v1")
app.include_router(security_router, prefix="/api/v1")
app.include_router(warnings_router, prefix="/api/v1")

app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(RequestValidationError, request_validation_error_handler)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}