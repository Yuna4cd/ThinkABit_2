# Backend Quick Start

This repository keeps `make` commands for macOS and Linux. Windows users should
use the Python CLI documented below instead of `make`.

## Commands

Run all commands from the repository root:

```bash
make backend-setup-minimal
make backend-setup-full
make backend-run
make backend-test
```

The backend virtual environment is created at `backend/.venv`.

## Windows Commands

Run all commands from the repository root:

```bash
python backend/tools/dev.py setup-minimal
python backend/tools/dev.py setup-full
python backend/tools/dev.py run
python backend/tools/dev.py test
```

The Python CLI resolves the virtual environment interpreter from either
`backend/.venv/bin/python` or `backend/.venv/Scripts/python.exe`, so the same
commands work across macOS, Linux, and Windows.

## Minimal Setup

Use minimal mode when you only need the API and test suite.

```bash
make backend-setup-minimal
```

This command:

- creates `backend/.venv` if needed
- installs `backend/requirements.txt`
- creates `backend/.env` from `backend/.env.example` if it does not exist
- sets `MINIO_UPLOAD_ENABLED=false`
- sets `METASTORE_INSERT_ENABLED=false`

After setup:

```bash
make backend-run
make backend-test
```

Windows equivalent:

```bash
python backend/tools/dev.py run
python backend/tools/dev.py test
```

## Full Setup

Use full mode when you need local MinIO plus the remote Supabase/Postgres
connection settings required by the backend metadata flow.

```bash
make backend-setup-full
```

This command:

- runs the full minimal setup flow first
- starts MinIO with `backend/docker-compose.minio.yml`
- sets `MINIO_UPLOAD_ENABLED=true`
- sets `METASTORE_INSERT_ENABLED=true`
- validates `DATABASE_URL`

If `DATABASE_URL` is still a placeholder, setup stops with a clear error after
starting MinIO. The repository does not store real credentials. Your team must
provide the real value separately and save it in `backend/.env`.

## Running the API

```bash
make backend-run
```

This starts:

```bash
backend/.venv/bin/python -m uvicorn app.main:app --reload --app-dir backend
```

Windows-friendly equivalent:

```bash
python backend/tools/dev.py run
```

Health endpoint:

- `GET /health`
- `POST /api/v1/upload`
- `POST /api/v1/chat`

## Running Tests

```bash
make backend-test
```

This runs:

```bash
backend/.venv/bin/python -m pytest backend/tests
```

Windows-friendly equivalent:

```bash
python backend/tools/dev.py test
```

The test suite is hermetic for storage and metastore by default, so it does not
require a running MinIO instance or live database connection.

## Supabase Metadata Table

If your team is using the metadata flow, apply the SQL files in `backend/supabase/` to the target Supabase project:

- `backend/supabase/migrations/init_supabase_datasets_metadata_mvp.sql`
- `backend/supabase/migrations/extend_datasets_metadata_for_dataset_get.sql`
- `backend/supabase/verification/verify_datasets_metadata_mvp.sql`

Manual settings used by the backend:

- `DATABASE_URL`
- `METASTORE_INSERT_ENABLED`

Additional Supabase-related values can stay in `.env` for future integrations,
but the current backend runtime only requires `DATABASE_URL` for metastore
writes.
