"use client";

import { useEffect, useState } from "react";
import { AppShell } from "../components/app-shell";
import { getForecastMenuItems, type ForecastPoint } from "../../lib/api";
import { CalendarDays, CircleCheckBig, TrendingUp } from "lucide-react";

const fallbackForecastRows = [
  { item: "Tandoori Chicken", date: "Aug 02", quantity: "1,280", status: "Stable" },
  { item: "Kaya Toast Set", date: "Aug 02", quantity: "1,140", status: "Rising" },
  { item: "Cendol", date: "Aug 03", quantity: "860", status: "Watch" },
  { item: "Teh Tarik", date: "Aug 03", quantity: "940", status: "Stable" },
];

function formatNumber(value: number) {
  return value.toLocaleString("en-US");
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
  }).format(new Date(value));
}

export default function ForecastPage() {
  const [forecastRows, setForecastRows] = useState<ForecastPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadForecast() {
      try {
        const data = await getForecastMenuItems();
        setForecastRows(data);
        setError(null);
      } catch (err) {
        console.error("Failed to load forecast", err);
        setError("Could not load live forecast data. Showing fallback data.");
      } finally {
        setLoading(false);
      }
    }

    loadForecast();
  }, []);

  const uniqueDates = new Set(forecastRows.map((row) => row.forecast_date));
  const averageQuantity =
    forecastRows.length > 0
      ? Math.round(
          forecastRows.reduce((total, row) => total + row.predicted_quantity_sold, 0) /
            forecastRows.length
        )
      : 0;

  const statusCards = [
    {
      title: "Forecast window",
      value: loading ? "Loading..." : forecastRows.length ? `${uniqueDates.size} days` : "Next 7 days",
      detail: "Coverage prepared for upcoming demand",
      icon: CalendarDays,
      tone: "bg-teal-50 text-teal-700",
    },
    {
      title: "Model",
      value: loading ? "Loading..." : forecastRows[0]?.model_name ?? "Pending",
      detail: "Prediction method used by backend",
      icon: CircleCheckBig,
      tone: "bg-emerald-50 text-emerald-700",
    },
    {
      title: "Avg predicted prep",
      value: loading ? "Loading..." : forecastRows.length ? formatNumber(averageQuantity) : "860",
      detail: "Average predicted quantity per row",
      icon: TrendingUp,
      tone: "bg-amber-50 text-amber-700",
    },
  ];

  const displayRows = forecastRows.length
    ? forecastRows.slice(0, 12).map((row) => ({
        item: row.menu_item_name,
        date: formatDate(row.forecast_date),
        quantity: formatNumber(row.predicted_quantity_sold),
        status: row.predicted_quantity_sold >= averageQuantity ? "High demand" : "Normal",
      }))
    : fallbackForecastRows;

  return (
    <AppShell
      title="Forecast"
      subtitle="Demand planning"
      description="A simple forecast MVP with predicted demand, dates, and confidence."
    >
      {error ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800">
          {error}
        </div>
      ) : null}

      <section className="grid gap-4 md:grid-cols-3">
        {statusCards.map((item, index) => {
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

      <section className="rounded-[28px] border border-slate-200/80 bg-white p-4 shadow-sm sm:p-5">
        <div className="mb-4">
          <p className="text-sm font-medium text-slate-500">Predicted demand</p>
          <h2 className="text-lg font-semibold text-slate-900">Upcoming menu demand snapshot</h2>
        </div>
        <div className="overflow-hidden rounded-[20px] border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-slate-500">
              <tr>
                <th className="px-3 py-3 font-medium">Menu item</th>
                <th className="px-3 py-3 font-medium">Forecast date</th>
                <th className="px-3 py-3 font-medium">Predicted quantity</th>
                <th className="px-3 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white text-slate-700">
              {displayRows.map((row) => (
                <tr key={`${row.item}-${row.date}`}>
                  <td className="px-3 py-3 font-semibold">{row.item}</td>
                  <td className="px-3 py-3">{row.date}</td>
                  <td className="px-3 py-3">{row.quantity}</td>
                  <td className="px-3 py-3">
                    <span className="rounded-full bg-teal-50 px-2.5 py-1 text-xs font-medium text-teal-700">
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
