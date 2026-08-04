"use client";

import { useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/app-shell";
import {
  getDashboardSummary,
  getSalesTrends,
  getTopMenuItems,
  type DashboardSummary,
  type MenuItemMetric,
  type SalesTrendPoint,
} from "../../lib/api";
import {
  ArrowUpRight,
  CircleDollarSign,
  PackageCheck,
  TrendingUp,
  UtensilsCrossed,
} from "lucide-react";

const fallbackTrendBars = [
  { label: "Mon", height: "46%" },
  { label: "Tue", height: "58%" },
  { label: "Wed", height: "66%" },
  { label: "Thu", height: "62%" },
  { label: "Fri", height: "84%" },
  { label: "Sat", height: "91%" },
  { label: "Sun", height: "78%" },
];

const fallbackTopItems = [
  { name: "Tandoori Chicken", value: "$248K", change: "+14%" },
  { name: "Kaya Toast Set", value: "$221K", change: "+10%" },
  { name: "Cendol", value: "$118K", change: "+6%" },
];

const fallbackPerformanceRows = [
  { name: "Kaya Toast Set", sold: "2,420", revenue: "$89K", status: "Growing" },
  { name: "Roti Canai", sold: "1,882", revenue: "$52K", status: "Stable" },
  { name: "Teh Tarik", sold: "3,108", revenue: "$48K", status: "Watch" },
];

function formatNumber(value: number) {
  return value.toLocaleString("en-US");
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function getDayLabel(period: string) {
  return new Intl.DateTimeFormat("en-US", { weekday: "short" }).format(new Date(period));
}

export default function SalesAnalyticsPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [salesTrends, setSalesTrends] = useState<SalesTrendPoint[]>([]);
  const [topMenuItems, setTopMenuItems] = useState<MenuItemMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadSalesAnalytics() {
      try {
        const [summaryData, trendData, topItemsData] = await Promise.all([
          getDashboardSummary(),
          getSalesTrends(),
          getTopMenuItems(),
        ]);

        setSummary(summaryData);
        setSalesTrends(trendData);
        setTopMenuItems(topItemsData);
        setError(null);
      } catch (err) {
        console.error("Failed to load sales analytics", err);
        setError("Could not load live sales analytics. Showing fallback data.");
      } finally {
        setLoading(false);
      }
    }

    loadSalesAnalytics();
  }, []);

  const topPerformer = topMenuItems[0];
  const averageTicket =
    summary && summary.total_quantity_sold > 0
      ? summary.total_revenue / summary.total_quantity_sold
      : null;

  const summaryCards = [
    {
      title: "Revenue summary",
      value: loading ? "Loading..." : summary ? formatCurrency(summary.total_revenue) : "$1.24M",
      detail: "Total revenue from the connected dataset",
      icon: CircleDollarSign,
      tone: "bg-teal-50 text-teal-700",
    },
    {
      title: "Quantity sold",
      value: loading ? "Loading..." : summary ? formatNumber(summary.total_quantity_sold) : "18,420",
      detail: "Units sold across the connected dataset",
      icon: PackageCheck,
      tone: "bg-emerald-50 text-emerald-700",
    },
    {
      title: "Average ticket",
      value: loading ? "Loading..." : averageTicket ? formatCurrency(averageTicket) : "$16.80",
      detail: "Average revenue per sold unit",
      icon: TrendingUp,
      tone: "bg-amber-50 text-amber-700",
    },
    {
      title: "Top performer",
      value: loading ? "Loading..." : topPerformer?.menu_item_name ?? "Tandoori Chicken",
      detail: "Highest revenue item in the dataset",
      icon: UtensilsCrossed,
      tone: "bg-sky-50 text-sky-700",
    },
  ];

  const trendBars = useMemo(() => {
    if (!salesTrends.length) {
      return fallbackTrendBars;
    }

    const latestTrends = salesTrends.slice(-7);
    const maxRevenue = Math.max(...latestTrends.map((point) => point.revenue), 1);

    return latestTrends.map((point) => ({
      label: getDayLabel(point.period),
      height: `${Math.max((point.revenue / maxRevenue) * 100, 8)}%`,
    }));
  }, [salesTrends]);

  const topItems = topMenuItems.length
    ? topMenuItems.slice(0, 3).map((item) => ({
        name: item.menu_item_name,
        value: formatCurrency(item.revenue),
        change: `${formatNumber(item.quantity_sold)} sold`,
      }))
    : fallbackTopItems;

  const performanceRows = topMenuItems.length
    ? topMenuItems.slice(0, 5).map((item, index) => ({
        name: item.menu_item_name,
        sold: formatNumber(item.quantity_sold),
        revenue: formatCurrency(item.revenue),
        status: index === 0 ? "Top revenue" : item.average_waste_ratio > 0.1 ? "Watch" : "Stable",
      }))
    : fallbackPerformanceRows;

  return (
    <AppShell
      title="Sales Analytics"
      subtitle="Operations overview"
      description="A lightweight MVP view for daily sales movement and high-value items."
    >
      {error ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800">
          {error}
        </div>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {summaryCards.map((item, index) => {
          const Icon = item.icon;
          return (
            <article key={index} className="rounded-[24px] border border-slate-200/80 bg-white p-4 shadow-sm">
              <div className={`mb-4 flex h-10 w-10 items-center justify-center rounded-2xl ${item.tone}`}>
                <Icon className="h-5 w-5" />
              </div>
              <p className="text-sm text-slate-500">{item.title}</p>
              <p className="mt-2 text-lg font-semibold text-slate-900">{item.value}</p>
              <p className="mt-1 text-sm text-slate-500">{item.detail}</p>
            </article>
          );
        })}
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <article className="rounded-[28px] border border-slate-200/80 bg-white p-4 shadow-sm sm:p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Sales trend</p>
              <h2 className="text-lg font-semibold text-slate-900">Revenue movement this week</h2>
            </div>
            <div className="rounded-full bg-teal-50 px-3 py-1 text-sm font-medium text-teal-700">
              +11.2%
            </div>
          </div>
          <div className="rounded-[24px] bg-slate-50 p-4">
            <div className="flex h-48 items-end gap-3">
              {trendBars.map((bar) => (
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
              <p className="text-sm font-medium text-slate-500">Top items</p>
              <h2 className="text-lg font-semibold text-slate-900">Highest revenue dishes</h2>
            </div>
          </div>
          <div className="space-y-3">
            {topItems.map((item) => (
              <div key={item.name} className="rounded-2xl bg-slate-50 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-800">{item.name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-slate-900">{item.value}</p>
                    <p className="text-xs font-medium text-emerald-600">{item.change}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="rounded-[28px] border border-slate-200/80 bg-white p-4 shadow-sm sm:p-5">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">Weekly snapshot</p>
            <h2 className="text-lg font-semibold text-slate-900">Sales by menu item</h2>
          </div>
        </div>
        <div className="overflow-hidden rounded-[20px] border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-slate-500">
              <tr>
                <th className="px-3 py-3 font-medium">Menu item</th>
                <th className="px-3 py-3 font-medium">Quantity sold</th>
                <th className="px-3 py-3 font-medium">Revenue</th>
                <th className="px-3 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white text-slate-700">
              {performanceRows.map((row) => (
                <tr key={row.name}>
                  <td className="px-3 py-3 font-semibold">{row.name}</td>
                  <td className="px-3 py-3">{row.sold}</td>
                  <td className="px-3 py-3">{row.revenue}</td>
                  <td className="px-3 py-3">
                    <span className="inline-flex items-center gap-1 rounded-full bg-teal-50 px-2.5 py-1 text-xs font-medium text-teal-700">
                      <ArrowUpRight className="h-3.5 w-3.5" />
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </AppShell>
  );
}
