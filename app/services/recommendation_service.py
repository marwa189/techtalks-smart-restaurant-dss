from collections import defaultdict
from datetime import timedelta

from app.schemas import ForecastPoint, Recommendation
from app.services.analytics_service import analytics_service


class RecommendationService:
    def simple_forecast(self, days: int, limit: int) -> list[ForecastPoint]:
        rows = analytics_service.daily_quantity_rows()
        latest_date = analytics_service.latest_sales_date()
        if not rows or latest_date is None:
            return []

        daily_quantities: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for row in rows:
            menu_item = str(row["menu_item_name"])
            daily_quantities[menu_item][row["sales_date"].isoformat()] += int(row["quantity_sold"])

        averages = []
        for menu_item, by_day in daily_quantities.items():
            averages.append((menu_item, sum(by_day.values()) / len(by_day)))
        averages.sort(key=lambda item: item[1], reverse=True)

        forecasts: list[ForecastPoint] = []
        for offset in range(1, days + 1):
            forecast_date = latest_date + timedelta(days=offset)
            for menu_item, average_quantity in averages[:limit]:
                forecasts.append(
                    ForecastPoint(
                        menu_item_name=menu_item,
                        forecast_date=forecast_date.isoformat(),
                        predicted_quantity_sold=max(0, int(round(average_quantity))),
                        model_name="moving_average_baseline",
                    )
                )
        return forecasts

    def generate_recommendations(self, limit: int) -> list[Recommendation]:
        waste_metrics = analytics_service.menu_metric_rows(sort_key="waste_cost", limit=limit)
        recommendations: list[Recommendation] = []
        for metric in waste_metrics:
            waste_cost = float(metric["waste_cost"])
            name = str(metric["menu_item_name"])
            recommendations.append(
                Recommendation(
                    target_type="MenuItem",
                    target_name=name,
                    severity=self._severity(waste_cost),
                    recommendation_text=f"Review preparation quantity for {name}.",
                    reason=(
                        f"{name} has total waste of {round(float(metric['waste_quantity']), 2)} "
                        f"and estimated waste cost of {round(waste_cost, 2)}."
                    ),
                )
            )
        return recommendations

    def _severity(self, waste_cost: float) -> str:
        if waste_cost >= 50000:
            return "High"
        if waste_cost >= 20000:
            return "Medium"
        return "Low"


recommendation_service = RecommendationService()
