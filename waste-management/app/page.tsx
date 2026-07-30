"use client";
import { useEffect, useState } from "react";
import {
  getDashboardSummary,
  getMenuItemWaste,
  getRecommendations,
  getSalesTrends,
  getTopMenuItems,
  type DashboardSummary,
  type MenuItemMetric,
  type Recommendation,
  type SalesTrendPoint,
  type WasteMetric,
} from "@/lib/api";
import {
  AlertTriangle,
  ArrowUpRight,
  BarChart3,
  ChevronRight,
  CircleDollarSign,
  Leaf,
  Sparkles,
  TrendingUp,
  UtensilsCrossed,
} from "lucide-react";
import { AppShell } from "./components/app-shell";

const metrics = [
  {
    title: "Total Records",
    value: "3,517",
    detail: "Operational entries tracked",
    icon: TrendingUp,
    tone: "bg-teal-50 text-teal-700",
  },
  {
    title: "Total Quantity Sold",
    value: "1,358,811",
    detail: "Units sold across the menu",
    icon: BarChart3,
    tone: "bg-emerald-50 text-emerald-700",
  },
  {
    title: "Total Revenue",
    value: "$9,816,537.23",
    detail: "Gross sales recorded",
    icon: CircleDollarSign,
    tone: "bg-amber-50 text-amber-700",
  },
  {
    title: "Total Waste Quantity",
    value: "92,173",
    detail: "Units discarded",
    icon: Leaf,
    tone: "bg-emerald-50 text-emerald-700",
  },
  {
    title: "Average Waste Ratio",
    value: "7.88%",
    detail: "Waste as a share of sales",
    icon: AlertTriangle,
    tone: "bg-sky-50 text-sky-700",
  },
  {
    title: "Unique Menu Items",
    value: "10",
    detail: "Distinct items tracked",
    icon: UtensilsCrossed,
    tone: "bg-teal-50 text-teal-700",
  },
];

const salesBars = [
  { label: "Mon", height: "42%" },
  { label: "Tue", height: "58%" },
  { label: "Wed", height: "70%" },
  { label: "Thu", height: "64%" },
  { label: "Fri", height: "88%" },
  { label: "Sat", height: "92%" },
  { label: "Sun", height: "75%" },
];

const topRevenueItems = [
  { name: "Tandoori Chicken", value: "$2,208,932.14" },
  { name: "Kaya Toast Set", value: "$2,204,396.22" },
  { name: "Cendol", value: "$946,290.17" },
];

const wasteItems = [
  { name: "Teh Tarik", value: "22,654 units" },
  { name: "Cendol", value: "17,750 units" },
  { name: "Roti Canai", value: "13,734 units" },
];

const inventoryRows = [
  {
    item: "Tandoori Chicken",
    sold: "91,048",
    revenue: "$2,208,932.14",
    waste: "8,840",
    ratio: "10.06%",
    action: "Optimize prep",
  },
  {
    item: "Kaya Toast Set",
    sold: "272,340",
    revenue: "$2,204,396.22",
    waste: "10,648",
    ratio: "4.02%",
    action: "Keep normal prep",
  },
  {
    item: "Cendol",
    sold: "152,651",
    revenue: "$946,290.17",
    waste: "17,750",
    ratio: "12.06%",
    action: "Reduce waste",
  },
  {
    item: "Teh Tarik",
    sold: "333,124",
    revenue: "$848,145.73",
    waste: "22,654",
    ratio: "7.00%",
    action: "Monitor waste",
  },
  {
    item: "Roti Canai",
    sold: "286,505",
    revenue: "$666,822.86",
    waste: "13,734",
    ratio: "5.01%",
    action: "Keep normal prep",
  },
];

