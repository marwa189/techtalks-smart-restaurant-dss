import {
  AlertTriangle,
  ArrowUpRight,
  BarChart3,
  Bell,
  ChevronRight,
  CircleDollarSign,
  LayoutDashboard,
  Leaf,
  Search,
  Sparkles,
  TrendingUp,
  UtensilsCrossed,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const navigation: Array<{ icon: LucideIcon; active?: boolean }> = [
  { icon: LayoutDashboard, active: true },
  { icon: BarChart3 },
  { icon: UtensilsCrossed },
  { icon: AlertTriangle },
];

const metrics = [
  {
    title: "Daily orders",
    value: "1,284",
    detail: "+12% vs yesterday",
    icon: TrendingUp,
    tone: "bg-teal-50 text-teal-700",
  },
  {
    title: "Waste avoided",
    value: "86 kg",
    detail: "+9% this week",
    icon: Leaf,
    tone: "bg-emerald-50 text-emerald-700",
  },
  {
    title: "Revenue",
    value: "$24.8k",
    detail: "Forecast on pace",
    icon: CircleDollarSign,
    tone: "bg-amber-50 text-amber-700",
  },
  {
    title: "Prep efficiency",
    value: "94%",
    detail: "Improved cadence",
    icon: Sparkles,
    tone: "bg-sky-50 text-sky-700",
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
  { name: "Lunch Combo", value: "$3.8k", change: "+18%" },
  { name: "Seasonal Bowl", value: "$2.6k", change: "+11%" },
  { name: "Weekend Brunch", value: "$2.1k", change: "+7%" },
];

const wasteItems = [
  { name: "Over-prepped greens", value: "14 kg" },
  { name: "Unsold desserts", value: "9 kg" },
  { name: "Low-turn proteins", value: "6 kg" },
];

const inventoryRows = [
  { item: "House salad", category: "Fresh", margin: "24%", status: "Healthy" },
  { item: "Soba noodles", category: "Dry goods", margin: "31%", status: "Steady" },
  { item: "Lemon herb chicken", category: "Protein", margin: "19%", status: "Peak" },
  { item: "Cocoa tart", category: "Bakery", margin: "16%", status: "Watch" },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-[#eef6f5] p-4 text-slate-800 sm:p-6 lg:p-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 lg:flex-row">
        <aside className="flex w-full flex-col justify-between rounded-[32px] bg-[#0f766e] p-5 text-white shadow-[0_24px_60px_rgba(15,118,110,0.25)] lg:w-72 lg:p-6">
          <div>
            <div className="mb-8 flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/20">
                <UtensilsCrossed className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-medium text-teal-50">SmartDine</p>
                <p className="text-xs text-teal-100">Operations</p>
              </div>
            </div>

            <nav className="flex gap-2 lg:flex-col" aria-label="Sidebar navigation">
              {navigation.map((item, index) => {
                const Icon = item.icon;
                return (
                  <button
                    key={index}
                    type="button"
                    aria-label={`Navigation item ${index + 1}`}
                    className={`flex h-11 w-11 items-center justify-center rounded-2xl transition ${
                      item.active
                        ? "bg-white/20 shadow-inner"
                        : "bg-white/10 hover:bg-white/20"
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="mt-6 rounded-[24px] border border-white/20 bg-white/10 p-4 backdrop-blur">
            <p className="text-sm font-semibold">Tonight boost</p>
            <p className="mt-2 text-sm leading-6 text-teal-50">
              Prep the citrus herb set earlier to lift sell-through by 14%.
            </p>
          </div>
        </aside>

        <main className="flex-1 space-y-4">
          <div className="flex flex-col gap-3 rounded-[28px] border border-slate-200/80 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between sm:p-5">
            <div>
              <p className="text-sm font-medium text-teal-700">Smart Restaurant Decision Support</p>
              <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
                SmartDine Dashboard
              </h1>
            </div>
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500">
                <Search className="h-4 w-4" />
                <span className="hidden sm:inline">Search</span>
              </label>
              <button
                type="button"
                className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100"
                aria-label="Notifications"
              >
                <Bell className="h-4 w-4 text-slate-600" />
              </button>
            </div>
          </div>

          <section className="rounded-[28px] bg-gradient-to-r from-teal-700 via-teal-600 to-emerald-500 p-5 text-white shadow-[0_20px_45px_rgba(15,118,110,0.18)] sm:p-6">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div className="max-w-xl">
                <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-sm font-medium backdrop-blur">
                  <Sparkles className="h-4 w-4" />
                  Recommendation engine
                </div>
                <h2 className="text-xl font-semibold sm:text-2xl">
                  Shift 20 portions of the grilled citrus bowl to the 5 PM window.
                </h2>
                <p className="mt-2 text-sm leading-6 text-teal-50/90">
                  Demand is climbing 18% in the late afternoon. This move should lift margin while reducing surplus waste.
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

          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {metrics.map((item, index) => {
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
                  <p className="mt-2 text-2xl font-semibold text-slate-900">{item.value}</p>
                  <p className="mt-1 text-sm text-slate-500">{item.detail}</p>
                </article>
              );
            })}
          </section>

          <section className="grid gap-4 xl:grid-cols-[2fr_1fr]">
            <article className="rounded-[28px] border border-slate-200/80 bg-white p-4 shadow-sm sm:p-5">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">Demand trend</p>
                  <h3 className="text-lg font-semibold text-slate-900">Weekly sales pulse</h3>
                </div>
                <div className="rounded-full bg-teal-50 px-3 py-1 text-sm font-medium text-teal-700">
                  +11.2%
                </div>
              </div>
              <div className="rounded-[24px] bg-slate-50 p-4">
                <div className="flex h-48 items-end gap-3">
                  {salesBars.map((bar) => (
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
                  <h3 className="text-lg font-semibold text-slate-900">Fast movers</h3>
                </div>
              </div>
              <div className="space-y-3">
                {topRevenueItems.map((item) => (
                  <div key={item.name} className="rounded-2xl bg-slate-50 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-slate-800">{item.name}</p>
                        <p className="text-xs text-slate-500">Strong midday demand</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-slate-900">{item.value}</p>
                        <p className="text-xs text-emerald-600">{item.change}</p>
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
                  <h3 className="text-lg font-semibold text-slate-900">Reduction opportunities</h3>
                </div>
                <div className="rounded-full bg-amber-50 px-3 py-1 text-sm font-medium text-amber-700">
                  2.3 hrs saved
                </div>
              </div>
              <div className="space-y-3">
                {wasteItems.map((item) => (
                  <div key={item.name} className="flex items-center justify-between rounded-2xl bg-slate-50 p-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-800">{item.name}</p>
                      <p className="text-xs text-slate-500">Adjust prep volume</p>
                    </div>
                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                      {item.value}
                      <ArrowUpRight className="h-4 w-4 text-emerald-600" />
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="rounded-[28px] border border-slate-200/80 bg-white p-4 shadow-sm sm:p-5">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">Inventory pulse</p>
                  <h3 className="text-lg font-semibold text-slate-900">Top line items</h3>
                </div>
              </div>
              <div className="overflow-hidden rounded-[20px] border border-slate-200">
                <table className="min-w-full divide-y divide-slate-200 text-sm">
                  <thead className="bg-slate-50 text-left text-slate-500">
                    <tr>
                      <th className="px-3 py-3 font-medium">Item</th>
                      <th className="px-3 py-3 font-medium">Category</th>
                      <th className="px-3 py-3 font-medium">Margin</th>
                      <th className="px-3 py-3 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 bg-white">
                    {inventoryRows.map((row) => (
                      <tr key={row.item} className="text-slate-700">
                        <td className="px-3 py-3 font-semibold">{row.item}</td>
                        <td className="px-3 py-3">{row.category}</td>
                        <td className="px-3 py-3">{row.margin}</td>
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
            </article>
          </section>
        </main>
      </div>
    </div>
  );
}
