from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

import psycopg2


@dataclass
class DatasetInsertRecord:
    dataset_id: str
    parse_status: str
    session_id: str | None
    original_filename: str
    extension: str
    mime_type: str
    size_bytes: int
    row_count: int
    column_count: int
    schema_json: list[dict[str, str | int]]
    storage_key_raw: str


@dataclass
class DatasetMetadataRecord:
    dataset_id: str
    parse_status: str
    session_id: str | None
    original_filename: str
    extension: str
    mime_type: str
    size_bytes: int
    row_count: int
    column_count: int
    created_at: datetime
    updated_at: datetime


@dataclass
class DatasetSchemaRecord:
    dataset_id: str
    schema_json: list[dict[str, str | int]]


class MetastoreService:
    def __init__(self, *, database_url: str | None) -> None:
        self.database_url = database_url

    def insert_dataset_metadata(self, record: DatasetInsertRecord) -> None:
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is not configured")

        query = """
            INSERT INTO public.datasets (
                dataset_id,
                parse_status,
                session_id,
                original_filename,
                extension,
                mime_type,
                size_bytes,
                row_count,
                column_count,
                schema_json,
                storage_key_raw
            )
            VALUES (
                %s,
                %s::public.dataset_parse_status,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s::jsonb,
                %s
            )
        """

        with psycopg2.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        record.dataset_id,
                        record.parse_status,
                        record.session_id,
                        record.original_filename,
                        record.extension,
                        record.mime_type,
                        record.size_bytes,
                        record.row_count,
                        record.column_count,
                        json.dumps(record.schema_json),
                        record.storage_key_raw,
                    ),
                )

    def get_dataset_metadata(self, dataset_id: str) -> DatasetMetadataRecord | None:
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is not configured")

        query = """
            SELECT
                dataset_id,
                parse_status::text,
                session_id,
                original_filename,
                extension,
                mime_type,
                size_bytes,
                COALESCE(row_count, 0),
                COALESCE(column_count, 0),
                created_at,
                updated_at
            FROM public.datasets
            WHERE dataset_id = %s
        """

        with psycopg2.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (dataset_id,))
                row = cursor.fetchone()
                if row is None:
                    return None

        return DatasetMetadataRecord(
            dataset_id=row[0],
            parse_status=row[1],
            session_id=row[2],
            original_filename=row[3],
            extension=row[4],
            mime_type=row[5],
            size_bytes=int(row[6]),
            row_count=int(row[7]),
            column_count=int(row[8]),
            created_at=row[9],
            updated_at=row[10],
        )

    def get_dataset_schema(self, dataset_id: str) -> DatasetSchemaRecord | None:
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is not configured")

        query = """
            SELECT
                dataset_id,
                COALESCE(schema_json, '[]'::jsonb)
            FROM public.datasets
            WHERE dataset_id = %s
        """

        with psycopg2.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (dataset_id,))
                row = cursor.fetchone()
                if row is None:
                    return None

        return DatasetSchemaRecord(
            dataset_id=row[0],
            schema_json=row[1],
        )
