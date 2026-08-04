# =============================================================================
# app/services/recommendation_service.py
# Smart Restaurant DSS — ML-Powered Recommendation Service
# =============================================================================
#
# WHAT THIS FILE DOES:
# --------------------
# Replaces the moving average baseline and simple waste-cost logic with the
# actual trained Random Forest model from inference_pipeline.py
#
# Keeps the EXACT same method signatures and return schemas so the router
# and the rest of the backend app require zero changes.
#
# Two methods:
#   simple_forecast()          → /forecast/menu-items
#   generate_recommendations() → /recommendations
# =============================================================================

from collections import defaultdict
from datetime import date, timedelta

# --- Import the ML pipeline ---
# inference_pipeline.py must be in the same directory or on the Python path
try:
    from inference_pipeline import predict_all_dishes, label_encoders
    ML_AVAILABLE = True
except Exception as e:
    ML_AVAILABLE = False
    ML_ERROR = str(e)

from app.schemas import ForecastPoint, Recommendation
from app.services.analytics_service import analytics_service


# Mapping from our ML urgency to their severity scale
URGENCY_TO_SEVERITY = {
    "HIGH"  : "High",
    "MEDIUM": "Medium",
    "LOW"   : "Low",
}

# Default conditions used when no specific conditions are passed
# These represent a typical operating day at the Food Stall
DEFAULT_CONDITIONS = {
    "date"                 : date.today().isoformat(),
    "meal_type"            : "Lunch",
    "weather_condition"    : "Sunny",
    "actual_selling_price" : 8.50,
    "quantity_sold"        : 100,
    "has_promotion"        : False,
    "special_event"        : False,
}


class RecommendationService:

    # -------------------------------------------------------------------------
    # /forecast/menu-items
    # -------------------------------------------------------------------------
    # Previously used a moving average baseline.
    # Now uses the Random Forest model to predict waste ratio per dish,
    # then calculates recommended prep quantity as the forecast.
    #
    # Falls back to moving average if the ML model is unavailable.
    # -------------------------------------------------------------------------

    def simple_forecast(self, days: int, limit: int) -> list[ForecastPoint]:

        if not ML_AVAILABLE:
            # Fallback to original moving average logic
            return self._moving_average_forecast(days=days, limit=limit)

        forecasts: list[ForecastPoint] = []

        try:
            # Get all known menu items from the label encoder
            menu_items = sorted(
                label_encoders['menu_item_name'].classes_.tolist()
            )[:limit]

            # Generate forecasts for each day in the requested range
            for offset in range(1, days + 1):
                forecast_date = date.today() + timedelta(days=offset)

                conditions = {
                    **DEFAULT_CONDITIONS,
                    "date": forecast_date.isoformat(),
                }

                # Run batch prediction for all dishes on this date
                results = predict_all_dishes(
                    base_input  = conditions,
                    menu_items  = menu_items
                )

                for result in results:
                    if 'error' not in result:
                        forecasts.append(
                            ForecastPoint(
                                menu_item_name         = result["menu_item_name"],
                                forecast_date          = forecast_date.isoformat(),
                                predicted_quantity_sold= result["adjusted_prep"],
                                model_name             = "random_forest_waste_model",
                            )
                        )

            return forecasts

        except Exception:
            # If ML prediction fails for any reason, fall back gracefully
            return self._moving_average_forecast(days=days, limit=limit)


    # -------------------------------------------------------------------------
    # /recommendations
    # -------------------------------------------------------------------------
    # Previously used waste cost thresholds to generate generic text.
    # Now uses the Random Forest model to generate dish-specific
    # recommendations with contextual plain-English reasons.
    #
    # Falls back to original waste-cost logic if ML model is unavailable.
    # -------------------------------------------------------------------------

    def generate_recommendations(self, limit: int) -> list[Recommendation]:

        if not ML_AVAILABLE:
            # Fallback to original waste-cost logic
            return self._waste_cost_recommendations(limit=limit)

        try:
            # Run batch prediction for today's conditions
            results = predict_all_dishes(
                base_input = DEFAULT_CONDITIONS,
                menu_items = None  # predict for all known dishes
            )

            recommendations: list[Recommendation] = []

            for result in results[:limit]:
                if 'error' in result:
                    continue

                action   = result["action"]
                urgency  = result["urgency"]
                severity = URGENCY_TO_SEVERITY.get(urgency, "Low")

                # Build recommendation text based on action
                if action == "DECREASE":
                    rec_text = (
                        f"Decrease tomorrow's prep for {result['menu_item_name']} "
                        f"by {result['change_amount']} portions. "
                        f"Recommended quantity: {result['adjusted_prep']} portions."
                    )
                elif action == "INCREASE":
                    rec_text = (
                        f"Increase tomorrow's prep for {result['menu_item_name']} "
                        f"by {result['change_amount']} portions. "
                        f"Recommended quantity: {result['adjusted_prep']} portions."
                    )
                else:
                    rec_text = (
                        f"Maintain current prep quantity for {result['menu_item_name']}. "
                        f"Prepare {result['adjusted_prep']} portions tomorrow."
                    )

                recommendations.append(
                    Recommendation(
                        target_type        = "MenuItem",
                        target_name        = result["menu_item_name"],
                        severity           = severity,
                        recommendation_text= rec_text,
                        reason             = result["reason"],
                    )
                )

            return recommendations

        except Exception:
            # If ML prediction fails, fall back gracefully
            return self._waste_cost_recommendations(limit=limit)


    # -------------------------------------------------------------------------
    # FALLBACK METHODS
    # These are the original implementations kept as safety nets.
    # They run automatically if the ML model files are missing or broken.
    # -------------------------------------------------------------------------

    def _moving_average_forecast(
        self, days: int, limit: int
    ) -> list[ForecastPoint]:
        """Original moving average baseline — fallback only."""
        rows = analytics_service.daily_quantity_rows()
        latest_date = analytics_service.latest_sales_date()
        if not rows or latest_date is None:
            return []

        daily_quantities: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        for row in rows:
            menu_item = str(row["menu_item_name"])
            daily_quantities[menu_item][row["sales_date"].isoformat()] += int(
                row["quantity_sold"]
            )

        averages = []
        for menu_item, by_day in daily_quantities.items():
            averages.append(
                (menu_item, sum(by_day.values()) / len(by_day))
            )
        averages.sort(key=lambda item: item[1], reverse=True)

        forecasts: list[ForecastPoint] = []
        for offset in range(1, days + 1):
            forecast_date = latest_date + timedelta(days=offset)
            for menu_item, average_quantity in averages[:limit]:
                forecasts.append(
                    ForecastPoint(
                        menu_item_name          = menu_item,
                        forecast_date           = forecast_date.isoformat(),
                        predicted_quantity_sold = max(0, int(round(average_quantity))),
                        model_name              = "moving_average_baseline",
                    )
                )
        return forecasts


    def _waste_cost_recommendations(self, limit: int) -> list[Recommendation]:
        """Original waste-cost logic — fallback only."""
        waste_metrics = analytics_service.menu_metric_rows(
            sort_key="waste_cost", limit=limit
        )
        recommendations: list[Recommendation] = []
        for metric in waste_metrics:
            waste_cost = float(metric["waste_cost"])
            name       = str(metric["menu_item_name"])
            recommendations.append(
                Recommendation(
                    target_type         = "MenuItem",
                    target_name         = name,
                    severity            = self._severity(waste_cost),
                    recommendation_text = (
                        f"Review preparation quantity for {name}."
                    ),
                    reason              = (
                        f"{name} has total waste of "
                        f"{round(float(metric['waste_quantity']), 2)} "
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
