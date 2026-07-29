from fastapi import APIRouter, Query

from app.schemas import (
    HighWasteLowSalesItem,
    MenuItemMetric,
    SalesTrendPoint,
    SummaryMetrics,
    WasteMetric,
)
from app.services.analytics_service import analytics_service


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=SummaryMetrics)
def get_summary() -> SummaryMetrics:
    return analytics_service.summary()


@router.get("/sales-trends", response_model=list[SalesTrendPoint])
def get_sales_trends(
    group_by: str = Query("date", pattern="^(date|month)$"),
) -> list[SalesTrendPoint]:
    return analytics_service.sales_trends(group_by=group_by)


@router.get("/top-menu-items", response_model=list[MenuItemMetric])
def get_top_menu_items(limit: int = Query(10, ge=1, le=50)) -> list[MenuItemMetric]:
    return analytics_service.top_menu_items(limit=limit)


@router.get("/waste/menu-items", response_model=list[WasteMetric])
def get_menu_item_waste(limit: int = Query(10, ge=1, le=50)) -> list[WasteMetric]:
    return analytics_service.menu_item_waste(limit=limit)


@router.get("/waste/inventory-estimate", response_model=list[WasteMetric])
def get_estimated_inventory_waste(limit: int = Query(10, ge=1, le=50)) -> list[WasteMetric]:
    return analytics_service.estimated_inventory_waste(limit=limit)


@router.get("/high-waste-low-sales", response_model=list[HighWasteLowSalesItem])
def get_high_waste_low_sales(limit: int = Query(10, ge=1, le=50)) -> list[HighWasteLowSalesItem]:
    return analytics_service.high_waste_low_sales(limit=limit)
