const API_BASE_URL = "http://localhost:8000";

export type DashboardSummary = {
  total_records: number;
  total_quantity_sold: number;
  total_revenue: number;
  total_waste_quantity: number;
  average_waste_ratio: number;
  unique_menu_items: number;
};

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await fetch(`${API_BASE_URL}/analytics/summary`);

  if (!response.ok) {
    throw new Error("Failed to fetch dashboard summary");
  }

  console.log("Dashboard summary fetched successfully");
  return response.json();
}
