from fastapi import APIRouter, Query

from app.schemas import ForecastPoint, Recommendation
from app.services.recommendation_service import recommendation_service


router = APIRouter(tags=["AI Outputs"])


@router.get("/forecast/menu-items", response_model=list[ForecastPoint])
def forecast_menu_items(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
) -> list[ForecastPoint]:
    return recommendation_service.simple_forecast(days=days, limit=limit)


@router.get("/recommendations", response_model=list[Recommendation])
def get_recommendations(limit: int = Query(10, ge=1, le=50)) -> list[Recommendation]:
    return recommendation_service.generate_recommendations(limit=limit)
