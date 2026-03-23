import io
import zipfile
from datetime import UTC, datetime
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.core.config import MAX_FILE_SIZE_BYTES
from app.api.v1 import upload as upload_module


def build_valid_xlsx_bytes() -> bytes:
    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>
"""
    root_rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""
    workbook = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
"""
    workbook_rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>
"""
    sheet = """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1">
      <c r="A1" t="inlineStr"><is><t>name</t></is></c>
      <c r="B1" t="inlineStr"><is><t>score</t></is></c>
    </row>
    <row r="2">
      <c r="A2" t="inlineStr"><is><t>Alice</t></is></c>
      <c r="B2"><v>90</v></c>
    </row>
    <row r="3">
      <c r="A3" t="inlineStr"><is><t>Bob</t></is></c>
      <c r="B3"><v>85</v></c>
    </row>
  </sheetData>
</worksheet>
"""
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    return stream.getvalue()


def build_sniffable_broken_xlsx_bytes() -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            "<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'/>",
        )
        archive.writestr("xl/dummy.xml", "<dummy/>")
    return stream.getvalue()


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
    assert payload["status"] == "ready"
    assert payload["session_id"] == "sess_demo_1"
    assert "file_meta" in payload
    assert payload["file_meta"]["extension"] == "csv"
    assert payload["shape"]["rows"] == 1
    assert payload["shape"]["columns"] == 2
    assert len(payload["schema"]) == 2
    assert len(payload["preview"]) == 1
    assert "shape" in payload
    assert "schema" in payload
    assert "preview" in payload
    assert "missing_summary" in payload
    assert "storage" in payload
    assert payload["warnings"] == []


def test_upload_valid_json_object_of_arrays_parses_successfully(client: TestClient) -> None:
    files = {
        "file": (
            "sample.json",
            b'{"name": ["Alice", "Bob"], "score": [90, 85]}',
            "application/json",
        )
    }
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["shape"]["rows"] == 2
    assert payload["shape"]["columns"] == 2
    assert payload["schema"][0]["name"] == "name"


def test_upload_valid_xlsx_parses_successfully(client: TestClient) -> None:
    files = {
        "file": (
            "sample.xlsx",
            build_valid_xlsx_bytes(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["shape"]["rows"] == 2
    assert payload["shape"]["columns"] == 2
    assert payload["preview"][0]["name"] == "Alice"


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


def test_upload_malformed_csv_returns_parse_failed(client: TestClient) -> None:
    files = {"file": ("sample.csv", b'a,b\n"1,2', "text/csv")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 422
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "PARSE_FAILED"


def test_upload_non_tabular_json_returns_parse_failed(client: TestClient) -> None:
    files = {"file": ("sample.json", b'{"a":1,"b":2}', "application/json")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 422
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "PARSE_FAILED"


def test_upload_with_storage_enabled_calls_put_object(
    client: TestClient, monkeypatch
) -> None:
    mock_storage = Mock()
    monkeypatch.setattr(upload_module.upload_service, "storage_enabled", True)
    monkeypatch.setattr(upload_module.upload_service, "storage_service", mock_storage)

    payload_bytes = b"col1,col2\n1,2\n"
    files = {"file": ("sample.csv", payload_bytes, "text/csv")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 201
    mock_storage.put_object.assert_called_once()
    call_kwargs = mock_storage.put_object.call_args.kwargs
    assert call_kwargs["file_bytes"] == payload_bytes
    assert call_kwargs["content_type"] == "text/csv"
    assert "raw/" in call_kwargs["key"]


def test_upload_storage_error_returns_storage_error(
    client: TestClient, monkeypatch
) -> None:
    failing_storage = Mock()
    failing_storage.put_object.side_effect = RuntimeError("simulated storage failure")
    monkeypatch.setattr(upload_module.upload_service, "storage_enabled", True)
    monkeypatch.setattr(
        upload_module.upload_service, "storage_service", failing_storage
    )

    files = {"file": ("sample.csv", b"col1,col2\n1,2\n", "text/csv")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 500
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "STORAGE_ERROR"


def test_upload_with_metastore_enabled_calls_insert(
    client: TestClient, monkeypatch
) -> None:
    mock_metastore = Mock()
    monkeypatch.setattr(upload_module.upload_service, "storage_enabled", False)
    monkeypatch.setattr(upload_module.upload_service, "metastore_enabled", True)
    monkeypatch.setattr(upload_module.upload_service, "metastore_service", mock_metastore)

    files = {"file": ("sample.csv", b"col1,col2\n1,2\n", "text/csv")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 201
    mock_metastore.insert_dataset_metadata.assert_called_once()
    record = mock_metastore.insert_dataset_metadata.call_args.args[0]
    assert record.parse_status == "ready"
    assert record.session_id is None
    assert record.original_filename == "sample.csv"
    assert record.size_bytes == len(b"col1,col2\n1,2\n")
    assert record.row_count == 1
    assert record.column_count == 2
    assert "raw/" in record.storage_key_raw


def test_upload_metastore_error_returns_metastore_error(
    client: TestClient, monkeypatch
) -> None:
    failing_metastore = Mock()
    failing_metastore.insert_dataset_metadata.side_effect = RuntimeError(
        "simulated metastore failure"
    )
    monkeypatch.setattr(upload_module.upload_service, "storage_enabled", False)
    monkeypatch.setattr(upload_module.upload_service, "metastore_enabled", True)
    monkeypatch.setattr(upload_module.upload_service, "metastore_service", failing_metastore)

    files = {"file": ("sample.csv", b"col1,col2\n1,2\n", "text/csv")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 500
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "METASTORE_ERROR"


def test_upload_sniffable_broken_xlsx_returns_parse_failed(client: TestClient) -> None:
    files = {
        "file": (
            "sample.xlsx",
            build_sniffable_broken_xlsx_bytes(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 422
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "PARSE_FAILED"


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


def test_get_dataset_returns_metadata_payload(client: TestClient, monkeypatch) -> None:
    now = datetime.now(UTC)
    mock_metastore = Mock()
    mock_metastore.get_dataset_metadata.return_value = type(
        "Record",
        (),
        {
            "dataset_id": "ds_test_001",
            "parse_status": "ready",
            "session_id": "sess_abc",
            "original_filename": "sample.csv",
            "extension": "csv",
            "mime_type": "text/csv",
            "size_bytes": 14,
            "row_count": 1,
            "column_count": 2,
            "created_at": now,
            "updated_at": now,
        },
    )()
    monkeypatch.setattr(upload_module, "metastore_service", mock_metastore)

    response = client.get("/api/v1/datasets/ds_test_001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset_id"] == "ds_test_001"
    assert payload["status"] == "ready"
    assert payload["session_id"] == "sess_abc"
    assert payload["file_meta"]["original_filename"] == "sample.csv"
    assert payload["shape"]["rows"] == 1
    assert payload["shape"]["columns"] == 2
    assert "created_at" in payload
    assert "updated_at" in payload


def test_get_dataset_not_found_returns_dataset_not_found(
    client: TestClient, monkeypatch
) -> None:
    mock_metastore = Mock()
    mock_metastore.get_dataset_metadata.return_value = None
    monkeypatch.setattr(upload_module, "metastore_service", mock_metastore)

    response = client.get("/api/v1/datasets/ds_missing")

    assert response.status_code == 404
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "DATASET_NOT_FOUND"


def test_get_dataset_metastore_error_returns_metastore_error(
    client: TestClient, monkeypatch
) -> None:
    mock_metastore = Mock()
    mock_metastore.get_dataset_metadata.side_effect = RuntimeError(
        "simulated read failure"
    )
    monkeypatch.setattr(upload_module, "metastore_service", mock_metastore)

    response = client.get("/api/v1/datasets/ds_test_002")

    assert response.status_code == 500
    payload = response.json()
    assert_error_schema(payload)
    assert payload["error"]["code"] == "METASTORE_ERROR"
