"use client";

import { useEffect, useState } from "react";
import { AppShell } from "../components/app-shell";
import {
  getDashboardSummary,
  getHighWasteLowSales,
  getMenuItemWaste,
  type DashboardSummary,
  type HighWasteLowSalesItem,
  type WasteMetric,
} from "../../lib/api";
import { AlertTriangle, DollarSign, Leaf, TrendingDown } from "lucide-react";

const fallbackWasteRows = [
  { item: "Teh Tarik", quantity: "4,120", cost: "$1,240", ratio: "12.4%" },
  { item: "Cendol", quantity: "3,410", cost: "$980", ratio: "11.2%" },
  { item: "Roti Canai", quantity: "2,980", cost: "$840", ratio: "9.1%" },
  { item: "Tandoori Chicken", quantity: "2,620", cost: "$760", ratio: "7.6%" },
];

const fallbackHighWasteItems = [
  { name: "Teh Tarik", note: "Slow moving in late service" },
  { name: "Cendol", note: "Prep volume exceeds peak demand" },
  { name: "Roti Canai", note: "High variance on weekend shifts" },
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

function formatPercent(value: number | null) {
  if (value === null) {
    return "N/A";
  }

  return `${(value * 100).toFixed(1)}%`;
}

export default function WasteAnalyticsPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [wasteItems, setWasteItems] = useState<WasteMetric[]>([]);
  const [highWasteItems, setHighWasteItems] = useState<HighWasteLowSalesItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadWasteAnalytics() {
      try {
        const [summaryData, wasteData, highWasteData] = await Promise.all([
          getDashboardSummary(),
          getMenuItemWaste(),
          getHighWasteLowSales(),
        ]);

        setSummary(summaryData);
        setWasteItems(wasteData);
        setHighWasteItems(highWasteData);
        setError(null);
      } catch (err) {
        console.error("Failed to load waste analytics", err);
        setError("Could not load live waste analytics. Showing fallback data.");
      } finally {
        setLoading(false);
      }
    }

    loadWasteAnalytics();
  }, []);

  const topWasteItem = wasteItems[0];
  const totalWasteCost = wasteItems.reduce((total, item) => total + item.waste_cost, 0);

  const summaryCards = [
    {
      title: "Total waste",
      value: loading
        ? "Loading..."
        : summary
          ? `${formatNumber(summary.total_waste_quantity)} units`
          : "14,820 units",
      detail: "Total waste from the connected dataset",
      icon: Leaf,
      tone: "bg-emerald-50 text-emerald-700",
    },
    {
      title: "Waste ratio",
      value: loading ? "Loading..." : summary ? formatPercent(summary.average_waste_ratio) : "8.6%",
      detail: "Average waste ratio across menu items",
      icon: AlertTriangle,
      tone: "bg-amber-50 text-amber-700",
    },
    {
      title: "Waste cost",
      value: loading ? "Loading..." : wasteItems.length ? formatCurrency(totalWasteCost) : "$4,320",
      detail: "Estimated value lost to waste",
      icon: DollarSign,
      tone: "bg-sky-50 text-sky-700",
    },
    {
      title: "Top waste item",
      value: loading ? "Loading..." : topWasteItem?.name ?? "Teh Tarik",
      detail: "Highest waste quantity item",
      icon: TrendingDown,
      tone: "bg-rose-50 text-rose-700",
    },
  ];

  const wasteRows = wasteItems.length
    ? wasteItems.slice(0, 5).map((item) => ({
        item: item.name,
        quantity: formatNumber(item.waste_quantity),
        cost: formatCurrency(item.waste_cost),
        ratio: formatPercent(item.average_waste_ratio),
      }))
    : fallbackWasteRows;

  const reviewItems = highWasteItems.length
    ? highWasteItems.slice(0, 4).map((item) => ({
        name: item.menu_item_name,
        note: item.reason,
      }))
    : fallbackHighWasteItems;

  return (
    <AppShell
      title="Waste Analytics"
      subtitle="Operations health"
      description="A simple MVP view for waste concentration, cost, and high-risk items."
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

      <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <article className="rounded-[28px] border border-slate-200/80 bg-white p-4 shadow-sm sm:p-5">
          <div className="mb-4">
            <p className="text-sm font-medium text-slate-500">Waste breakdown</p>
            <h2 className="text-lg font-semibold text-slate-900">Top waste items by quantity</h2>
          </div>
          <div className="overflow-hidden rounded-[20px] border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-slate-500">
                <tr>
                  <th className="px-3 py-3 font-medium">Item</th>
                  <th className="px-3 py-3 font-medium">Waste qty</th>
                  <th className="px-3 py-3 font-medium">Cost</th>
                  <th className="px-3 py-3 font-medium">Ratio</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white text-slate-700">
                {wasteRows.map((row) => (
                  <tr key={row.item}>
                    <td className="px-3 py-3 font-semibold">{row.item}</td>
                    <td className="px-3 py-3">{row.quantity}</td>
                    <td className="px-3 py-3">{row.cost}</td>
                    <td className="px-3 py-3">{row.ratio}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <article className="rounded-[28px] border border-slate-200/80 bg-white p-4 shadow-sm sm:p-5">
          <div className="mb-4">
            <p className="text-sm font-medium text-slate-500">High-waste items</p>
            <h2 className="text-lg font-semibold text-slate-900">Items to review soon</h2>
          </div>
          <div className="space-y-3">
            {reviewItems.map((item) => (
              <div key={item.name} className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-sm font-semibold text-slate-800">{item.name}</p>
                <p className="mt-1 text-sm text-slate-500">{item.note}</p>
              </div>
            ))}
          </div>
        </article>
      </section>
    </AppShell>
  );
}
