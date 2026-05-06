# Docker Deployment Handoff

## Local Build And Run Command

The app was built and run locally with:

```powershell
docker compose up --build
```

## Images

This project uses separate frontend and backend images.

Frontend image:

```text
thinkabit_2-frontend
```

Backend image:

```text
thinkabit_2-backend
```

If these images are pushed to a registry, replace the local image names above with the pushed registry paths, for example:

```text
<registry>/group17/thinkabit-frontend:v1
<registry>/group17/thinkabit-backend:v1
```

## Container Ports

Frontend container:

```text
80
```

Local compose mapping:

```text
5173:80
```

Backend container:

```text
8000
```

Local compose mapping:

```text
8000:8000
```

Supporting services used by compose:

```text
postgres: 5432
minio: 9000
minio console: 9001
```

Local compose maps MinIO as:

```text
19000:9000
19001:9001
```

## Environment Variables

Backend environment variables used by `docker-compose.yml`:

```text
DATABASE_URL=postgresql://thinkabit_user:thinkabit_password@postgres:5432/thinkabit_db
MINIO_ENDPOINT=http://minio:9000
MINIO_PORT=9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=thinkabit-raw
MINIO_SECURE=false
```

Backend also loads:

```text
backend/.env
```

Values expected in `backend/.env` may include:

```text
GEMINI_API_KEY=<real-api-key>
MINIO_UPLOAD_ENABLED=<true-or-false>
METASTORE_INSERT_ENABLED=<true-or-false>
SUPABASE_URL=<optional>
SUPABASE_SERVICE_ROLE_KEY=<optional>
```

Postgres environment variables used by compose:

```text
POSTGRES_USER=thinkabit_user
POSTGRES_PASSWORD=thinkabit_password
POSTGRES_DB=thinkabit_db
```

MinIO environment variables used by compose:

```text
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
```
