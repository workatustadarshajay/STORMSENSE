import { Link } from "react-router-dom";
import { useCoverSimulation } from "../api/hooks";
import { QueryView } from "../components/StateViews";
import { money } from "../lib/format";

/** A parametric storm cover, simulated on today's forecast. An illustration for discussion; it is not a contract. */
export default function Cover() {
  const cover = useCoverSimulation();
  return (
    <>
      <h1 className="text-4xl font-extrabold">Storm cover (simulation)</h1>
      <p className="mt-1 text-muted">
        Would a storm cover pay out in each region, on the forecast this week? Sample data, illustrative thresholds.
      </p>
      <p className="mt-3 text-sm"><Link to="/impact" className="font-bold text-teal-deep underline">Back to business impact</Link></p>

      <QueryView query={cover} rows={3}>
        {(c) => (
          <>
            <div className="mt-6 rounded-2xl border border-line bg-paper p-5">
              <p className="font-bold">The trigger</p>
              <p className="mt-1 text-muted">{c.trigger}</p>
              <p className="mt-3 text-sm text-muted">
                Payout is the sales lost in the region, capped at {money(c.cap_usd)}. {c.note}
              </p>
            </div>
            <div className="mt-6 grid gap-4 md:grid-cols-3">
              {c.regions.map((r) => (
                <section key={r.region} aria-label={r.region} className={`rounded-2xl border p-5 ${r.triggered ? "border-signal/50 bg-signal-tint" : "border-line bg-paper"}`}>
                  <p className="text-sm font-bold text-muted">{r.region}</p>
                  <p className="mt-2 text-2xl font-extrabold">{r.triggered ? "Would trigger" : "Would not trigger"}</p>
                  <p className="mt-1 text-sm text-muted">
                    {r.stores_hit.length === 0
                      ? "No store reaches the trigger on this forecast."
                      : `${r.stores_hit.length} stores reach the trigger: ${r.stores_hit.join(", ")}${r.first_day ? `, from ${r.first_day}` : ""}.`}
                  </p>
                  <dl className="mt-4 grid gap-2 text-sm">
                    <div className="flex justify-between"><dt className="text-muted">Sales lost if nothing moves</dt><dd className="font-bold">{money(r.projected_lost_sales_usd)}</dd></div>
                    <div className="flex justify-between"><dt className="text-muted">Units still short</dt><dd className="font-bold">{r.projected_short_units}</dd></div>
                    <div className="flex justify-between"><dt className="text-muted">Illustrative payout</dt><dd className="font-bold">{money(r.simulated_payout_usd)}</dd></div>
                  </dl>
                </section>
              ))}
            </div>
          </>
        )}
      </QueryView>
    </>
  );
}
