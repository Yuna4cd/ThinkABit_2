from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.upload import router as upload_router
from app.api.v1.chat import router as chat_router
from app.errors import APIError, api_error_handler, request_validation_error_handler


app = FastAPI(
    title="ThinkABit File Upload API",
    version="1.0.0",
    description="Sprint 1 backend skeleton for file upload.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")

app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(RequestValidationError, request_validation_error_handler)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
