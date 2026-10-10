import { useCallback, useEffect, useState } from "react";
import {
  type Analysis, type Checks, type Economics, type Feed, type PlanStatus,
  analysis as loadAnalysis, buildPlan, checks as loadChecks, economics as loadEconomics, emailPlanners,
  listFeeds, loadDemo, planStatus, saveEconomics, scanDrop, uploadCharts, type UploadCharts,
} from "./api";
import { FeedCard } from "./FeedCard";
import { ChartCard, CoverBars, DailyLine, StatusBars } from "./Charts";

const SNIPPET = `curl -X POST http://localhost:8000/api/ingest/feeds/stores/rows \\
  -H "Content-Type: application/json" \\
  -H "X-Requested-With: stormsense" \\
  -d '{"rows": [{"store_id": "S01", "name": "Orlando", "city": "Orlando",
        "region": "Florida", "latitude": 28.5, "longitude": -81.4}]}'`;

// The planner is its own app: on the dev server it runs on 5173, in a built copy it is at the root.
const PLANNER = import.meta.env.DEV ? "http://localhost:5173/?data=upload" : "/?data=upload";
const money = (n: number) => `$${Math.round(n).toLocaleString("en-US")}`;

export default function App() {
  const [feeds, setFeeds] = useState<Feed[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checks, setChecks] = useState<Checks | null>(null);
  const [plan, setPlan] = useState<PlanStatus | null>(null);
  const [data, setData] = useState<Analysis | null>(null);
  const [cost, setCost] = useState<Economics | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [charts, setCharts] = useState<UploadCharts | null>(null);

  const load = useCallback(() => {
    listFeeds().then((f) => { setFeeds(f); setError(null); }).catch((e: Error) => setError(e.message));
    loadChecks().then((c) => setChecks(c)).catch(() => setChecks(null));
    planStatus().then(setPlan).catch(() => setPlan(null));
    loadAnalysis().then(setData).catch(() => setData(null));
    loadEconomics().then(setCost).catch(() => setCost(null));
    uploadCharts().then(setCharts).catch(() => setCharts(null));
  }, []);
  useEffect(load, [load]);

  const run = async (label: string, job: () => Promise<unknown>) => {
    setBusy(true);
    setNote(null);
    try {
      const result = await job();
      setNote(label + (result && typeof result === "object" && "message" in result ? ` ${(result as { message: string }).message}` : ""));
      load();
    } catch (e) {
      setNote((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <main>
      <header>
        <h1>StormSense ingestion client</h1>
        <p className="muted">
          Bring in your own data. Load the sample, or upload your four files. Every row is checked, then the plan is built and
          you can see it in the planner.
        </p>
      </header>

      {error && (
        <section className="card" role="alert">
          <p className="error">{error}</p>
          <p className="muted">Uploads are switched on by the StormSense server setting <code>STORMSENSE_INGEST_ENABLED=1</code>. Restart the server after changing it.</p>
        </section>
      )}

      <section className="card" aria-labelledby="start-h">
        <h2 id="start-h">Start here</h2>
        <div className="row wrap">
          <button type="button" disabled={busy} onClick={() => run("Sample loaded.", loadDemo)}>Load the sample data (one click)</button>
          <button type="button" className="secondary" disabled={busy} onClick={() => run("Plan built.", buildPlan)}>Build the plan from my files</button>
          <a className="button secondary" href={PLANNER}>Open the planner on my data</a>
        </div>
        {note && <p role="status" className="result">{note}</p>}
        {plan?.ready && plan.net_benefit && (
          <p className="muted small">
            Estimated profit from the plan: {money(plan.net_benefit.net_usd)} (margin {money(plan.net_benefit.margin_usd)} less trucking {money(plan.net_benefit.trucking_usd)}).
          </p>
        )}
      </section>

      {charts && (
        <section className="card" aria-labelledby="pictures-h">
          <h2 id="pictures-h">Your data in pictures</h2>
          <p className="muted">What the files say, day by day and store by store. Each chart has its numbers in a table underneath.</p>
          <div className="charts">
            {charts.sales_by_day.length > 0 && (
              <ChartCard title="Sales each day" caption="Units sold across all stores"
                table={<table><thead><tr><th>Date</th><th>Units sold</th></tr></thead><tbody>
                  {charts.sales_by_day.map((r) => <tr key={r.date}><td>{r.date}</td><td>{r.units}</td></tr>)}</tbody></table>}>
                <DailyLine data={charts.sales_by_day} dataKey="units" color="#0097ac" label="Units sold" />
              </ChartCard>
            )}
            {charts.stock_by_day.length > 0 && (
              <ChartCard title="Stock on hand each day" caption="Units on hand across all stores"
                table={<table><thead><tr><th>Date</th><th>Units on hand</th></tr></thead><tbody>
                  {charts.stock_by_day.map((r) => <tr key={r.date}><td>{r.date}</td><td>{r.on_hand}</td></tr>)}</tbody></table>}>
                <DailyLine data={charts.stock_by_day} dataKey="on_hand" color="#231f20" label="Units on hand" />
              </ChartCard>
            )}
            {charts.cover_by_store.length > 0 && (
              <ChartCard title="Days of stock left, by store" caption="The lowest product in each store. Lines mark 7 and 21 days."
                table={<table><thead><tr><th>Store</th><th>Days left</th></tr></thead><tbody>
                  {charts.cover_by_store.map((r) => <tr key={r.store}><td>{r.store}</td><td>{r.days}</td></tr>)}</tbody></table>}>
                <CoverBars data={charts.cover_by_store} />
              </ChartCard>
            )}
            {Object.values(charts.status_counts).some((n) => n > 0) && (
              <ChartCard title="Store and product pairs by status" caption="Short under a week, Watch under three weeks, Plenty otherwise"
                table={<table><thead><tr><th>Status</th><th>Pairs</th></tr></thead><tbody>
                  {Object.entries(charts.status_counts).map(([k, v]) => <tr key={k}><td>{k}</td><td>{v}</td></tr>)}</tbody></table>}>
                <StatusBars counts={charts.status_counts} />
              </ChartCard>
            )}
          </div>
          <table className="completeness">
            <thead><tr><th>File</th><th>Rows kept</th><th>Rows refused</th></tr></thead>
            <tbody>{charts.completeness.map((c) => (
              <tr key={c.feed}><td>{c.feed}</td><td>{c.loaded ? c.kept : "not yet"}</td><td>{c.refused}</td></tr>
            ))}</tbody>
          </table>
        </section>
      )}

      <section className="card" aria-labelledby="checks-h">
        <h2 id="checks-h">What we found in your files</h2>
        {checks ? (
          <ul>{checks.sentences.map((s) => <li key={s}>{s}</li>)}</ul>
        ) : (
          <p className="muted">Upload a file to see the checks.</p>
        )}
      </section>

      <section className="card" id="analysis" aria-labelledby="analysis-h">
        <h2 id="analysis-h">Analysis</h2>
        {data ? (
          <>
            <p className="muted">Last {data.window_days} days of sales and the latest stock count on {data.as_of}. A simple check, not the forecast.</p>
            <div className="tiles">
              <div><strong>{data.short}</strong><span>running short</span></div>
              <div><strong>{data.watch}</strong><span>on watch</span></div>
              <div><strong>{money(data.sales_value_usd)}</strong><span>sales in the window</span></div>
              <div><strong>{money(data.stock_value_usd)}</strong><span>stock on hand</span></div>
            </div>
            {data.items.length > 0 && (
              <table>
                <thead><tr><th>Store</th><th>Product</th><th>On hand</th><th>Sells per day</th><th>Days left</th><th>Status</th></tr></thead>
                <tbody>
                  {data.items.map((i) => (
                    <tr key={`${i.store}-${i.product}`}>
                      <td>{i.store}</td><td><strong>{i.product}</strong></td><td>{i.on_hand}</td>
                      <td>{i.sold_per_day}</td><td>{i.days_of_cover ?? "–"}</td><td>{i.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {data.short > 0 && (
              <div className="row wrap">
                <button type="button" className="secondary" disabled={busy}
                  onClick={() => run("Planners were emailed.", emailPlanners)}>
                  Email the planners about {data.short} short product{data.short === 1 ? "" : "s"}
                </button>
                <span className="muted small">The email is sent by the workspace, so it needs the live workspace to be connected.</span>
              </div>
            )}
          </>
        ) : (
          <p className="muted">Upload your stores, products, daily sales and daily stock to see the analysis.</p>
        )}
      </section>

      <section className="card" aria-labelledby="cost-h">
        <h2 id="cost-h">Cost and margin</h2>
        <p className="muted">Used to estimate the profit of the plan. Both are assumptions until you enter your own.</p>
        {cost && (
          <form className="row wrap" onSubmit={(e) => { e.preventDefault(); run("Saved.", () => saveEconomics(cost)); }}>
            <label className="field">Truck cost per mile ($)
              <input type="number" step="0.1" min="0" value={cost.truck_cost_per_mile}
                onChange={(e) => setCost({ ...cost, truck_cost_per_mile: Number(e.target.value) })} />
            </label>
            <label className="field">Margin on sales (%)
              <input type="number" step="1" min="0" max="100" value={cost.margin_pct}
                onChange={(e) => setCost({ ...cost, margin_pct: Number(e.target.value) })} />
            </label>
            <button type="submit" disabled={busy}>Save</button>
          </form>
        )}
      </section>

      <section className="card" aria-labelledby="drop-h">
        <h2 id="drop-h">Drop folder</h2>
        <p>Put CSV or Excel files named <code>stores</code>, <code>products</code>, <code>sales</code> or <code>stock</code> into the drop folder on the server. They load automatically when the server is set to watch it, or you can load them now.</p>
        <button type="button" className="secondary" disabled={busy}
          onClick={() => run("Drop folder checked.", async () => {
            const r = await scanDrop();
            return { message: r.loaded.length ? `Loaded: ${r.loaded.join(", ")}.` : "Nothing waiting in the drop folder." };
          })}>
          Load files from the drop folder now
        </button>
      </section>

      <section className="card" aria-labelledby="ways-h">
        <h2 id="ways-h">Other ways to connect</h2>
        <ol>
          <li><strong>Upload here.</strong> Use the cards below. No code needed.</li>
          <li><strong>Send from your system.</strong> POST rows as JSON to <code>/api/ingest/feeds/&lt;feed&gt;/rows</code>. The checks are the same.</li>
          <li><strong>Connect an AI assistant.</strong> Point it at the MCP server at <code>http://localhost:8200/mcp</code>.</li>
        </ol>
        <pre>{SNIPPET}</pre>
        <p className="muted small">Feeds in order: stores, products, daily sales, daily stock. Sales and stock refer to the stores and products you upload first.</p>
      </section>

      {feeds?.map((f) => <FeedCard key={f.feed} feed={f} onChanged={load} />)}
    </main>
  );
}
