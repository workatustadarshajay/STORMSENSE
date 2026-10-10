import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useLoads } from "../api/hooks";
import { QueryView } from "../components/StateViews";
import { money } from "../lib/format";

export default function Loads() {
  const loads = useLoads();
  useEffect(() => {
    document.title = "Shared truck loads · StormSense";
  }, []);

  return (
    <>
      <h1 className="text-4xl font-extrabold">Shared truck loads</h1>
      <p className="mt-1 max-w-3xl text-muted">
        Moves on the same route can travel on one truck. This shows the trips that would save, using the same cost per trip as the business impact page. It only suggests loads. Nothing changes until a planner approves the moves.
      </p>
      <QueryView query={loads} rows={3} isEmpty={(l) => l.routes.length === 0}
        empty={<p className="mt-6 text-muted">No moves are waiting, so there is nothing to load together. <Link to="/transfers" className="font-bold text-teal-deep underline">Back to transfers</Link></p>}>
        {(l) => (
          <div className="mt-6 grid gap-5">
            <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                ["Truck trips today", l.trips_now],
                ["Trips if loads are shared", l.trips_together],
                ["Trucking saved", money(l.saved_usd)],
                ["Carbon saved (kg CO₂)", Math.round(l.saved_kg)],
              ].map(([label, value]) => (
                <div key={String(label)} className="rounded-2xl bg-mist p-4">
                  <dt className="text-sm text-muted">{label}</dt>
                  <dd className="text-2xl font-extrabold">{value}</dd>
                </div>
              ))}
            </dl>
            <p className="text-sm text-muted">
              One truck carries {l.truck_units} units. Trucking is ${l.cost_per_mile} per mile per trip. Carbon uses about 0.9 kg CO₂ per loaded truck-mile.
            </p>
            <div className="grid gap-4">
              {l.routes.map((r) => (
                <section key={`${r.from_store}-${r.to_store}`} aria-label={`${r.from_store} to ${r.to_store}`}
                  className="rounded-2xl border border-line bg-paper p-5">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <h2 className="text-xl font-extrabold">{r.from_store} to {r.to_store}</h2>
                    <p className="text-sm text-muted">{r.miles} miles, {r.units} units</p>
                  </div>
                  <p className="mt-2 font-bold">
                    {r.trips_now === r.trips_together
                      ? `${r.trips_now} trip${r.trips_now === 1 ? "" : "s"}: no saving on this route.`
                      : `${r.trips_now} trips today, ${r.trips_together} together: saves ${money(r.saved_usd)}.`}
                  </p>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-ink-soft">
                    {r.moves.map((m) => <li key={m.id}>{m.qty} {m.product}</li>)}
                  </ul>
                </section>
              ))}
            </div>
          </div>
        )}
      </QueryView>
    </>
  );
}
