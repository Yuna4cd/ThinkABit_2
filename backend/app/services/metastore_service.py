from __future__ import annotations

from dataclasses import dataclass

import psycopg2


@dataclass
class DatasetInsertRecord:
    dataset_id: str
    parse_status: str
    original_filename: str
    extension: str
    mime_type: str
    size_bytes: int
    storage_key_raw: str


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
                original_filename,
                extension,
                mime_type,
                size_bytes,
                storage_key_raw
            )
            VALUES (%s, %s::public.dataset_parse_status, %s, %s, %s, %s, %s)
        """

        with psycopg2.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        record.dataset_id,
                        record.parse_status,
                        record.original_filename,
                        record.extension,
                        record.mime_type,
                        record.size_bytes,
                        record.storage_key_raw,
                    ),
                )
