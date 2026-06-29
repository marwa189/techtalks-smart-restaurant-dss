from collections import defaultdict
from typing import Any

from app.schemas import (
    HighWasteLowSalesItem,
    MenuItemMetric,
    SalesTrendPoint,
    SummaryMetrics,
    WasteMetric,
)
from app.services.dataset_service import dataset_store


class AnalyticsService:
    def summary(self) -> SummaryMetrics:
        rows = self._valid_rows()
        return SummaryMetrics(
            total_records=len(rows),
            total_quantity_sold=sum(int(row["quantity_sold"]) for row in rows),
            total_revenue=round(sum(self._revenue(row) for row in rows), 2),
            total_waste_quantity=round(sum(float(row["waste_quantity"]) for row in rows), 2),
            average_waste_ratio=round(self._average([float(row["waste_ratio"]) for row in rows]), 4),
            unique_menu_items=len({str(row["menu_item_name"]) for row in rows}),
        )

    def sales_trends(self, group_by: str) -> list[SalesTrendPoint]:
        grouped: dict[str, dict[str, float]] = defaultdict(
            lambda: {"quantity_sold": 0, "revenue": 0.0, "waste_quantity": 0.0}
        )
        for row in self._valid_rows():
            record_date = row["date"]
            period = record_date.strftime("%Y-%m") if group_by == "month" else record_date.isoformat()
            grouped[period]["quantity_sold"] += int(row["quantity_sold"])
            grouped[period]["revenue"] += self._revenue(row)
            grouped[period]["waste_quantity"] += float(row["waste_quantity"])

        return [
            SalesTrendPoint(
                period=period,
                quantity_sold=int(values["quantity_sold"]),
                revenue=round(values["revenue"], 2),
                waste_quantity=round(values["waste_quantity"], 2),
            )
            for period, values in sorted(grouped.items())
        ]

    def top_menu_items(self, limit: int) -> list[MenuItemMetric]:
        return [
            MenuItemMetric(
                menu_item_name=str(row["menu_item_name"]),
                quantity_sold=int(row["quantity_sold"]),
                revenue=round(float(row["revenue"]), 2),
                waste_quantity=round(float(row["waste_quantity"]), 2),
                average_waste_ratio=round(float(row["average_waste_ratio"]), 4),
            )
            for row in self.menu_metric_rows(sort_key="revenue", limit=limit)
        ]

    def menu_item_waste(self, limit: int) -> list[WasteMetric]:
        return [
            WasteMetric(
                name=str(row["menu_item_name"]),
                waste_quantity=round(float(row["waste_quantity"]), 2),
                waste_cost=round(float(row["waste_cost"]), 2),
                average_waste_ratio=round(float(row["average_waste_ratio"]), 4),
            )
            for row in self.menu_metric_rows(sort_key="waste_quantity", limit=limit)
        ]

    def estimated_inventory_waste(self, limit: int) -> list[WasteMetric]:
        # Temporary API contract until MenuIngredient mapping is added.
        # Later: estimated_item_waste = menu_waste * quantity_required.
        return self.menu_item_waste(limit=limit)

    def high_waste_low_sales(self, limit: int) -> list[HighWasteLowSalesItem]:
        metric_rows = self.menu_metric_rows(sort_key="waste_quantity", limit=10_000)
        if not metric_rows:
            return []

        average_quantity_sold = self._average([float(row["quantity_sold"]) for row in metric_rows])
        average_waste_ratio = self._average([float(row["average_waste_ratio"]) for row in metric_rows])

        flagged_rows = [
            row
            for row in metric_rows
            if float(row["quantity_sold"]) < average_quantity_sold
            and float(row["average_waste_ratio"]) > average_waste_ratio
        ]
        flagged_rows.sort(
            key=lambda row: (float(row["average_waste_ratio"]), float(row["waste_quantity"])),
            reverse=True,
        )

        return [
            HighWasteLowSalesItem(
                menu_item_name=str(row["menu_item_name"]),
                quantity_sold=int(row["quantity_sold"]),
                revenue=round(float(row["revenue"]), 2),
                waste_quantity=round(float(row["waste_quantity"]), 2),
                average_waste_ratio=round(float(row["average_waste_ratio"]), 4),
                reason="Below-average sales with above-average waste ratio.",
            )
            for row in flagged_rows[:limit]
        ]

    def menu_metric_rows(self, sort_key: str, limit: int) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        ratios: dict[str, list[float]] = defaultdict(list)

        for row in self._valid_rows():
            name = str(row["menu_item_name"])
            grouped.setdefault(
                name,
                {
                    "menu_item_name": name,
                    "quantity_sold": 0,
                    "revenue": 0.0,
                    "waste_quantity": 0.0,
                    "waste_cost": 0.0,
                },
            )
            grouped[name]["quantity_sold"] += int(row["quantity_sold"])
            grouped[name]["revenue"] += self._revenue(row)
            grouped[name]["waste_quantity"] += float(row["waste_quantity"])
            grouped[name]["waste_cost"] += self._waste_cost(row)
            ratios[name].append(float(row["waste_ratio"]))

        results = []
        for name, values in grouped.items():
            values["average_waste_ratio"] = self._average(ratios[name])
            results.append(values)
        return sorted(results, key=lambda row: row[sort_key], reverse=True)[:limit]

    def _valid_rows(self) -> list[dict[str, Any]]:
        return [
            row
            for row in dataset_store.rows()
            if row.get("date") is not None and row.get("restaurant_type") != "restaurant_type"
        ]

    def _revenue(self, row: dict[str, Any]) -> float:
        return float(row["quantity_sold"]) * float(row["actual_selling_price"])

    def _waste_cost(self, row: dict[str, Any]) -> float:
        return float(row["waste_quantity"]) * float(row["typical_ingredient_cost"])

    def _average(self, values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0


analytics_service = AnalyticsService()
