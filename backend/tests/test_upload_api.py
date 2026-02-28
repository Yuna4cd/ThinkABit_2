from fastapi.testclient import TestClient


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
