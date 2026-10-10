import { useEffect } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "../api/client";
import { useIngestAnalysis } from "../api/hooks";
import { QueryView } from "../components/StateViews";
import { money } from "../lib/format";

// The ingestion client is its own app: on the dev server it runs on 5174, in a built copy it sits at /ingest/.
const INGEST_HOME = import.meta.env.DEV ? "http://localhost:5174/" : "/ingest/";

const STATUS_STYLE: Record<string, string> = {
  Short: "bg-signal-tint text-signal-deep",
  Watch: "bg-heat-tint text-heat",
  Plenty: "bg-teal-tint text-teal-deep",
  "No sales": "bg-mist text-muted",
};

export default function YourData() {
  const analysis = useIngestAnalysis();
  useEffect(() => {
    document.title = "Your data · StormSense";
  }, []);

  return (
    <>
      <h1 className="text-4xl font-extrabold">Your data</h1>
      <p className="mt-1 max-w-3xl text-muted">
        A plain look at the files you uploaded: how fast each product sells, and how many days of stock are left. This is a simple check, not the forecast.
      </p>
      {analysis.error instanceof ApiError && analysis.error.status === 404 ? (
        <div className="mt-6 rounded-2xl border border-line bg-paper p-5">
          <p className="font-bold">No uploaded data yet.</p>
          <p className="mt-1 text-muted">Upload your stores, products, daily sales and daily stock in the upload app, then come back.</p>
          <a href={INGEST_HOME} className="mt-4 inline-flex min-h-11 items-center rounded-xl bg-ink px-4 font-bold text-white">Open the upload app</a>
        </div>
      ) : (
      <QueryView query={analysis} rows={3}>
        {(a) => (
          <div className="mt-6 grid gap-6">
            <p className="text-sm text-muted">Based on the last {a.window_days} days of sales, and the latest stock count on {a.as_of}.</p>
            <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                ["Stores", a.stores], ["Products", a.products], ["Running short", a.short], ["On watch", a.watch],
                ["Sales in the window", money(a.sales_value_usd)], ["Stock on hand", money(a.stock_value_usd)],
              ].map(([label, value]) => (
                <div key={String(label)} className="rounded-2xl bg-mist p-4">
                  <dt className="text-sm text-muted">{label}</dt>
                  <dd className="text-2xl font-extrabold">{value}</dd>
                </div>
              ))}
            </dl>

            <section aria-labelledby="by-store-h">
              <h2 id="by-store-h" className="text-xl font-extrabold">By store</h2>
              <div className="mt-3 overflow-x-auto rounded-2xl border border-line">
                <table className="w-full min-w-[30rem] text-left">
                  <thead className="bg-mist text-sm text-muted">
                    <tr>
                      <th scope="col" className="px-4 py-3">Store</th>
                      <th scope="col" className="px-4 py-3 text-right">Running short</th>
                      <th scope="col" className="px-4 py-3 text-right">Stock on hand</th>
                    </tr>
                  </thead>
                  <tbody>
                    {a.by_store.map((s) => (
                      <tr key={s.store} className="border-t border-line">
                        <th scope="row" className="px-4 py-3 font-bold">{s.store}</th>
                        <td className="px-4 py-3 text-right">{s.short_items}</td>
                        <td className="px-4 py-3 text-right">{money(s.stock_value_usd)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section aria-labelledby="items-h">
              <h2 id="items-h" className="text-xl font-extrabold">Products to watch</h2>
              {a.items.length === 0 ? (
                <p className="mt-2 text-muted">Nothing is running short or on watch.</p>
              ) : (
                <div className="mt-3 overflow-x-auto rounded-2xl border border-line">
                  <table className="w-full min-w-[40rem] text-left">
                    <thead className="bg-mist text-sm text-muted">
                      <tr>
                        <th scope="col" className="px-4 py-3">Store</th>
                        <th scope="col" className="px-4 py-3">Product</th>
                        <th scope="col" className="px-4 py-3 text-right">On hand</th>
                        <th scope="col" className="px-4 py-3 text-right">Sells per day</th>
                        <th scope="col" className="px-4 py-3 text-right">Days left</th>
                        <th scope="col" className="px-4 py-3">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {a.items.map((i) => (
                        <tr key={`${i.store}-${i.product}`} className="border-t border-line">
                          <td className="px-4 py-3">{i.store}</td>
                          <td className="px-4 py-3 font-bold">{i.product}</td>
                          <td className="px-4 py-3 text-right">{i.on_hand}</td>
                          <td className="px-4 py-3 text-right">{i.sold_per_day}</td>
                          <td className="px-4 py-3 text-right">{i.days_of_cover ?? "–"}</td>
                          <td className="px-4 py-3">
                            <span className={`rounded-full px-2.5 py-0.5 text-sm font-bold ${STATUS_STYLE[i.status] ?? ""}`}>{i.status}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            <p className="text-sm text-muted">
              <Link to="/transfers" className="font-bold text-teal-deep underline">Review the moves in the planner</Link> (these still come from the planning data).
            </p>
          </div>
        )}
      </QueryView>
      )}
    </>
  );
}
