import io
import zipfile

from fastapi.testclient import TestClient

from app.core.config import MAX_FILE_SIZE_BYTES


def assert_error_schema(payload: dict) -> None:
    assert "error" in payload
    error = payload["error"]
    assert isinstance(error, dict)
    assert "code" in error
    assert "message" in error
    assert "details" in error
    assert "request_id" in error


def test_upload_valid_request_returns_structured_response(client: TestClient) -> None:
    files = {"file": ("sample.csv", b"col1,col2\n1,2\n", "text/csv")}
    data = {
        "session_id": "sess_demo_1",
        "source": "user_upload",
        "preview_rows": "50",
    }

    response = client.post("/api/v1/upload", files=files, data=data)

    assert response.status_code == 201
    payload = response.json()
    assert "dataset_id" in payload
    assert payload["status"] == "uploaded"
    assert payload["session_id"] == "sess_demo_1"
    assert "file_meta" in payload
    assert payload["file_meta"]["extension"] == "csv"
    assert "shape" in payload
    assert "schema" in payload
    assert "preview" in payload
    assert "missing_summary" in payload
    assert "storage" in payload
    assert "warnings" in payload


def test_upload_invalid_preview_rows_returns_error_schema(client: TestClient) -> None:
    files = {"file": ("sample.csv", b"col1,col2\n1,2\n", "text/csv")}
    response = client.post(
        "/api/v1/upload",
        files=files,
        data={"preview_rows": "0"},
    )

    assert response.status_code == 400
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "INVALID_REQUEST"


def test_upload_unsupported_extension_returns_error_schema(client: TestClient) -> None:
    files = {"file": ("sample.txt", b"hello", "text/plain")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 415
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


def test_upload_disallowed_mime_returns_error_schema(client: TestClient) -> None:
    files = {"file": ("sample.csv", b"col1,col2\n1,2\n", "application/pdf")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 415
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "MIME_TYPE_NOT_ALLOWED"


def test_upload_unsafe_filename_returns_error_schema(client: TestClient) -> None:
    files = {"file": ("../sample.csv", b"col1,col2\n1,2\n", "text/csv")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 400
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "UNSAFE_FILENAME"


def test_upload_mime_extension_mismatch_returns_error_schema(client: TestClient) -> None:
    files = {"file": ("sample.csv", b"col1,col2\n1,2\n", "application/json")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 415
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "MIME_EXTENSION_MISMATCH"


def test_upload_oversized_file_returns_error_schema(client: TestClient) -> None:
    oversized_content = b"a" * (MAX_FILE_SIZE_BYTES + 1)
    files = {"file": ("sample.csv", oversized_content, "text/csv")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 413
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "FILE_TOO_LARGE"


def test_upload_spoofed_xlsx_content_returns_error_schema(client: TestClient) -> None:
    files = {
        "file": (
            "sample.xlsx",
            b"this is plain text not a zip-based xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 415
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "MIME_EXTENSION_MISMATCH"


def test_upload_fake_zip_xlsx_returns_error_schema(client: TestClient) -> None:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("not_excel.txt", "hello")
    files = {
        "file": (
            "sample.xlsx",
            stream.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 415
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "MIME_EXTENSION_MISMATCH"


def test_upload_empty_file_returns_error_schema(client: TestClient) -> None:
    files = {"file": ("sample.csv", b"", "text/csv")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 422
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "EMPTY_FILE"


def test_upload_control_char_filename_returns_error_schema(client: TestClient) -> None:
    files = {"file": ("bad\x1fname.csv", b"col1,col2\n1,2\n", "text/csv")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 400
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "UNSAFE_FILENAME"


def test_upload_missing_mime_type_returns_error_schema(client: TestClient) -> None:
    files = {"file": ("sample.csv", b"col1,col2\n1,2\n", "")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 415
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "MIME_TYPE_NOT_ALLOWED"


def test_upload_missing_file_returns_error_schema(client: TestClient) -> None:
    response = client.post("/api/v1/upload", data={"preview_rows": "10"})

    assert response.status_code == 400
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "INVALID_REQUEST"


def test_upload_invalid_source_returns_error_schema(client: TestClient) -> None:
    files = {"file": ("sample.csv", b"col1,col2\n1,2\n", "text/csv")}
    response = client.post(
        "/api/v1/upload",
        files=files,
        data={"source": "invalid_source"},
    )

    assert response.status_code == 400
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "INVALID_REQUEST"


def test_upload_session_id_too_long_returns_error_schema(client: TestClient) -> None:
    files = {"file": ("sample.csv", b"col1,col2\n1,2\n", "text/csv")}
    long_session_id = "s" * 129
    response = client.post(
        "/api/v1/upload",
        files=files,
        data={"session_id": long_session_id},
    )

    assert response.status_code == 400
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "INVALID_REQUEST"
