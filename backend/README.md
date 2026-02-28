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
