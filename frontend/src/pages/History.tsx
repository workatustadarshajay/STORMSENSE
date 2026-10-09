import { CheckCircle2, XCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { useHistory } from "../api/hooks";
import { Empty, QueryView } from "../components/StateViews";
import { personFromEmail, when } from "../lib/format";

export default function History() {
  const history = useHistory();
  return (
    <>
      <h1 className="text-4xl font-extrabold">History</h1>
      <p className="mt-1 text-muted">Every transfer that was approved or rejected, and by whom.</p>
      <p className="mt-2 text-sm">
        <Link to="/backtest" className="font-bold text-teal-deep underline">How past storms would have gone</Link>
      </p>
      <div className="mt-6">
        <QueryView
          query={history}
          isEmpty={(d) => d.length === 0}
          empty={
            <Empty title="Nothing decided yet" action={<Link to="/transfers" className="inline-flex min-h-12 items-center rounded-xl bg-ink px-5 font-bold text-white">Review transfers</Link>}>
              Approved and rejected transfers will show up here.
            </Empty>
          }
        >
          {(rows) => (
            <ul className="grid gap-3">
              {rows.map((t) => {
                const ok = t.status === "APPROVED";
                return (
                  <li key={t.id} className="rounded-2xl border border-line bg-paper p-4 sm:p-5">
                    <p className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-sm font-extrabold ${ok ? "bg-teal-tint text-teal-deep" : "bg-mist text-ink-soft"}`}>
                      {ok ? <CheckCircle2 className="size-4" aria-hidden /> : <XCircle className="size-4" aria-hidden />}
                      {ok ? "Approved" : "Rejected"}
                    </p>
                    <p className="mt-1.5 text-lg font-extrabold leading-snug">{t.headline}</p>
                    <p className="mt-1 text-sm text-muted">
                      {personFromEmail(t.decided_by)} on {when(t.decided_at)}
                    </p>
                    {t.note && <p className="mt-2 text-ink-soft">“{t.note}”</p>}
                  </li>
                );
              })}
            </ul>
          )}
        </QueryView>
      </div>
    </>
  );
}
