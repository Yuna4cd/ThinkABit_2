import sys
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Keep tests hermetic: do not require a running MinIO instance.
os.environ.setdefault("MINIO_UPLOAD_ENABLED", "false")
os.environ.setdefault("METASTORE_INSERT_ENABLED", "false")

from app.main import app  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
