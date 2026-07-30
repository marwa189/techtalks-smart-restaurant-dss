import { AppShell } from "../components/app-shell";
import { AlertTriangle, Sparkles, Target } from "lucide-react";

const recommendations = [
  {
    severity: "High",
    title: "Increase prep for the weekend set",
    reason: "Demand is expected to rise above the current prep plan.",
    item: "Kaya Toast Set",
  },
  {
    severity: "Medium",
    title: "Reduce beverage overproduction",
    reason: "Late service data shows lower sell-through for chilled drinks.",
    item: "Teh Tarik",
  },
  {
    severity: "Low",
    title: "Keep premium items visible in the service line",
    reason: "High revenue items are outperforming but need consistent exposure.",
    item: "Tandoori Chicken",
  },
];

export default function RecommendationsPage() {
  return (
    <AppShell
      title="Recommendations"
      subtitle="Action center"
      description="A clean MVP list of operational actions for the team to review."
    >
      <section className="rounded-[28px] border border-slate-200/80 bg-white p-4 shadow-sm sm:p-5">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">Suggested actions</p>
            <h2 className="text-lg font-semibold text-slate-900">Priority recommendations</h2>
          </div>
          <div className="rounded-full bg-teal-50 px-3 py-1 text-sm font-medium text-teal-700">
            3 active
          </div>
        </div>

        <div className="space-y-3">
          {recommendations.map((item) => (
            <article key={item.title} className="rounded-[24px] border border-slate-200 bg-slate-50 p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-teal-700">
                    {item.severity === "High" ? (
                      <AlertTriangle className="h-5 w-5" />
                    ) : item.severity === "Medium" ? (
                      <Sparkles className="h-5 w-5" />
                    ) : (
                      <Target className="h-5 w-5" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-800">{item.title}</p>
                    <p className="mt-1 text-sm text-slate-500">{item.reason}</p>
                  </div>
                </div>
                <div className="flex flex-col items-start gap-2 sm:items-end">
                  <span className="rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-slate-700">
                    {item.severity}
                  </span>
                  <span className="text-sm font-medium text-slate-600">Target: {item.item}</span>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </AppShell>
  );
}
