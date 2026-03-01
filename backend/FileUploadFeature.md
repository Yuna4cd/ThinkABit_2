# File Upload API Contract (Sprint 1) + Roadmap (Sprint 2-3)

Version: `v1`  
Status: `reviewed`  
Owner: `backend (YongShen)`  

## 1) Scope and Decisions

- Supported file types: `csv`, `xlsx`, `json`
- Not supported: `pdf`
- Backend stack: `Python + FastAPI + pandas`
- Metastore: `Supabase (PostgreSQL)`
- Object storage: `MinIO` now, S3-compatible contract by design
- Upload size limit: `25 MB`
- Upload response includes: `dataset_id + schema + preview`
- Session model: `session_id` (anonymous)

## 2) Base API Rules

- Base path: `/api/v1`
- Resource naming: use plural resources (`/datasets/{dataset_id}`), not `/dataset/{id}`
- Content type:
- Upload endpoint uses `multipart/form-data`
- All non-upload responses use `application/json`
- Time format: ISO-8601 UTC, e.g. `2026-02-28T18:25:43Z`
- Error response shape is consistent for all endpoints

## 3) Validation and Parse Constraints

- Allowed extensions: `.csv`, `.xlsx`, `.json`
- Allowed MIME types:
- `text/csv`
- `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `application/json`
- Extension and MIME must both pass validation
- Reject unsafe filename patterns:
- path traversal (`../`, `..\\`)
- control characters
- blank filename
- Max file size: `25 MB`
- Parse timeout: `30 seconds`
- Row cap: `200000` rows
- Preview row default: `100`, max: `200`

## 4) Canonical Data Model (DataFrame-like)

- Canonical tabular object:
- `columns`: ordered array of column names
- `dtypes`: map of column name -> canonical type
- `rows`: tabular records
- Canonical type mapping:
- `string`, `int`, `float`, `bool`, `datetime`, `unknown`
- Missing values are normalized to `null`

## 4.1) Task 4 Parsing Assumptions (Confirmed)

- JSON supported shapes for Sprint 1:
- top-level `array of objects`
- top-level `object of arrays`
- Excel parsing strategy: read first worksheet only (`sheet_name=0`)
- Datetime values in preview are serialized as ISO-8601 strings

## 5) API Endpoints

### 5.1 POST `/api/v1/upload`

Uploads a dataset file, validates it, parses it, stores it, and returns metadata + preview.

Request (`multipart/form-data`):

- `file` (required): binary file
- `session_id` (optional): string, max 128
- `source` (optional): enum `user_upload | sample`, default `user_upload`
- `preview_rows` (optional): integer `1..200`, default `100`

Success `201`:

```json
{
  "dataset_id": "ds_01JX5F8QH9P5Y7M3S4V8N2K6TQ",
  "status": "ready",
  "session_id": "sess_abc123",
  "file_meta": {
    "original_filename": "sales_2025.csv",
    "extension": "csv",
    "mime_type": "text/csv",
    "size_bytes": 184321
  },
  "shape": {
    "rows": 4821,
    "columns": 9
  },
  "schema": [
    {
      "name": "order_id",
      "dtype": "string",
      "null_count": 0
    },
    {
      "name": "order_date",
      "dtype": "datetime",
      "null_count": 2
    },
    {
      "name": "total_amount",
      "dtype": "float",
      "null_count": 13
    }
  ],
  "preview": [
    {
      "order_id": "A001",
      "order_date": "2025-01-02T00:00:00Z",
      "total_amount": 31.25
    }
  ],
  "missing_summary": {
    "rows_with_missing": 49,
    "total_missing_cells": 77
  },
  "storage": {
    "provider": "s3-compatible",
    "bucket": "thinkabit-raw",
    "object_key": "raw/2026/02/28/ds_01JX5F8QH9P5Y7M3S4V8N2K6TQ/sales_2025.csv"
  },
  "warnings": []
}
```

Error examples:

- `400` invalid multipart/form fields
- `413` file too large
- `415` unsupported extension/mime
- `422` parse failed / non-tabular json / empty table
- `500` storage/metastore/internal failure

### 5.2 GET `/api/v1/datasets/{dataset_id}`

Returns upload and parse metadata for a dataset.

Success `200`:

```json
{
  "dataset_id": "ds_01JX5F8QH9P5Y7M3S4V8N2K6TQ",
  "status": "ready",
  "session_id": "sess_abc123",
  "file_meta": {
    "original_filename": "sales_2025.csv",
    "extension": "csv",
    "mime_type": "text/csv",
    "size_bytes": 184321
  },
  "shape": {
    "rows": 4821,
    "columns": 9
  },
  "created_at": "2026-02-28T18:25:43Z",
  "updated_at": "2026-02-28T18:25:44Z"
}
```

### 5.3 GET `/api/v1/datasets/{dataset_id}/schema`

Returns inferred column schema and missing counts.

Success `200`:

```json
{
  "dataset_id": "ds_01JX5F8QH9P5Y7M3S4V8N2K6TQ",
  "schema": [
    {
      "name": "order_id",
      "dtype": "string",
      "null_count": 0
    },
    {
      "name": "total_amount",
      "dtype": "float",
      "null_count": 13
    }
  ]
}
```

### 5.4 GET `/api/v1/datasets/{dataset_id}/preview`

Returns tabular preview rows.

Query params:

- `limit` (optional): integer `1..200`, default `100`
- `offset` (optional): integer `>=0`, default `0`

Success `200`:

```json
{
  "dataset_id": "ds_01JX5F8QH9P5Y7M3S4V8N2K6TQ",
  "limit": 100,
  "offset": 0,
  "rows": [
    {
      "order_id": "A001",
      "order_date": "2025-01-02T00:00:00Z",
      "total_amount": 31.25
    }
  ]
}
```

### 5.5 DELETE `/api/v1/datasets/{dataset_id}`

Deletes dataset metadata from Supabase and best-effort deletes raw object from MinIO.

Success `204`:

- empty body

Error examples:

- `404` dataset not found
- `500` storage/metastore/internal failure

## 6) Unified Error Schema

Every non-2xx response must follow:

```json
{
  "error": {
    "code": "UNSUPPORTED_FILE_TYPE",
    "message": "Only csv, xlsx, json are allowed.",
    "details": {
      "allowed_extensions": [
        "csv",
        "xlsx",
        "json"
      ]
    },
    "request_id": "req_2S9M8P"
  }
}
```

Error code catalog:

- `INVALID_MULTIPART` -> malformed multipart request (`400`)
- `INVALID_REQUEST` -> field validation failed (`400`)
- `FILE_TOO_LARGE` -> exceeds 25MB (`413`)
- `UNSUPPORTED_FILE_TYPE` -> extension not allowed (`415`)
- `MIME_TYPE_NOT_ALLOWED` -> mime not allowed (`415`)
- `MIME_EXTENSION_MISMATCH` -> mime and extension mismatch (`415`)
- `UNSAFE_FILENAME` -> invalid filename/path traversal (`400`)
- `EMPTY_FILE` -> zero-byte file or no rows (`422`)
- `ROW_LIMIT_EXCEEDED` -> exceeds row cap (`422`)
- `PARSE_TIMEOUT` -> parsing exceeded timeout (`408`)
- `PARSE_FAILED` -> parser error for valid type (`422`)
- `DATASET_NOT_FOUND` -> unknown `dataset_id` (`404`)
- `STORAGE_ERROR` -> MinIO/S3 write-read failure (`500`)
- `METASTORE_ERROR` -> Supabase/PostgreSQL operation failure (`500`)
- `INTERNAL_ERROR` -> fallback server error (`500`)

## 7) Storage Contract (MinIO now, S3 later)

Storage contract is strictly S3-compatible to keep migration to AWS S3 frictionless.

- Raw bucket (current): `thinkabit-raw`
- Canonical bucket (optional sprint 1): `thinkabit-canonical`
- Object key format:
- `raw/{yyyy}/{mm}/{dd}/{dataset_id}/{sanitized_filename}`
- `canonical/{yyyy}/{mm}/{dd}/{dataset_id}/dataset.parquet`
- Server stores and returns:
- `provider` (`s3-compatible`)
- `bucket`
- `object_key`
- direct MinIO endpoint is internal and not exposed in API response

## 8) Metastore Fields (Supabase/PostgreSQL Contract-level)

`datasets` table contract:

- `dataset_id` (`text`, pk)
- `session_id` (`text`, nullable)
- `parse_status` (enum-like text: `uploaded | parsing | ready | failed`)
- `original_filename` (`text`)
- `extension` (`text`)
- `mime_type` (`text`)
- `size_bytes` (`bigint`)
- `row_count` (`integer`, nullable)
- `column_count` (`integer`, nullable)
- `storage_bucket_raw` (`text`)
- `storage_key_raw` (`text`)
- `storage_bucket_canonical` (`text`, nullable)
- `storage_key_canonical` (`text`, nullable)
- `error_code` (`text`, nullable)
- `error_message` (`text`, nullable)
- `created_at` (`timestamptz`, UTC)
- `updated_at` (`timestamptz`, UTC)
- Access pattern: backend uses Supabase service role key for metastore writes/reads.
- API response field `status` is mapped from `parse_status`.

## 9) Non-goals in Sprint 1

- Auth/JWT/user accounts
- Presigned URL upload flow
- Async job queue for parsing
- Multi-file batch upload
- PDF ingestion

## 10) Prioritized Task Backlog (All Included)

| Priority | Task | Est. Implementation Time (Hours) |
| --- | --- | ---: |
| P0 | Supabase - metadata table init | 6 |
| P0 | MinIO - `put_object(file_bytes, key, content_type)` | 5 |
| P0 | Supabase - record insert | 5 |
| P0 | Implement `GET /api/v1/datasets/{dataset_id}` | 4 |
| P0 | Implement `GET /api/v1/datasets/{dataset_id}/schema` | 4 |
| P0 | Implement `GET /api/v1/datasets/{dataset_id}/preview` | 6 |
| P0 | Implement `DELETE /api/v1/datasets/{dataset_id}` | 6 |
| P0 | MinIO - `delete_object(key)` | 4 |
| P0 | Supabase - record delete | 4 |
| P0 | Integration test for MinIO -> Metastore | 8 |
| P1 | MinIO - `get_object(key)` | 4 |
| P1 | Background async parse pipeline (`uploaded -> parsing -> ready/failed`) | 14 |
| P2 | Advanced content safety checks (zip-bomb / malicious payload patterns) | 12 |
| P2 | Soft-delete and periodic orphan cleanup jobs | 14 |

Total estimated implementation time: `96 hours`.

## 11) Sprint Plan (20h each, by priority)

| Sprint | Scope | Planned Hours |
| --- | --- | ---: |
| Sprint 2 | Supabase table init (6) + MinIO put (5) + Supabase insert (5) + `GET /datasets/{dataset_id}` (4) | 20 |
| Sprint 3 | `GET /datasets/{dataset_id}/schema` (4) + `GET /datasets/{dataset_id}/preview` (6) + `DELETE /datasets/{dataset_id}` (6) + Supabase delete (4) | 20 |
| Sprint 4 | MinIO delete (4) + MinIO get (4) + Integration test MinIO->Metastore (8) + stabilization buffer (4) | 20 |
| Sprint 5 | Async parse pipeline (14) + Content safety checks phase 1 (6) | 20 |
| Sprint 6 | Content safety checks phase 2 (6) + Soft-delete + orphan cleanup jobs (14) | 20 |

## 12) Acceptance Criteria (Summary)

- All endpoints return responses that match `backend/openapi/upload-api.v1.yaml`.
- All error responses follow the unified error schema in this document.
- Metastore writes/deletes are persisted in Supabase with deterministic behavior.
- MinIO operations (`put/get/delete`) have explicit success and failure handling.
- Integration test validates end-to-end flow: upload -> MinIO -> Supabase -> query -> delete.
- Async pipeline persists and exposes valid state transitions: `uploaded -> parsing -> ready/failed`.
- Security checks block malicious payload patterns without breaking valid uploads.
- Soft-delete and cleanup jobs are repeatable and produce observable run logs.
