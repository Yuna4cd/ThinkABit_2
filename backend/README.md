# Backend Skeleton

## Run locally

1. Create virtual environment and install dependencies from `requirements.txt`.
2. Start API:

```bash
uvicorn app.main:app --reload --app-dir backend
```

## Endpoints in skeleton

- `GET /health`
- `POST /api/v1/upload`

Current upload route accepts multipart request and returns contract-compatible
response shape. Validation, storage write, and dataframe parsing are scaffolded
for later tasks.

## Supabase Metadata Table (MVP)

Migration SQL file:

- `backend/supabase/migrations/init_supabase_datasets_metadata_mvp.sql`

Verification SQL file:

- `backend/supabase/verification/verify_datasets_metadata_mvp.sql`

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
