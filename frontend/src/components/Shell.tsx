import { ChartColumn, CloudLightning, CloudSun, History, MessageCircle, Store, Truck, TrendingUp, type LucideIcon } from "lucide-react";
import { DataSourceSwitch } from "./DataSourceSwitch";
import { useEffect, useRef } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useMe } from "../api/hooks";

const NAV: { to: string; label: string; icon: LucideIcon; end?: boolean }[] = [
  { to: "/", label: "Today", icon: CloudSun, end: true },
  { to: "/transfers", label: "Transfers", icon: Truck },
  { to: "/stores", label: "Stores", icon: Store },
  { to: "/ask", label: "Ask", icon: MessageCircle },
  { to: "/analysis", label: "Analysis", icon: ChartColumn },
  { to: "/impact", label: "Business impact", icon: TrendingUp },
  { to: "/history", label: "History", icon: History },
];

function Brand() {
  return (
    <span className="inline-flex items-center gap-2.5 text-lg font-extrabold tracking-tight">
      <span className="grid size-8 place-items-center rounded-lg border border-glow/30 bg-glow/15 text-glow">
        <CloudLightning className="size-[18px]" fill="currentColor" aria-hidden />
      </span>
      <span>
        storm<span className="text-glow">sense</span>
      </span>
    </span>
  );
}

export function Shell() {
  const me = useMe();
  const { pathname } = useLocation();
  const main = useRef<HTMLElement>(null);
  const lastPath = useRef(pathname);

  // Keyboard and screen-reader users land at the top of the new page, not on the old link.
  useEffect(() => {
    if (lastPath.current !== pathname) {
      lastPath.current = pathname;
      main.current?.focus({ preventScroll: true });
    }
    window.scrollTo(0, 0);
  }, [pathname]);

  const sample = me.data?.data_label === "sample";
  const uploaded = me.data?.data_label === "uploaded";
  const label = sample || uploaded ? (
    <span className="rounded-full border border-white/25 px-2.5 py-0.5 text-xs font-semibold text-white/85">{uploaded ? "Your data" : "Sample data"}</span>
  ) : null;

  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[16rem_1fr]">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-paper focus:px-4 focus:py-2 focus:font-bold">
        Skip to content
      </a>

      <aside className="rail sticky top-0 hidden h-dvh flex-col bg-ink p-6 text-white lg:flex">
        <Brand />
        <nav aria-label="Main" className="mt-10 grid gap-1">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex min-h-12 items-center gap-3 rounded-xl px-4 font-semibold transition-colors ${
                  isActive ? "bg-white/12 text-white" : "text-[#a9b8c2] hover:bg-white/8 hover:text-white"
                }`
              }
            >
              <Icon className="size-5" aria-hidden />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto grid gap-3 text-sm">
          <DataSourceSwitch />
          {label}
          {me.data && (
            <p className="text-[#a9b8c2]">
              <span className="block font-bold text-white">{me.data.name}</span>
              <span className="capitalize">{me.data.role}</span>
            </p>
          )}
        </div>
      </aside>

      <div className="flex min-h-dvh min-w-0 flex-col">
        <header className="on-dark flex h-14 items-center justify-between bg-ink px-4 text-white lg:hidden">
          <Brand />
          {label}
        </header>
        <main id="main" ref={main} tabIndex={-1} className="mx-auto w-full max-w-3xl flex-1 px-4 pb-32 pt-6 outline-none lg:px-8 lg:pb-16 lg:pt-10">
          <Outlet />
        </main>
        <nav aria-label="Main" className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-line bg-paper pb-[env(safe-area-inset-bottom)] lg:hidden">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex min-h-16 flex-col items-center justify-center gap-0.5 text-xs font-bold ${isActive ? "text-teal-deep" : "text-muted"}`
              }
            >
              {({ isActive }) => (
                <>
                  <span className={`grid h-7 w-14 place-items-center rounded-full transition-colors ${isActive ? "bg-teal-tint" : ""}`}>
                    <Icon className="size-5" aria-hidden />
                  </span>
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  );
}
