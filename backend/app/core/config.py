import os

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


ALLOWED_EXTENSIONS = {"csv", "xlsx", "json"}
ALLOWED_MIME_TYPES = {
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/json",
}
MIME_TYPES_BY_EXTENSION = {
    "csv": {"text/csv"},
    "xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    "json": {"application/json"},
}

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024
ROW_CAP = 200000
DEFAULT_PREVIEW_ROWS = 100
MAX_PREVIEW_ROWS = 200

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:19000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_RAW_BUCKET = os.getenv("MINIO_RAW_BUCKET", "thinkabit-raw")
MINIO_SECURE = _env_bool("MINIO_SECURE", default=False)
MINIO_AUTO_CREATE_BUCKET = _env_bool("MINIO_AUTO_CREATE_BUCKET", default=True)
MINIO_UPLOAD_ENABLED = _env_bool("MINIO_UPLOAD_ENABLED", default=True)

DATABASE_URL = os.getenv("DATABASE_URL")
METASTORE_INSERT_ENABLED = _env_bool("METASTORE_INSERT_ENABLED", default=True)

# chatbot api key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"