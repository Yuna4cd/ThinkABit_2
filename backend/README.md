# Backend Skeleton

## Run locally

1. Create virtual environment and install dependencies from `requirements.txt`.
2. (Optional but recommended) Start local MinIO:

```bash
docker compose -f backend/docker-compose.minio.yml up -d
```

3. Copy env template and adjust values if needed:

```bash
cp backend/.env.example backend/.env
```

4. Start API:

```bash
uvicorn app.main:app --reload --app-dir backend
```

## Endpoints in skeleton

- `GET /health`
- `POST /api/v1/upload`
- `POST /api/v1/chat`

Current upload route accepts multipart request and returns contract-compatible
response shape. Validation, storage write, and dataframe parsing are scaffolded
for later tasks.

## Supabase Metadata Table (MVP)

Migration SQL file:

- `backend/supabase/migrations/init_supabase_datasets_metadata_mvp.sql`

Verification SQL file:

- `backend/supabase/verification/verify_datasets_metadata_mvp.sql`
- `backend/supabase/migrations/extend_datasets_metadata_for_dataset_get.sql` (run before `GET /api/v1/datasets/{dataset_id}` work)

Manual steps (Supabase):

1. Open Supabase SQL Editor for your target project.
2. Run the migration SQL file.
3. Run the verification SQL file and check:
   - `public.datasets` exists with expected columns.
   - enum `public.dataset_parse_status` has `uploaded/parsing/ready/failed`.
   - trigger `trg_datasets_set_updated_at` exists and updates `updated_at`.

Manual settings:

- If you use a schema other than `public`, replace `public.` prefixes in both SQL files.
- For later app integration (Task 8/9), configure:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `DATABASE_URL`
  - `METASTORE_INSERT_ENABLED`

## MinIO Upload Notes

- Upload to object storage is controlled by `MINIO_UPLOAD_ENABLED`.
- `MINIO_UPLOAD_ENABLED=true` enables real `put_object` writes.
- Default local endpoint is `http://localhost:19000` and bucket is `thinkabit-raw`.
- Metadata insert to Supabase Postgres is controlled by `METASTORE_INSERT_ENABLED`.
