import { Link } from "react-router-dom";
import { useRecovery } from "../api/hooks";
import { QueryView } from "../components/StateViews";
import { money, parseDay } from "../lib/format";

const shortDate = (iso: string) => parseDay(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });

/** After each storm: what was lost, what could have been protected, and which stores were restocked first. */
export default function Recovery() {
  const recovery = useRecovery();
  return (
    <>
      <h1 className="text-4xl font-extrabold">Past storm recovery</h1>
      <p className="mt-1 text-muted">What each storm cost, and how the restock went. The learning loop for next season.</p>
      <p className="mt-3 text-sm"><Link to="/impact" className="font-bold text-teal-deep underline">Back to business impact</Link></p>

      <QueryView query={recovery} rows={3}>
        {(r) => (
          <>
            <p className="mt-6 rounded-2xl border border-line bg-paper p-4 text-sm text-muted">{r.note}</p>
            <div className="mt-6 grid gap-5">
              {r.events.map((e) => (
                <article key={e.event.event_name} className="rounded-2xl border border-line bg-paper p-5">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <h2 className="text-xl font-extrabold">{e.event.event_name}</h2>
                    <p className="text-sm text-muted">
                      {shortDate(e.event.start_date)} to {shortDate(e.event.end_date)}, {e.event.stores} stores
                    </p>
                  </div>
                  <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
                    <div><dt className="text-muted">Sales lost</dt><dd className="text-lg font-extrabold">{money(e.event.lost_usd)}</dd></div>
                    <div><dt className="text-muted">Protected by moves</dt><dd className="text-lg font-extrabold">{money(e.event.protected_usd)}</dd></div>
                    <div><dt className="text-muted">Not protected</dt><dd className="text-lg font-extrabold text-signal-deep">{money(e.unprotected_usd)}</dd></div>
                  </dl>
                  <div className="mt-4">
                    <p className="text-sm font-bold">Restocked, first to last</p>
                    {e.stores_restocked.length === 0 ? (
                      <p className="mt-1 text-sm text-muted">No approved restock recorded in this storm's window yet.</p>
                    ) : (
                      <ol className="mt-2 grid gap-1 text-sm">
                        {e.stores_restocked.map((s) => (
                          <li key={s.store.id}>
                            <strong>{s.store.name}</strong>: {s.moves} moves, {s.units} units, first decision {s.days_after_start} days after the storm started.
                          </li>
                        ))}
                      </ol>
                    )}
                  </div>
                </article>
              ))}
            </div>
          </>
        )}
      </QueryView>
    </>
  );
}
