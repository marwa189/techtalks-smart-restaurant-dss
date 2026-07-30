import { AppShell } from "../components/app-shell";
import {
  ArrowUpRight,
  CircleDollarSign,
  PackageCheck,
  TrendingUp,
  UtensilsCrossed,
} from "lucide-react";

const summaryCards = [
  {
    title: "Revenue summary",
    value: "$1.24M",
    detail: "Weekly sales across core menu items",
    icon: CircleDollarSign,
    tone: "bg-teal-50 text-teal-700",
  },
  {
    title: "Quantity sold",
    value: "18,420",
    detail: "Units moved across the last 7 days",
    icon: PackageCheck,
    tone: "bg-emerald-50 text-emerald-700",
  },
  {
    title: "Average ticket",
    value: "$16.80",
    detail: "Estimated basket size per order",
    icon: TrendingUp,
    tone: "bg-amber-50 text-amber-700",
  },
  {
    title: "Top performer",
    value: "Tandoori Chicken",
    detail: "Highest revenue item this week",
    icon: UtensilsCrossed,
    tone: "bg-sky-50 text-sky-700",
  },
];

const trendBars = [
  { label: "Mon", height: "46%" },
  { label: "Tue", height: "58%" },
  { label: "Wed", height: "66%" },
  { label: "Thu", height: "62%" },
  { label: "Fri", height: "84%" },
  { label: "Sat", height: "91%" },
  { label: "Sun", height: "78%" },
];

const topItems = [
  { name: "Tandoori Chicken", value: "$248K", change: "+14%" },
  { name: "Kaya Toast Set", value: "$221K", change: "+10%" },
  { name: "Cendol", value: "$118K", change: "+6%" },
];

const performanceRows = [
  { name: "Kaya Toast Set", sold: "2,420", revenue: "$89K", status: "Growing" },
  { name: "Roti Canai", sold: "1,882", revenue: "$52K", status: "Stable" },
  { name: "Teh Tarik", sold: "3,108", revenue: "$48K", status: "Watch" },
];

export default function SalesAnalyticsPage() {
  return (
    <AppShell
      title="Sales Analytics"
      subtitle="Operations overview"
      description="A lightweight MVP view for daily sales movement and high-value items."
    >
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
