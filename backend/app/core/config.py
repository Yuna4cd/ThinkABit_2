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
DEFAULT_PREVIEW_ROWS = 100
MAX_PREVIEW_ROWS = 200
