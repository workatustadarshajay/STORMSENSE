import { CloudLightning } from "lucide-react";
import { useState } from "react";
import type { WhatIfRequest, WhatIfResult } from "../api/client";
import { useWhatIf } from "../api/hooks";
import { ErrorState } from "../components/StateViews";
import { money } from "../lib/format";

const STARTS = [
  { value: 0, label: "Tomorrow" }, { value: 1, label: "In two days" }, { value: 2, label: "In three days" },
  { value: 3, label: "In four days" }, { value: 4, label: "In five days" }, { value: 5, label: "In six days" }, { value: 6, label: "In a week" },
];
const REGIONS = [
  { value: "", label: "All stores" }, { value: "Florida", label: "Florida" }, { value: "Texas", label: "Texas" }, { value: "California", label: "California" },
];

function Result({ r }: { r: WhatIfResult }) {
  if (!r.answered) {
    return <p role="status" className="rounded-2xl border border-dashed border-line bg-paper p-6 font-semibold">{r.message}</p>;
  }
  const rows = r.rows ?? [];
  return (
    <div className="grid gap-5">
      <section aria-labelledby="cost-h" className="rounded-2xl bg-ink p-5 text-white sm:p-6">
        <h2 id="cost-h" className="text-sm font-bold uppercase tracking-wide text-glow">Cost of doing nothing</h2>
        <p className="mt-2 text-4xl font-extrabold">{money(r.extra_lost_usd ?? 0)}</p>
        <p className="mt-2 text-white/85">{r.sentence}</p>
      </section>

      <dl className="grid grid-cols-3 gap-3 text-center">
        <div className="rounded-2xl border border-line bg-paper p-3"><dt className="text-sm text-muted">Normal week</dt><dd className="text-2xl font-extrabold">{r.normal_units}</dd></div>
        <div className="rounded-2xl border border-line bg-paper p-3"><dt className="text-sm text-muted">With the storm</dt><dd className="text-2xl font-extrabold text-signal">{r.storm_units}</dd></div>
        <div className="rounded-2xl border border-line bg-paper p-3"><dt className="text-sm text-muted">Stock to move</dt><dd className="text-2xl font-extrabold text-teal-deep">{r.stock_to_move_units}</dd></div>
      </dl>

      {rows.length > 0 && (
        <section aria-labelledby="rows-h">
          <h2 id="rows-h" className="text-xl font-extrabold">Where the sales would be lost</h2>
          <div className="mt-3 overflow-x-auto rounded-2xl border border-line bg-paper">
            <table className="w-full min-w-max text-left text-sm tabular-nums">
              <caption className="sr-only">Sales at risk by store and product</caption>
              <thead className="bg-mist">
                <tr>
                  <th scope="col" className="px-3 py-2">Store</th><th scope="col" className="px-3 py-2">Product</th>
                  <th scope="col" className="px-3 py-2 text-right">Normal</th><th scope="col" className="px-3 py-2 text-right">Storm</th>
                  <th scope="col" className="px-3 py-2 text-right">On hand</th><th scope="col" className="px-3 py-2 text-right">Lost in sales</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={`${row.store}-${row.product}`} className="border-t border-line">
                    <td className="px-3 py-2 font-semibold">{row.store}</td><td className="px-3 py-2">{row.product}</td>
                    <td className="px-3 py-2 text-right">{row.normal_units}</td><td className="px-3 py-2 text-right">{row.storm_units}</td>
                    <td className="px-3 py-2 text-right">{row.on_hand}</td><td className="px-3 py-2 text-right font-bold">{money(row.extra_lost_usd)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {r.plan_change && (
        <section aria-labelledby="change-h" className="rounded-2xl border border-line bg-paper p-5">
          <h2 id="change-h" className="text-xl font-extrabold">What changed in the stock plan</h2>
          <p className="mt-2 text-ink-soft">{r.plan_change.sentence}</p>
          <p className="mt-2 text-sm text-muted">
            Compared with the plan saved before the last daily run (version {r.plan_change.before_version}), against the plan now (version {r.plan_change.now_version}).
          </p>
        </section>
      )}

      <p className="text-sm text-muted">
        These are estimates from the forecaster for a scenario you chose. They don't change any stock, transfer or forecast.
      </p>
    </div>
  );
}

export default function WhatIf() {
  const sim = useWhatIf();
  const [strength, setStrength] = useState(70);
  const [start, setStart] = useState(1);
  const [days, setDays] = useState(2);
  const [region, setRegion] = useState("");
  const body: WhatIfRequest = { strength, start_day: start, days, region: (region || null) as WhatIfRequest["region"] };

  return (
    <>
      <h1 className="flex items-center gap-3 text-4xl font-extrabold">
        <CloudLightning className="size-8 text-signal" aria-hidden /> What if a storm comes?
      </h1>
      <p className="mt-2 max-w-prose text-muted">
        Pick how strong the storm is and when it hits. The simulator shows the sales that would be lost if nothing moved, and how much stock would need to move to cover it.
      </p>

      <form
        className="mt-6 grid gap-5 rounded-2xl border border-line bg-paper p-5 sm:p-6"
        onSubmit={(e) => {
          e.preventDefault();
          sim.mutate(body);
        }}
      >
        <label className="grid gap-2">
          <span className="flex items-center justify-between font-bold">Storm strength <output aria-live="polite">{strength === 0 ? "None" : strength < 40 ? "Light" : strength < 75 ? "Strong" : "Severe"}</output></span>
          <input type="range" min={0} max={100} step={5} value={strength} onChange={(e) => setStrength(Number(e.target.value))}
            aria-valuetext={`${strength} out of 100`} className="h-3 w-full cursor-pointer accent-signal" />
        </label>
        <div className="grid gap-4 sm:grid-cols-3">
          <label className="grid gap-1.5">
            <span className="font-bold">When it hits</span>
            <select value={start} onChange={(e) => setStart(Number(e.target.value))} className="min-h-12 rounded-xl border border-line bg-white px-3">
              {STARTS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </label>
          <label className="grid gap-1.5">
            <span className="font-bold">How many days</span>
            <select value={days} onChange={(e) => setDays(Number(e.target.value))} className="min-h-12 rounded-xl border border-line bg-white px-3">
              {[1, 2, 3, 4].map((d) => <option key={d} value={d}>{d === 1 ? "1 day" : `${d} days`}</option>)}
            </select>
          </label>
          <label className="grid gap-1.5">
            <span className="font-bold">Where</span>
            <select value={region} onChange={(e) => setRegion(e.target.value)} className="min-h-12 rounded-xl border border-line bg-white px-3">
              {REGIONS.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
            </select>
          </label>
        </div>
        <button type="submit" disabled={sim.isPending} className="min-h-14 rounded-2xl bg-ink px-6 text-lg font-extrabold text-white disabled:bg-line disabled:text-muted">
          {sim.isPending ? "Running the simulation…" : "Run the storm"}
        </button>
      </form>

      <div className="mt-8" aria-live="polite">
        {sim.isError && <ErrorState error={sim.error} retry={() => sim.mutate(body)} />}
        {sim.isSuccess && <Result r={sim.data} />}
      </div>
    </>
  );
}
