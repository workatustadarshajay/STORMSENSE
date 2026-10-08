import { CloudLightning, CloudRain, Flame, Sun, TriangleAlert, type LucideIcon } from "lucide-react";
import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import type { ProductForecast, StoreForecast } from "../api/client";
import { useForecast, useStores } from "../api/hooks";
import { QueryView } from "../components/StateViews";
import { shortDay } from "../lib/format";

const ICON: Record<string, LucideIcon> = { storm: CloudLightning, heavy_rain: CloudRain, rain: CloudRain, heat: Flame, clear: Sun };
const TONE: Record<string, string> = {
  storm: "bg-signal-tint text-signal-deep",
  heavy_rain: "bg-rain-tint text-rain",
  heat: "bg-heat-tint text-heat",
};

function WeatherStrip({ days }: { days: StoreForecast["weather"] }) {
  return (
    <ul aria-label="Weather this week" tabIndex={0} className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 lg:mx-0 lg:px-0">
      {days.map((d) => {
        const Icon = ICON[d.condition] ?? Sun;
        return (
          <li key={d.date} className={`flex min-w-[4.5rem] flex-1 flex-col items-center rounded-2xl px-2 py-3 text-center ${TONE[d.condition] ?? "bg-paper text-ink-soft"}`}>
            <span className="text-sm font-extrabold">{shortDay(d.date)}</span>
            <Icon className="my-1.5 size-6" aria-hidden />
            <span className="text-lg font-extrabold leading-none">{d.temp_max_f}°</span>
            <span className="mt-1 text-xs font-semibold">{d.label}</span>
            {d.wind_max_mph >= 25 && <span className="text-xs">{d.wind_max_mph} mph</span>}
          </li>
        );
      })}
    </ul>
  );
}

function Chip({ p }: { p: ProductForecast }) {
  if (p.status === "RUNNING_LOW")
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-signal-tint px-3 py-1 text-sm font-extrabold text-signal-deep">
        <TriangleAlert className="size-4" aria-hidden /> Runs low {p.runs_low_day}
      </span>
    );
  if (p.status === "EXTRA") return <span className="rounded-full bg-rain-tint px-3 py-1 text-sm font-extrabold text-rain">Extra stock</span>;
  return <span className="rounded-full bg-teal-tint px-3 py-1 text-sm font-extrabold text-teal-deep">On track</span>;
}

function Bars({ p }: { p: ProductForecast }) {
  const max = Math.max(...p.days.map((d) => d.units), 1);
  const lowAt = p.status === "RUNNING_LOW" ? p.days.findIndex((d) => d.weekday === p.runs_low_day) : -1;
  const summary = p.days.map((d, i) => `${d.weekday} ${d.units}${i === lowAt ? " (runs low)" : ""}`).join(", ");
  return (
    <div role="img" aria-label={`Expected sales per day: ${summary}`} className="mt-4 flex h-28 items-end gap-1.5 sm:gap-2">
      {p.days.map((d, i) => (
        <div key={d.date} aria-hidden className="flex h-full flex-1 flex-col justify-end text-center">
          <span className="text-xs font-bold">{d.units}</span>
          <span className={`mt-0.5 block rounded-t-md ${i === lowAt ? "bg-signal" : "bg-teal"}`} style={{ height: `${Math.max(6, (d.units / max) * 70)}%` }} />
          <span className={`mt-1 text-xs ${i === lowAt ? "font-extrabold text-signal" : "font-semibold text-muted"}`}>{shortDay(d.date)}</span>
        </div>
      ))}
    </div>
  );
}

function ProductBlock({ p }: { p: ProductForecast }) {
  return (
    <section aria-labelledby={`p-${p.product.id}`} className={`rounded-2xl border bg-paper p-4 sm:p-5 ${p.status === "RUNNING_LOW" ? "border-signal/40" : "border-line"}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 id={`p-${p.product.id}`} className="text-xl font-extrabold">
          {p.product.name}
        </h3>
        <Chip p={p} />
      </div>
      <p className="mt-2 text-ink-soft">
        About <strong>{p.total_units}</strong> expected this week <span className="text-muted">(likely {p.range_low} to {p.range_high})</span>. {p.available} on hand and on the way.
      </p>
      <Bars p={p} />
      <p className="mt-3 text-sm text-ink-soft">{p.why}</p>
    </section>
  );
}

export default function Stores() {
  const stores = useStores();
  const [params, setParams] = useSearchParams();
  const wanted = params.get("store");
  const list = stores.data;
  // Default to the store in the most trouble.
  const fallback = list ? [...list].sort((a, b) => b.running_low - a.running_low)[0]?.id : undefined;
  const storeId = list?.some((s) => s.id === wanted) ? wanted! : fallback;
  const forecast = useForecast(storeId);

  useEffect(() => {
    document.title = "Store forecast · StormSense";
  }, []);

  return (
    <>
      <h1 className="text-4xl font-extrabold">Store forecast</h1>
      <p className="mt-1 text-muted">What each store is likely to sell this week, and when it could run low.</p>

      <QueryView query={stores} rows={2}>
        {(data) => (
          <div className="mt-6">
            <label className="block">
              <span className="font-bold">Store</span>
              <select
                value={storeId}
                onChange={(e) => setParams({ store: e.target.value })}
                className="mt-1.5 block min-h-14 w-full rounded-2xl border border-line bg-paper px-4 text-lg font-bold"
              >
                {data.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}, {s.region}
                    {s.running_low > 0 ? ` (${s.running_low} running low)` : ""}
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}
      </QueryView>

      <div className="mt-6" aria-live="polite">
        {storeId && (
          <QueryView query={forecast} rows={3}>
            {(f) => (
              <div className="grid gap-4">
                <WeatherStrip days={f.weather} />
                {f.products.map((p) => (
                  <ProductBlock key={p.product.id} p={p} />
                ))}
              </div>
            )}
          </QueryView>
        )}
      </div>
    </>
  );
}
