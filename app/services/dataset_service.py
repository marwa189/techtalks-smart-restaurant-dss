import csv
from datetime import date, datetime
from io import StringIO
from pathlib import Path
from typing import Any

from app.schemas import DatasetProfile


REQUIRED_COLUMNS = {
    "date",
    "restaurant_type",
    "menu_item_name",
    "meal_type",
    "weather_condition",
    "typical_ingredient_cost",
    "actual_selling_price",
    "quantity_sold",
    "has_promotion",
    "special_event",
    "waste_quantity",
    "waste_ratio",
}


class DatasetStore:
    def __init__(self) -> None:
        self._rows: list[dict[str, Any]] | None = None
        self._columns: list[str] = []
        self._source_name = "not loaded"

    def load_csv(self, content: bytes, source_name: str) -> DatasetProfile:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("Could not decode file as UTF-8 CSV data.") from exc

        rows, columns = self._parse_csv(text)
        return self._set_rows(rows=rows, columns=columns, source_name=source_name)

    def load_sample(self) -> DatasetProfile:
        candidates = [
            Path("data/restaurant_sales_with_waste.csv"),
            Path("data/restaurant_sales_with_waste.csv.xls"),
            Path.home() / "Downloads" / "restaurant_sales_with_waste.csv.xls",
        ]
        for candidate in candidates:
            if candidate.exists():
                rows, columns = self._parse_csv(candidate.read_text(encoding="utf-8-sig"))
                return self._set_rows(rows=rows, columns=columns, source_name=str(candidate))
        raise FileNotFoundError("No sample dataset found.")

    def rows(self) -> list[dict[str, Any]]:
        if self._rows is None:
            self.load_sample()
        return list(self._rows or [])

    def profile(self) -> DatasetProfile:
        if self._rows is None:
            self.load_sample()
        return self._build_profile(self.rows(), source_name=self._source_name)

    def _parse_csv(self, text: str) -> tuple[list[dict[str, str]], list[str]]:
        reader = csv.DictReader(StringIO(text))
        if reader.fieldnames is None:
            raise ValueError("CSV file must include a header row.")

        columns = [field.strip().lower() for field in reader.fieldnames]
        rows: list[dict[str, str]] = []
        for raw_row in reader:
            values = list(raw_row.values())
            row = {columns[index]: (value or "").strip() for index, value in enumerate(values)}
            rows.append(row)
        return rows, columns

    def _set_rows(
        self,
        rows: list[dict[str, str]],
        columns: list[str],
        source_name: str,
    ) -> DatasetProfile:
        missing_columns = sorted(REQUIRED_COLUMNS - set(columns))
        if missing_columns:
            raise ValueError(f"Dataset is missing required columns: {', '.join(missing_columns)}")

        self._rows = [self._coerce_row(row) for row in rows]
        self._columns = columns
        self._source_name = source_name
        return self._build_profile(self._rows, source_name=source_name)

    def _coerce_row(self, row: dict[str, str]) -> dict[str, Any]:
        coerced: dict[str, Any] = dict(row)
        coerced["date"] = self._parse_date(row.get("date", ""))
        coerced["typical_ingredient_cost"] = self._parse_float(row.get("typical_ingredient_cost", "0"))
        coerced["actual_selling_price"] = self._parse_float(row.get("actual_selling_price", "0"))
        coerced["quantity_sold"] = int(self._parse_float(row.get("quantity_sold", "0")))
        coerced["waste_quantity"] = int(self._parse_float(row.get("waste_quantity", "0")))
        coerced["waste_ratio"] = self._parse_float(row.get("waste_ratio", "0"))
        coerced["has_promotion"] = row.get("has_promotion", "").strip().lower() == "true"
        coerced["special_event"] = row.get("special_event", "").strip().lower() == "true"
        return coerced

    def _parse_date(self, value: str) -> date | None:
        for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    def _parse_float(self, value: str) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _build_profile(self, rows: list[dict[str, Any]], source_name: str) -> DatasetProfile:
        row_signatures = [tuple(sorted(row.items())) for row in rows]
        duplicate_rows = len(row_signatures) - len(set(row_signatures))
        valid_dates = [row["date"] for row in rows if row.get("date")]

        quality_issues: list[str] = []
        if duplicate_rows:
            quality_issues.append(f"{duplicate_rows} duplicate rows detected.")

        invalid_dates = sum(1 for row in rows if row.get("date") is None)
        if invalid_dates:
            quality_issues.append(f"{invalid_dates} rows have invalid dates.")

        invalid_restaurant_type = sum(
            1 for row in rows if row.get("restaurant_type") == "restaurant_type"
        )
        if invalid_restaurant_type:
            quality_issues.append(
                f"{invalid_restaurant_type} row has an invalid restaurant_type value."
            )

        return DatasetProfile(
            source_name=source_name,
            rows=len(rows),
            columns=self._columns,
            date_min=min(valid_dates).isoformat() if valid_dates else None,
            date_max=max(valid_dates).isoformat() if valid_dates else None,
            duplicate_rows=duplicate_rows,
            quality_issues=quality_issues,
        )


dataset_store = DatasetStore()
