const API_BASE_URL = "http://localhost:8000";

export type DashboardSummary = {
  total_records: number;
  total_quantity_sold: number;
  total_revenue: number;
  total_waste_quantity: number;
  average_waste_ratio: number;
  unique_menu_items: number;
};

export type SalesTrendPoint = {
  period: string;
  quantity_sold: number;
  revenue: number;
  waste_quantity: number;
};

export type MenuItemMetric = {
  menu_item_name: string;
  quantity_sold: number;
  revenue: number;
  waste_quantity: number;
  average_waste_ratio: number;
};

export type WasteMetric = {
  name: string;
  waste_quantity: number;
  waste_cost: number;
  average_waste_ratio: number | null;
};

export type HighWasteLowSalesItem = {
  menu_item_name: string;
  quantity_sold: number;
  revenue: number;
  waste_quantity: number;
  average_waste_ratio: number;
  reason: string;
};

export type ForecastPoint = {
  menu_item_name: string;
  forecast_date: string;
  predicted_quantity_sold: number;
  model_name: string;
};

export type Recommendation = {
  target_type: string;
  target_name: string;
  severity: string;
  recommendation_text: string;
  reason: string;
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch ${path}`);
  }

  return response.json();
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return getJson<DashboardSummary>("/analytics/summary");
}

export async function getSalesTrends(): Promise<SalesTrendPoint[]> {
  return getJson<SalesTrendPoint[]>("/analytics/sales-trends");
}

export async function getTopMenuItems(): Promise<MenuItemMetric[]> {
  return getJson<MenuItemMetric[]>("/analytics/top-menu-items?limit=10");
}

export async function getMenuItemWaste(): Promise<WasteMetric[]> {
  return getJson<WasteMetric[]>("/analytics/waste/menu-items?limit=10");
}

export async function getHighWasteLowSales(): Promise<HighWasteLowSalesItem[]> {
  return getJson<HighWasteLowSalesItem[]>("/analytics/high-waste-low-sales");
}

export async function getForecastMenuItems(): Promise<ForecastPoint[]> {
  return getJson<ForecastPoint[]>("/forecast/menu-items?days=7&limit=10");
}

export async function getRecommendations(): Promise<Recommendation[]> {
  return getJson<Recommendation[]>("/recommendations?limit=10");
}
