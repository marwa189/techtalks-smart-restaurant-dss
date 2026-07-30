"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  AlertTriangle,
  BarChart3,
  Bell,
  LayoutDashboard,
  Leaf,
  Search,
  Sparkles,
  UtensilsCrossed,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

const navigation: NavItem[] = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/sales-analytics", label: "Sales Analytics", icon: BarChart3 },
  { href: "/waste-analytics", label: "Waste Analytics", icon: UtensilsCrossed },
  { href: "/forecast", label: "Forecast", icon: AlertTriangle },
  { href: "/recommendations", label: "Recommendations", icon: Sparkles },
];

type AppShellProps = {
  title: string;
  subtitle?: string;
  description?: string;
  children: React.ReactNode;
};

export function AppShell({ title, subtitle, description, children }: AppShellProps) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-[#eef6f5] p-4 text-slate-800 sm:p-6 lg:p-8">  
      <div className="mx-auto flex max-w-7xl gap-4">
        <aside className="fixed left-4 top-4 bottom-4 z-50 hidden w-72 flex-col justify-between rounded-[32px] bg-[#0f766e] p-5 text-white shadow-[0_24px_60px_rgba(15,118,110,0.25)] lg:flex lg:p-6">
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

            <nav className="flex flex-wrap gap-2 lg:flex-col" aria-label="Sidebar navigation">
              {navigation.map((item) => {
                const Icon = item.icon;
                const isActive =
                  item.href === "/"
                    ? pathname === item.href
                    : pathname.startsWith(item.href);

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    aria-label={item.label}
                    className={`flex min-h-11 items-center justify-start gap-3 rounded-2xl px-3 py-2 text-left text-sm transition ${
                      isActive ? "bg-white/20 shadow-inner" : "bg-white/10 hover:bg-white/20"
                    }`}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span className="whitespace-nowrap text-sm font-medium">{item.label}</span>
                  </Link>
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

        <main className="ml-0 flex-1 space-y-4 lg:ml-76">
          <div className="flex flex-col gap-3 rounded-[28px] border border-slate-200/80 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between sm:p-5">
            <div>
              <p className="text-sm font-medium text-teal-700">{subtitle ?? "Smart Restaurant Decision Support"}</p>
              <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{title}</h1>
              {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
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

          {children}
        </main>
      </div>
    </div>
  );
}
