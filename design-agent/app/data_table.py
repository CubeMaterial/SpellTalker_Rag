from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from app.settings import Settings


@dataclass
class DataValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass
class DataTable:
    name: str
    path: Path
    headers: list[str]
    rows: list[dict[str, str]]
    validation: DataValidationResult


class DataTableManager:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.settings.data_sources_path.mkdir(parents=True, exist_ok=True)
        self.settings.unity_exports_path.mkdir(parents=True, exist_ok=True)

    def list_tables(self) -> list[dict[str, str | int]]:
        tables = []
        for path in sorted(self.settings.data_sources_path.glob("*.csv")):
            if path.is_symlink():
                continue
            rows = self._count_rows(path)
            tables.append({"name": path.name, "path": str(path), "rows": rows})
        return tables

    def load(self, name: str) -> DataTable:
        path = self.validate_table_name(name, must_exist=True)
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = list(reader.fieldnames or [])
            rows = [{header: row.get(header, "") or "" for header in headers} for row in reader]
        validation = self.validate(headers, rows)
        return DataTable(name=path.name, path=path, headers=headers, rows=rows, validation=validation)

    def save(self, name: str, headers: list[str], rows: list[dict[str, str]]) -> DataTable:
        path = self.validate_table_name(name, must_exist=False)
        clean_headers = self._clean_headers(headers)
        clean_rows = self._clean_rows(clean_headers, rows)
        validation = self.validate(clean_headers, clean_rows)
        if validation.errors:
            raise ValueError("; ".join(validation.errors))
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=clean_headers)
            writer.writeheader()
            writer.writerows(clean_rows)
        return self.load(path.name)

    def export_unity_json(self, name: str) -> Path:
        table = self.load(name)
        if table.validation.errors:
            raise ValueError("; ".join(table.validation.errors))
        payload = {
            "table": Path(table.name).stem,
            "source": table.name,
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "items": [self._unity_row(row) for row in table.rows],
        }
        export_path = self.settings.unity_exports_path / f"{Path(table.name).stem}.json"
        self._validate_export_path(export_path)
        export_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return export_path

    def validate(self, headers: list[str], rows: list[dict[str, str]]) -> DataValidationResult:
        result = DataValidationResult()
        if not headers:
            result.errors.append("CSV header가 없습니다.")
            return result
        duplicated_headers = self._duplicates(headers)
        if duplicated_headers:
            result.errors.append(f"중복 header: {', '.join(duplicated_headers)}")
        if "id" in headers:
            ids = [row.get("id", "").strip() for row in rows]
            blank_count = sum(1 for value in ids if not value)
            duplicated_ids = self._duplicates([value for value in ids if value])
            if blank_count:
                result.errors.append(f"id가 비어 있는 행: {blank_count}개")
            if duplicated_ids:
                result.errors.append(f"중복 id: {', '.join(duplicated_ids)}")
        else:
            result.warnings.append("Unity export 안정성을 위해 id 컬럼을 권장합니다.")

        for row_index, row in enumerate(rows, start=1):
            for header in headers:
                value = row.get(header, "")
                if header.endswith(("_id", "Id", "ID")) and not value.strip():
                    result.warnings.append(f"{row_index}행 {header} 값이 비어 있습니다.")
        return result

    def validate_table_name(self, name: str, must_exist: bool) -> Path:
        candidate = Path(name)
        if candidate.is_absolute():
            raise ValueError(f"절대 경로는 사용할 수 없습니다: {name}")
        if ".." in candidate.parts:
            raise ValueError(f"상위 경로 이동은 사용할 수 없습니다: {name}")
        if candidate.name != name:
            raise ValueError(f"파일명만 사용할 수 있습니다: {name}")
        if candidate.suffix.lower() != ".csv":
            raise ValueError(f"CSV 파일만 사용할 수 있습니다: {name}")
        path = (self.settings.data_sources_path / candidate.name).resolve()
        root = self.settings.data_sources_path.resolve()
        if not (path == root or root in path.parents):
            raise ValueError(f"data_sources 밖의 파일은 사용할 수 없습니다: {name}")
        if path.exists() and path.is_symlink():
            raise ValueError(f"symlink CSV는 사용할 수 없습니다: {name}")
        if must_exist and not path.exists():
            raise FileNotFoundError(f"CSV를 찾을 수 없습니다: {name}")
        return path

    def _validate_export_path(self, path: Path) -> None:
        root = self.settings.unity_exports_path.resolve()
        candidate = path.resolve()
        if candidate.suffix.lower() != ".json":
            raise ValueError("Unity export는 JSON 파일만 허용합니다.")
        if not (candidate == root or root in candidate.parents):
            raise ValueError("Unity export 경로가 허용 범위를 벗어났습니다.")
        if candidate.exists() and candidate.is_symlink():
            raise ValueError("symlink export 파일은 사용할 수 없습니다.")

    def _count_rows(self, path: Path) -> int:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            next(reader, None)
            return sum(1 for _ in reader)

    def _clean_headers(self, headers: list[str]) -> list[str]:
        return [header.strip() for header in headers if header.strip()]

    def _clean_rows(self, headers: list[str], rows: list[dict[str, str]]) -> list[dict[str, str]]:
        clean_rows = []
        for row in rows:
            clean = {header: str(row.get(header, "")).strip() for header in headers}
            if any(value for value in clean.values()):
                clean_rows.append(clean)
        return clean_rows

    def _unity_row(self, row: dict[str, str]) -> dict[str, Any]:
        return {key: self._infer_value(value) for key, value in row.items()}

    def _infer_value(self, value: str) -> Any:
        text = value.strip()
        if text == "":
            return ""
        lowered = text.lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
        if "|" in text:
            return [self._infer_value(part) for part in text.split("|")]
        try:
            if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
                return int(text)
            return float(text)
        except ValueError:
            return text

    def _duplicates(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        duplicated: list[str] = []
        for value in values:
            if value in seen and value not in duplicated:
                duplicated.append(value)
            seen.add(value)
        return duplicated
