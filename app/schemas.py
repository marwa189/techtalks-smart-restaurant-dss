from pydantic import BaseModel, Field


class DatasetProfile(BaseModel):
    source_name: str
    rows: int
    columns: list[str]
    date_min: str | None = None
    date_max: str | None = None
    duplicate_rows: int
    quality_issues: list[str] = Field(default_factory=list)


class SummaryMetrics(BaseModel):
    total_records: int
    total_quantity_sold: int
    total_revenue: float
    total_waste_quantity: float
    average_waste_ratio: float
    unique_menu_items: int


class SalesTrendPoint(BaseModel):
    period: str
    quantity_sold: int
    revenue: float
    waste_quantity: float


class MenuItemMetric(BaseModel):
    menu_item_name: str
    quantity_sold: int
    revenue: float
    waste_quantity: float
    average_waste_ratio: float


class WasteMetric(BaseModel):
    name: str
    waste_quantity: float
    waste_cost: float
    average_waste_ratio: float | None = None


class HighWasteLowSalesItem(BaseModel):
    menu_item_name: str
    quantity_sold: int
    revenue: float
    waste_quantity: float
    average_waste_ratio: float
    reason: str


class ForecastPoint(BaseModel):
    menu_item_name: str
    forecast_date: str
    predicted_quantity_sold: int
    model_name: str


class Recommendation(BaseModel):
    target_type: str
    target_name: str
    severity: str
    recommendation_text: str
    reason: str
