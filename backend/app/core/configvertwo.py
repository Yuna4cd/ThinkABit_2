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

# ── Security constants ────────────────────────────────────────────────────────
# How long a dataset is retained before it is considered expired.
DATASET_EXPIRY_DAYS = 7

# Column name patterns treated as sensitive — values are masked in previews.
# Add new patterns here as needed; matching is case-insensitive substring check.
SENSITIVE_COLUMN_PATTERNS = [
    "ssn", "social_security",
    "password", "passwd",
    "credit_card", "card_number", "cvv",
    "bank_account", "account_number",
    "passport",
    "license",
    "dob", "date_of_birth", "birthdate",
    "phone", "mobile",
    "email",
    "address", "zip", "postal",
    "salary", "income", "wage",
    "tax_id", "ein", "tin",
]