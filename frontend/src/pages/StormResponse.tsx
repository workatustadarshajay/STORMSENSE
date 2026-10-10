import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useStormDecide, useStormDraft } from "../api/hooks";
import { QueryView } from "../components/StateViews";
import { money } from "../lib/format";

export default function StormResponse() {
  const draft = useStormDraft();
  const decide = useStormDecide();
  const [chosen, setChosen] = useState<Set<string> | null>(null);
  const [reason, setReason] = useState("Not needed for this storm.");
  useEffect(() => {
    document.title = "Storm response · StormSense";
  }, []);

  return (
    <>
      <h1 className="text-4xl font-extrabold">Storm response</h1>
      <p className="mt-1 max-w-3xl text-muted">
        A storm is forecast, so the moves for it are drafted here. Nothing has been sent or moved. Keep the moves you want, and the rest are rejected with the reason you give.
      </p>
      <QueryView query={draft} rows={3} isEmpty={() => false}>
        {(d) => {
          const selected = chosen ?? new Set(d.moves.map((m) => m.id));
          const toggle = (id: string) => {
            const next = new Set(selected);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            setChosen(next);
          };
          const decided = d.status === "decided";
          return (
            <div className="mt-6 grid gap-5">
              <section className="rounded-2xl border border-line bg-paper p-5" aria-labelledby="storm-h">
                <h2 id="storm-h" className="text-xl font-extrabold">{d.storm}</h2>
                <p className="mt-1 text-muted">Expected {d.weekday} for {d.stores.join(", ")}.</p>
                <dl className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <div className="rounded-xl bg-mist p-3"><dt className="text-sm text-muted">Moves in the draft</dt><dd className="text-2xl font-extrabold">{d.moves.length}</dd></div>
                  <div className="rounded-xl bg-mist p-3"><dt className="text-sm text-muted">Sales protected</dt><dd className="text-2xl font-extrabold">{money(d.protected_usd)}</dd></div>
                  <div className="rounded-xl bg-mist p-3"><dt className="text-sm text-muted">Carbon (kg CO₂)</dt><dd className="text-2xl font-extrabold">{Math.round(d.co2_kg)}</dd></div>
                  <div className="rounded-xl bg-mist p-3"><dt className="text-sm text-muted">Markdowns to decide</dt><dd className="text-2xl font-extrabold">{d.markdowns_open}</dd></div>
                </dl>
              </section>

              {decided ? (
                <p role="status" className="rounded-2xl bg-teal-tint p-5 font-bold text-teal-deep">
                  Decided by {d.decided_by}: {d.approved} approved, {d.rejected} rejected.
                </p>
              ) : (
                <section aria-labelledby="moves-h">
                  <h2 id="moves-h" className="text-xl font-extrabold">Moves for this storm</h2>
                  <div className="mt-3 overflow-x-auto rounded-2xl border border-line">
                    <table className="w-full min-w-[40rem] text-left">
                      <thead className="bg-mist text-sm text-muted">
                        <tr>
                          <th scope="col" className="px-4 py-3"><span className="sr-only">Keep</span></th>
                          <th scope="col" className="px-4 py-3">Move</th>
                          <th scope="col" className="px-4 py-3">Urgency</th>
                          <th scope="col" className="px-4 py-3 text-right">Sales protected</th>
                        </tr>
                      </thead>
                      <tbody>
                        {d.moves.map((m) => (
                          <tr key={m.id} className="border-t border-line">
                            <td className="px-4 py-3">
                              <input type="checkbox" aria-label={`Keep: ${m.headline}`} checked={selected.has(m.id)} onChange={() => toggle(m.id)} />
                            </td>
                            <td className="px-4 py-3"><span className="font-bold">{m.headline}</span><br /><span className="text-sm text-muted">{m.reason}</span></td>
                            <td className="px-4 py-3">{m.urgency === "URGENT" ? "Urgent" : "Normal"}</td>
                            <td className="px-4 py-3 text-right">{money(m.sales_protected_usd)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
                    <label className="block text-sm font-bold">
                      Reason for the moves you reject
                      <input className="mt-1 min-h-11 w-full rounded-xl border border-line bg-white px-3 font-normal" value={reason}
                        onChange={(e) => setReason(e.target.value)} />
                    </label>
                    <button type="button" disabled={decide.isPending || reason.trim().length < 3}
                      onClick={() => decide.mutate({ id: d.id, approve_ids: [...selected], reason })}
                      className="min-h-12 rounded-xl bg-ink px-5 font-bold text-white disabled:bg-line disabled:text-muted">
                      {decide.isPending ? "Saving…" : `Approve ${selected.size}, reject ${d.moves.length - selected.size}`}
                    </button>
                  </div>
                  {decide.isError && <p role="alert" className="mt-2 font-semibold text-signal-deep">{decide.error.message}</p>}
                </section>
              )}

              <details className="rounded-2xl border border-line bg-paper p-5">
                <summary className="cursor-pointer font-bold">Notes for store managers (drafts)</summary>
                <p className="mt-2 text-sm text-muted">These are drafts only. They have not been sent, because store email addresses are not set up yet.</p>
                <ul className="mt-3 space-y-2">
                  {d.store_notes.map((n) => <li key={n.store}><strong>{n.store}:</strong> {n.text}</li>)}
                </ul>
              </details>
              <p className="text-sm"><Link to="/transfers" className="font-bold text-teal-deep underline">Back to transfers</Link></p>
            </div>
          );
        }}
      </QueryView>
    </>
  );
}
