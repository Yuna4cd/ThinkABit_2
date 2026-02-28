import io
import json
import xml.etree.ElementTree as ET
import zipfile
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import UploadFile
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_float_dtype,
    is_integer_dtype,
    is_object_dtype,
    is_string_dtype,
)

from app.core.config import ROW_CAP
from app.errors import APIError
from app.schemas.upload import (
    ColumnSchema,
    FileMeta,
    MissingSummary,
    Shape,
    StorageRef,
    UploadResponse,
)


class UploadService:
    def __init__(self, raw_bucket: str = "thinkabit-raw") -> None:
        self.raw_bucket = raw_bucket

    async def handle_upload(
        self,
        file: UploadFile,
        session_id: str | None,
        preview_rows: int,
    ) -> UploadResponse:
        dataset_id = f"ds_{uuid4().hex}"
        extension = Path(file.filename or "").suffix.lower().lstrip(".")
        now = datetime.now(UTC)

        object_key = (
            f"raw/{now.year:04d}/{now.month:02d}/{now.day:02d}/{dataset_id}/{file.filename}"
        )

        content = await file.read()
        file_size = len(content)
        await file.seek(0)

        try:
            dataframe = self._parse_to_dataframe(content=content, extension=extension)
            dataframe = self._normalize_columns(dataframe)

            if len(dataframe) > ROW_CAP:
                raise self._build_error(
                    code="ROW_LIMIT_EXCEEDED",
                    message="Row limit exceeded.",
                    details={"row_cap": ROW_CAP},
                    status_code=422,
                )

            schema = self._build_schema(dataframe)
            preview = self._build_preview(dataframe, preview_rows)
            missing_summary = self._build_missing_summary(dataframe)
        except APIError:
            raise
        except Exception as exc:
            raise self._build_error(
                code="PARSE_FAILED",
                message=f"Failed to parse {extension} file.",
                details={"reason": str(exc)[:200]},
                status_code=422,
            ) from exc

        return UploadResponse(
            dataset_id=dataset_id,
            status="ready",
            session_id=session_id,
            file_meta=FileMeta(
                original_filename=file.filename or "unknown",
                extension=extension,
                mime_type=file.content_type or "application/octet-stream",
                size_bytes=file_size,
            ),
            shape=Shape(rows=int(dataframe.shape[0]), columns=int(dataframe.shape[1])),
            schema_=schema,
            preview=preview,
            missing_summary=missing_summary,
            storage=StorageRef(
                provider="s3-compatible",
                bucket=self.raw_bucket,
                object_key=object_key,
            ),
            warnings=[],
        )

    def _parse_to_dataframe(self, content: bytes, extension: str) -> pd.DataFrame:
        if extension == "csv":
            return pd.read_csv(io.BytesIO(content))
        if extension == "json":
            return self._parse_json_to_dataframe(content)
        if extension == "xlsx":
            return self._parse_xlsx_to_dataframe(content)
        raise ValueError(f"Unsupported extension: {extension}")

    def _parse_json_to_dataframe(self, content: bytes) -> pd.DataFrame:
        parsed = json.loads(content.decode("utf-8"))
        if isinstance(parsed, list):
            if not parsed:
                raise ValueError("JSON array is empty.")
            if not all(isinstance(row, dict) for row in parsed):
                raise ValueError("JSON array must contain objects.")
            return pd.DataFrame(parsed)
        if isinstance(parsed, dict):
            if not parsed:
                raise ValueError("JSON object is empty.")
            values = list(parsed.values())
            if not all(isinstance(item, list) for item in values):
                raise ValueError("JSON object values must be arrays.")
            lengths = {len(item) for item in values}
            if len(lengths) > 1:
                raise ValueError("JSON object arrays must have equal lengths.")
            return pd.DataFrame(parsed)
        raise ValueError("JSON root must be an array of objects or an object of arrays.")

    def _parse_xlsx_to_dataframe(self, content: bytes) -> pd.DataFrame:
        main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        package_rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"

        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            workbook = ET.fromstring(archive.read("xl/workbook.xml"))
            rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
            shared_strings = self._load_shared_strings(archive, main_ns)

            sheets_node = workbook.find(f"{{{main_ns}}}sheets")
            if sheets_node is None:
                raise ValueError("Workbook does not contain sheets.")
            first_sheet = sheets_node.find(f"{{{main_ns}}}sheet")
            if first_sheet is None:
                raise ValueError("Workbook does not contain any sheet.")

            relation_id = first_sheet.attrib.get(f"{{{rel_ns}}}id")
            if not relation_id:
                raise ValueError("Sheet relation id is missing.")

            target_path = None
            for relation in rels.findall(f"{{{package_rel_ns}}}Relationship"):
                if relation.attrib.get("Id") == relation_id:
                    target_path = relation.attrib.get("Target")
                    break
            if not target_path:
                raise ValueError("Sheet target path not found in relationships.")

            sheet_path = target_path.lstrip("/")
            if not sheet_path.startswith("xl/"):
                sheet_path = f"xl/{sheet_path}"
            sheet_root = ET.fromstring(archive.read(sheet_path))
            sheet_data = sheet_root.find(f"{{{main_ns}}}sheetData")
            if sheet_data is None:
                raise ValueError("Sheet data is missing.")

            rows: list[dict[int, object]] = []
            max_col = 0
            for row_node in sheet_data.findall(f"{{{main_ns}}}row"):
                row_values: dict[int, object] = {}
                for cell_node in row_node.findall(f"{{{main_ns}}}c"):
                    reference = cell_node.attrib.get("r", "")
                    col_letters = "".join(ch for ch in reference if ch.isalpha())
                    if not col_letters:
                        continue
                    col_index = self._column_letters_to_index(col_letters)
                    cell_type = cell_node.attrib.get("t")
                    row_values[col_index] = self._extract_xlsx_cell_value(
                        cell_node, cell_type, shared_strings, main_ns
                    )
                    max_col = max(max_col, col_index)
                rows.append(row_values)

        if not rows or max_col == 0:
            raise ValueError("Worksheet is empty.")

        matrix: list[list[object | None]] = []
        for row_values in rows:
            matrix.append([row_values.get(index) for index in range(1, max_col + 1)])

        header = matrix[0]
        data_rows = matrix[1:]
        header_names = self._normalize_header_names(header)
        return pd.DataFrame(data_rows, columns=header_names)

    def _load_shared_strings(
        self, archive: zipfile.ZipFile, main_ns: str
    ) -> list[str]:
        if "xl/sharedStrings.xml" not in archive.namelist():
            return []
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        values: list[str] = []
        for item in root.findall(f"{{{main_ns}}}si"):
            text_parts = [node.text or "" for node in item.findall(f".//{{{main_ns}}}t")]
            values.append("".join(text_parts))
        return values

    def _extract_xlsx_cell_value(
        self,
        cell_node: ET.Element,
        cell_type: str | None,
        shared_strings: list[str],
        main_ns: str,
    ) -> object | None:
        if cell_type == "inlineStr":
            text_parts = [
                node.text or "" for node in cell_node.findall(f".//{{{main_ns}}}t")
            ]
            return "".join(text_parts)

        value_node = cell_node.find(f"{{{main_ns}}}v")
        value_text = value_node.text if value_node is not None else None
        if value_text is None:
            return None

        if cell_type == "s":
            index = int(value_text)
            if index >= len(shared_strings):
                raise ValueError("Shared string index out of range.")
            return shared_strings[index]
        if cell_type == "b":
            return value_text == "1"
        if cell_type == "str":
            return value_text
        return self._coerce_numeric(value_text)

    def _coerce_numeric(self, value: str) -> object:
        if value == "":
            return None
        if any(token in value for token in (".", "e", "E")):
            return float(value)
        return int(value)

    def _column_letters_to_index(self, letters: str) -> int:
        index = 0
        for char in letters:
            index = index * 26 + (ord(char.upper()) - ord("A") + 1)
        return index

    def _normalize_header_names(self, header: list[object | None]) -> list[str]:
        names: list[str] = []
        seen: dict[str, int] = {}
        for idx, raw in enumerate(header, start=1):
            base = str(raw).strip() if raw is not None else ""
            if not base:
                base = f"column_{idx}"
            count = seen.get(base, 0) + 1
            seen[base] = count
            names.append(base if count == 1 else f"{base}_{count}")
        return names

    def _normalize_columns(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        renamed = dataframe.copy()
        renamed.columns = self._normalize_header_names(list(renamed.columns))
        return renamed

    def _build_schema(self, dataframe: pd.DataFrame) -> list[ColumnSchema]:
        result: list[ColumnSchema] = []
        for column_name in dataframe.columns:
            series = dataframe[column_name]
            result.append(
                ColumnSchema(
                    name=column_name,
                    dtype=self._map_dtype(series),
                    null_count=int(series.isna().sum()),
                )
            )
        return result

    def _map_dtype(self, series: pd.Series) -> str:
        if series.isna().all():
            return "unknown"
        if is_bool_dtype(series):
            return "bool"
        if is_integer_dtype(series):
            return "int"
        if is_float_dtype(series):
            return "float"
        if is_datetime64_any_dtype(series):
            return "datetime"
        if is_string_dtype(series) or is_object_dtype(series):
            return "string"
        return "unknown"

    def _build_preview(self, dataframe: pd.DataFrame, preview_rows: int) -> list[dict]:
        preview_frame = dataframe.head(preview_rows)
        preview: list[dict] = []
        for _, row in preview_frame.iterrows():
            serialized = {
                str(column): self._serialize_preview_value(row[column])
                for column in preview_frame.columns
            }
            preview.append(serialized)
        return preview

    def _serialize_preview_value(self, value: object) -> object:
        if pd.isna(value):
            return None
        if isinstance(value, pd.Timestamp):
            dt = value.to_pydatetime()
            if dt.tzinfo is None:
                return dt.isoformat() + "Z"
            return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.isoformat() + "Z"
            return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
        if isinstance(value, date):
            return value.isoformat()
        if hasattr(value, "item"):
            return value.item()
        return value

    def _build_missing_summary(self, dataframe: pd.DataFrame) -> MissingSummary:
        null_mask = dataframe.isna()
        return MissingSummary(
            rows_with_missing=int(null_mask.any(axis=1).sum()),
            total_missing_cells=int(null_mask.sum().sum()),
        )

    def _build_error(
        self,
        *,
        code: str,
        message: str,
        details: dict[str, object],
        status_code: int,
    ) -> APIError:
        return APIError(
            status_code=status_code,
            code=code,
            message=message,
            details=details,
            request_id=f"req_{uuid4().hex[:8]}",
        )