export default function Home() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [salesTrends, setSalesTrends] = useState<SalesTrendPoint[]>([]);
  const [menuItems, setMenuItems] = useState<MenuItemMetric[]>([]);
  const [menuWaste, setMenuWaste] = useState<WasteMetric[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDashboardData() {
      try {
        const [summaryData, trendsData, menuData, wasteData, recommendationData] =
          await Promise.all([
            getDashboardSummary(),
            getSalesTrends(),
            getTopMenuItems(),
            getMenuItemWaste(),
            getRecommendations(),
          ]);

        setSummary(summaryData);
        setSalesTrends(trendsData);
        setMenuItems(menuData);
        setMenuWaste(wasteData);
        setRecommendations(recommendationData);
      } catch (err) {
        console.error("Dashboard data error:", err);
        setError("Could not load live dashboard data");
      } finally {
        setLoading(false);
      }
    }

    fetchDashboardData();
  }, []);

  const loadingValue = loading ? "Loading..." : "N/A";
  const formatNumber = (value: number | undefined) =>
    value === undefined ? loadingValue : value.toLocaleString();
  const formatCurrency = (value: number | undefined) =>
    value === undefined
      ? loadingValue
      : value.toLocaleString(undefined, {
          style: "currency",
          currency: "USD",
        });
  const formatPercent = (value: number | undefined) =>
    value === undefined ? loadingValue : `${(value * 100).toFixed(2)}%`;

  const liveTopRevenueItems =
    menuItems.length > 0
      ? menuItems.slice(0, 3).map((item) => ({
          name: item.menu_item_name,
          value: formatCurrency(item.revenue),
        }))
      : topRevenueItems;

  const liveWasteItems =
    menuWaste.length > 0
      ? menuWaste.slice(0, 3).map((item) => ({
          name: item.name,
          value: `${formatNumber(item.waste_quantity)} units`,
        }))
      : wasteItems;

  const maxTrendRevenue = Math.max(...salesTrends.slice(-7).map((point) => point.revenue), 1);
  const liveSalesBars =
    salesTrends.length > 0
      ? salesTrends.slice(-7).map((point) => ({
          label: new Date(point.period).toLocaleDateString(undefined, { weekday: "short" }),
          height: `${Math.max(10, Math.round((point.revenue / maxTrendRevenue) * 100))}%`,
        }))
      : salesBars;

  const liveInventoryRows =
    menuItems.length > 0
      ? menuItems.slice(0, 5).map((item) => ({
          item: item.menu_item_name,
          sold: formatNumber(item.quantity_sold),
          revenue: formatCurrency(item.revenue),
          waste: formatNumber(item.waste_quantity),
          ratio: formatPercent(item.average_waste_ratio),
          action:
            item.average_waste_ratio >= 0.1
              ? "Reduce waste"
              : item.average_waste_ratio >= 0.07
                ? "Monitor waste"
                : "Keep normal prep",
        }))
      : inventoryRows;

  const mainRecommendation = recommendations[0];

  const dashboardMetrics = metrics.map((metric) => {
    const values: Record<string, string> = {
      "Total Records": formatNumber(summary?.total_records),
      "Total Quantity Sold": formatNumber(summary?.total_quantity_sold),
      "Total Revenue": formatCurrency(summary?.total_revenue),
      "Total Waste Quantity": formatNumber(summary?.total_waste_quantity),
      "Average Waste Ratio": formatPercent(summary?.average_waste_ratio),
      "Unique Menu Items": formatNumber(summary?.unique_menu_items),
    };

    return {
      ...metric,
      value: values[metric.title] ?? metric.value,
    };
  });

  return (
    <AppShell
      title="SmartDine Dashboard"
      subtitle="Decision support"
      description="An operating view for sales, waste, and recommendation signals."
    >
      {error && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800">
          {error}. Showing fallback dashboard values.
        </div>
      )}

      <section className="rounded-[28px] bg-gradient-to-r from-teal-700 via-teal-600 to-emerald-500 p-5 text-white shadow-[0_20px_45px_rgba(15,118,110,0.18)] sm:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-xl">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-sm font-medium backdrop-blur">
              <Sparkles className="h-4 w-4" />
              Recommendation engine
            </div>
            <h2 className="text-xl font-semibold sm:text-2xl">
              {mainRecommendation?.recommendation_text ??
                "High-revenue items should not automatically be reduced. Keep strong revenue items prioritized, but optimize preparation to reduce waste cost."}
            </h2>
            <p className="mt-2 text-sm leading-6 text-teal-50/90">
              {mainRecommendation?.reason ??
                "The dashboard highlights high-value items that should stay available while prep is tuned to limit unnecessary waste."}
            </p>
          </div>
          <button
            type="button"
            className="inline-flex items-center justify-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-semibold text-teal-700"
          >
            Review action
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {dashboardMetrics.map((item, index) => {
          const Icon = item.icon;
          return (
            <article
              key={index}
              className="rounded-[24px] border border-slate-200/80 bg-white p-4 shadow-sm"
            >
              <div className={`mb-4 flex h-10 w-10 items-center justify-center rounded-2xl ${item.tone}`}>
                <Icon className="h-5 w-5" />
              </div>
              <p className="text-sm text-slate-500">{item.title}</p>
              <p className="mt-2 text-lg font-semibold leading-tight text-slate-900 sm:text-xl">{item.value}</p>
              <p className="mt-1 text-sm leading-5 text-slate-500">{item.detail}</p>
            </article>
          );
        })}
      </section>

      <section className="grid gap-4 xl:grid-cols-[2fr_1fr]">
        <article className="rounded-[28px] border border-slate-200/80 bg-white p-4 shadow-sm sm:p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Performance trend</p>
              <h3 className="text-lg font-semibold text-slate-900">Revenue vs Waste Trend</h3>
            </div>
            <div className="rounded-full bg-teal-50 px-3 py-1 text-sm font-medium text-teal-700">
              +11.2%
            </div>
          </div>
          <div className="rounded-[24px] bg-slate-50 p-4">
            <div className="flex h-48 items-end gap-3">
              {liveSalesBars.map((bar) => (
                <div key={bar.label} className="flex flex-1 flex-col items-center gap-2">
                  <div className="flex h-36 w-full items-end rounded-full bg-white p-1">
                    <div
                      className="w-full rounded-full bg-gradient-to-t from-teal-600 to-emerald-400"
                      style={{ height: bar.height }}
                    />
                  </div>
                  <span className="text-xs font-medium text-slate-500">{bar.label}</span>
                </div>
              ))}
            </div>
          </div>
        </article>

        <article className="rounded-[28px] border border-slate-200/80 bg-white p-4 shadow-sm sm:p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Top revenue</p>
              <h3 className="text-lg font-semibold text-slate-900">High revenue items</h3>
            </div>
          </div>
          <div className="space-y-3">
            {liveTopRevenueItems.map((item) => (
              <div key={item.name} className="rounded-2xl bg-slate-50 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold leading-tight text-slate-800">{item.name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-slate-900">{item.value}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
        <article className="rounded-[28px] border border-slate-200/80 bg-white p-4 shadow-sm sm:p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Waste watch</p>
              <h3 className="text-lg font-semibold text-slate-900">Highest Waste Quantity</h3>
            </div>
          </div>
          <div className="space-y-3">
            {liveWasteItems.map((item) => (
              <div key={item.name} className="flex items-center justify-between gap-3 rounded-2xl bg-slate-50 p-3">
                <div className="min-w-0">
                  <p className="text-sm font-semibold leading-tight text-slate-800">{item.name}</p>
                </div>
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                  {item.value}
                  <ArrowUpRight className="h-4 w-4 shrink-0 text-emerald-600" />
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="rounded-[28px] border border-slate-200/80 bg-white p-4 shadow-sm sm:p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Menu insights</p>
              <h3 className="text-lg font-semibold text-slate-900">Menu Item Performance</h3>
            </div>
          </div>
          <div className="overflow-hidden rounded-[20px] border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-xs sm:text-sm">
              <thead className="bg-slate-50 text-left text-slate-500">
                <tr>
                  <th className="px-2 py-3 font-medium sm:px-3">Menu Item</th>
                  <th className="px-2 py-3 font-medium sm:px-3">Quantity Sold</th>
                  <th className="px-2 py-3 font-medium sm:px-3">Revenue</th>
                  <th className="px-2 py-3 font-medium sm:px-3">Waste Quantity</th>
                  <th className="px-2 py-3 font-medium sm:px-3">Waste Ratio</th>
                  <th className="px-2 py-3 font-medium sm:px-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {liveInventoryRows.map((row) => (
                  <tr key={row.item} className="text-slate-700">
                    <td className="px-2 py-3 font-semibold sm:px-3">{row.item}</td>
                    <td className="px-2 py-3 sm:px-3">{row.sold}</td>
                    <td className="px-2 py-3 sm:px-3">{row.revenue}</td>
                    <td className="px-2 py-3 sm:px-3">{row.waste}</td>
                    <td className="px-2 py-3 sm:px-3">{row.ratio}</td>
                    <td className="px-2 py-3 sm:px-3">
                      <span className="rounded-full bg-teal-50 px-2.5 py-1 text-[11px] font-medium text-teal-700">
                        {row.action}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
      </section>
    </AppShell>
  );
}
