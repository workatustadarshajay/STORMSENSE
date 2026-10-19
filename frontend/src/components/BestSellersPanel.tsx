import { useState } from "react";
import { useBestSellers } from "../api/hooks";

type Weather = "heat" | "wind" | "rain";
const WEATHER: { value: Weather; label: string }[] = [
  { value: "heat", label: "Heat" },
  { value: "wind", label: "Wind and storms" },
  { value: "rain", label: "Heavy rain" },
];

/** Which products sell most under a kind of weather, over the next seven days, across all stores. */
export function BestSellersPanel() {
  const [weather, setWeather] = useState<Weather>("heat");
  const best = useBestSellers(weather);
  const top = best.data?.ranking ?? [];
  const max = Math.max(1, ...top.map((r) => r.units));

  return (
    <section aria-labelledby="best-h" className="mt-6 rounded-2xl border border-line bg-paper p-5">
      <h2 id="best-h" className="text-xl font-extrabold">Best sellers by weather</h2>
      <p className="mt-1 text-sm text-muted">Forecast units for the next seven days, across all stores.</p>
      <div role="group" aria-label="Weather" className="mt-3 flex flex-wrap gap-2">
        {WEATHER.map((w) => (
          <button
            key={w.value}
            type="button"
            aria-pressed={weather === w.value}
            onClick={() => setWeather(w.value)}
            className={`min-h-10 rounded-xl border px-4 text-sm font-bold ${weather === w.value ? "border-ink bg-ink text-white" : "border-line text-ink hover:border-teal"}`}
          >
            {w.label}
          </button>
        ))}
      </div>
      {best.isError && <p className="mt-3 text-sm text-signal-deep">Could not load this view. Try again in a moment.</p>}
      {best.data && (
        <>
          <ol className="mt-4 grid gap-3">
            {top.map((r) => (
              <li key={r.product.id}>
                <div className="flex justify-between text-sm">
                  <span className="font-bold">{r.product.name_plural}</span>
                  <span className="text-muted">
                    {r.units.toLocaleString("en-US")} units, {r.stores} stores
                  </span>
                </div>
                <div className="mt-1 h-2.5 overflow-hidden rounded-full bg-mist">
                  <div className="h-full rounded-full bg-teal" style={{ width: `${(r.units / max) * 100}%` }} />
                </div>
              </li>
            ))}
          </ol>
          <p className="mt-4 text-sm">
            <strong>What comes next:</strong> {best.data.what_next}
          </p>
        </>
      )}
    </section>
  );
}
