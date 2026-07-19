from datetime import date
from typing import Any

from sqlalchemy import text

from app.database import engine
from app.schemas import (
    HighWasteLowSalesItem,
    MenuItemMetric,
    SalesTrendPoint,
    SummaryMetrics,
    WasteMetric,
)


class AnalyticsService:
    def summary(self) -> SummaryMetrics:
        query = text(
            """
            SELECT
                (SELECT COUNT(*) FROM sales_record_table) AS total_records,
                COALESCE((SELECT SUM(quantity_sold) FROM sales_record_table), 0) AS total_quantity_sold,
                COALESCE((SELECT SUM(quantity_sold * actual_selling_price) FROM sales_record_table), 0) AS total_revenue,
                COALESCE((SELECT SUM(waste_quantity) FROM waste_record_table), 0) AS total_waste_quantity,
                COALESCE((SELECT AVG(waste_ratio) FROM waste_record_table), 0) AS average_waste_ratio,
                (SELECT COUNT(*) FROM menu_table) AS unique_menu_items
            """
        )
        row = self._fetch_one(query)
        return SummaryMetrics(
            total_records=int(row["total_records"]),
            total_quantity_sold=int(row["total_quantity_sold"]),
            total_revenue=round(float(row["total_revenue"]), 2),
            total_waste_quantity=round(float(row["total_waste_quantity"]), 2),
            average_waste_ratio=round(float(row["average_waste_ratio"]), 4),
            unique_menu_items=int(row["unique_menu_items"]),
        )

    def sales_trends(self, group_by: str) -> list[SalesTrendPoint]:
        date_expression = (
            "DATE_FORMAT(sales_date, '%Y-%m')" if group_by == "month" else "sales_date"
        )
        query = text(
            f"""
            SELECT
                sales_metrics.period,
                sales_metrics.quantity_sold,
                sales_metrics.revenue,
                COALESCE(waste_metrics.waste_quantity, 0) AS waste_quantity
            FROM (
                SELECT
                    {date_expression} AS period,
                    COALESCE(SUM(quantity_sold), 0) AS quantity_sold,
                    COALESCE(SUM(quantity_sold * actual_selling_price), 0) AS revenue
                FROM sales_record_table
                GROUP BY {date_expression}
            ) AS sales_metrics
            LEFT JOIN (
                SELECT
                    {"DATE_FORMAT(waste_date, '%Y-%m')" if group_by == "month" else "waste_date"} AS period,
                    COALESCE(SUM(waste_quantity), 0) AS waste_quantity
                FROM waste_record_table
                GROUP BY {"DATE_FORMAT(waste_date, '%Y-%m')" if group_by == "month" else "waste_date"}
            ) AS waste_metrics
                ON sales_metrics.period = waste_metrics.period
            ORDER BY sales_metrics.period
            """
        )
        return [
            SalesTrendPoint(
                period=self._period_to_string(row["period"]),
                quantity_sold=int(row["quantity_sold"]),
                revenue=round(float(row["revenue"]), 2),
                waste_quantity=round(float(row["waste_quantity"]), 2),
            )
            for row in self._fetch_all(query)
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
        allowed_sort_keys = {
            "quantity_sold": "quantity_sold",
            "revenue": "revenue",
            "waste_quantity": "waste_quantity",
            "waste_cost": "waste_cost",
            "average_waste_ratio": "average_waste_ratio",
        }
        order_column = allowed_sort_keys.get(sort_key, "revenue")
        query = text(
            f"""
            SELECT
                menu.menu_item_name,
                COALESCE(sales.quantity_sold, 0) AS quantity_sold,
                COALESCE(sales.revenue, 0) AS revenue,
                COALESCE(waste.waste_quantity, 0) AS waste_quantity,
                COALESCE(waste.waste_quantity * menu.typical_ingredient_cost, 0) AS waste_cost,
                COALESCE(waste.average_waste_ratio, 0) AS average_waste_ratio
            FROM menu_table AS menu
            LEFT JOIN (
                SELECT
                    MenuID,
                    SUM(quantity_sold) AS quantity_sold,
                    SUM(quantity_sold * actual_selling_price) AS revenue
                FROM sales_record_table
                GROUP BY MenuID
            ) AS sales
                ON menu.MenuID = sales.MenuID
            LEFT JOIN (
                SELECT
                    MenuID,
                    SUM(waste_quantity) AS waste_quantity,
                    AVG(waste_ratio) AS average_waste_ratio
                FROM waste_record_table
                GROUP BY MenuID
            ) AS waste
                ON menu.MenuID = waste.MenuID
            ORDER BY {order_column} DESC
            LIMIT :limit
            """
        )
        return self._fetch_all(query, {"limit": limit})

    def _average(self, values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    def daily_quantity_rows(self) -> list[dict[str, Any]]:
        query = text(
            """
            SELECT
                menu.menu_item_name,
                sales.sales_date,
                SUM(sales.quantity_sold) AS quantity_sold
            FROM sales_record_table AS sales
            JOIN menu_table AS menu
                ON sales.MenuID = menu.MenuID
            GROUP BY menu.menu_item_name, sales.sales_date
            ORDER BY sales.sales_date, menu.menu_item_name
            """
        )
        return self._fetch_all(query)

    def latest_sales_date(self) -> date | None:
        query = text("SELECT MAX(sales_date) AS latest_date FROM sales_record_table")
        row = self._fetch_one(query)
        return row["latest_date"]

    def _fetch_all(
        self, query: Any, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        with engine.connect() as connection:
            return [dict(row) for row in connection.execute(query, params or {}).mappings()]

    def _fetch_one(
        self, query: Any, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        with engine.connect() as connection:
            row = connection.execute(query, params or {}).mappings().first()
            return dict(row) if row else {}

    def _period_to_string(self, period: Any) -> str:
        if hasattr(period, "isoformat"):
            return period.isoformat()
        return str(period)


analytics_service = AnalyticsService()
