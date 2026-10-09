import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useBacktest } from "../api/hooks";
import { QueryView } from "../components/StateViews";
import { money } from "../lib/format";

export default function Backtest() {
  const storms = useBacktest();
  useEffect(() => {
    document.title = "Past storms · StormSense";
  }, []);

  return (
    <>
      <h1 className="text-4xl font-extrabold">Past storms, replayed</h1>
      <p className="mt-1 max-w-3xl text-muted">
        What each past storm cost in lost sales, and how much of it nearby stock could have covered. It uses what really sold, so read it as the best case a planner could have reached.
      </p>

      <section aria-labelledby="how-h" className="mt-6 rounded-2xl border border-line bg-paper p-5">
        <h2 id="how-h" className="font-extrabold">How this is worked out</h2>
        <ul className="mt-2 list-disc space-y-1.5 pl-5 text-ink-soft">
          <li>Stock at the start of the storm is the count the day before it.</li>
          <li>Lost sales are the units sold during the storm beyond that stock. Restocking during the storm is not counted.</li>
          <li>Protected sales are what a store with spare stock nearby could have sent, within the distance limit. This is an estimate of the best case, not a forecast.</li>
        </ul>
      </section>

      <div className="mt-6">
        <QueryView query={storms} rows={3} isEmpty={(d) => d.length === 0}>
          {(rows) => {
            const lost = rows.reduce((sum, r) => sum + r.lost_usd, 0);
            const protectedUsd = rows.reduce((sum, r) => sum + r.protected_usd, 0);
            return (
              <>
                <p className="text-lg font-bold">
                  Across {rows.length} named storms, {money(lost)} of sales were lost. Nearby stock could have covered {money(protectedUsd)} of it.
                </p>
                <div className="mt-4 overflow-x-auto rounded-2xl border border-line">
                  <table className="w-full min-w-[40rem] text-left">
                    <caption className="sr-only">Named storms with their lost sales and the share nearby stock could have covered</caption>
                    <thead className="bg-mist text-sm text-muted">
                      <tr>
                        <th scope="col" className="px-4 py-3">Storm</th>
                        <th scope="col" className="px-4 py-3">Dates</th>
                        <th scope="col" className="px-4 py-3 text-right">Stores hit</th>
                        <th scope="col" className="px-4 py-3 text-right">Sales lost</th>
                        <th scope="col" className="px-4 py-3 text-right">Could have protected</th>
                        <th scope="col" className="px-4 py-3 text-right">Share</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((r) => (
                        <tr key={r.event_name} className="border-t border-line">
                          <th scope="row" className="px-4 py-3 font-bold">{r.event_name}</th>
                          <td className="px-4 py-3 text-sm text-muted">{r.start_date} to {r.end_date}</td>
                          <td className="px-4 py-3 text-right">{r.stores}</td>
                          <td className="px-4 py-3 text-right font-bold">{money(r.lost_usd)}</td>
                          <td className="px-4 py-3 text-right">{money(r.protected_usd)}</td>
                          <td className="px-4 py-3 text-right font-bold">{Math.round(r.share_protected * 100)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="mt-4 text-sm text-muted">
                  A low share means the nearby stores were short too, or had little left over. That is useful to know before the next storm.{" "}
                  <Link to="/transfers" className="font-bold text-teal-deep underline">Back to transfers</Link>
                </p>
              </>
            );
          }}
        </QueryView>
      </div>
    </>
  );
}
