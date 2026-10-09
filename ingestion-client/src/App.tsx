import { useCallback, useEffect, useState } from "react";
import { type Feed, listFeeds } from "./api";
import { FeedCard } from "./FeedCard";

const SNIPPET = `curl -X POST /api/ingest/feeds/stores/rows \\
  -H "Content-Type: application/json" \\
  -H "X-Requested-With: stormsense" \\
  -d '{"rows": [{"store_id": "S01", "name": "Orlando", "city": "Orlando",
        "region": "Florida", "latitude": 28.5, "longitude": -81.4}]}'`;

export default function App() {
  const [feeds, setFeeds] = useState<Feed[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    listFeeds()
      .then((f) => { setFeeds(f); setError(null); })
      .catch((e: Error) => setError(e.message));
  }, []);
  useEffect(load, [load]);

  return (
    <main>
      <header>
        <h1>StormSense ingestion client</h1>
        <p className="muted">
          Connect your data to StormSense. Upload the four files here, or send the same rows from your own system.
          Every row is checked, and refused rows say why.
        </p>
      </header>

      <section className="card" aria-labelledby="ways-h">
        <h2 id="ways-h">Three ways to connect</h2>
        <ol>
          <li><strong>Upload here.</strong> Use the cards below. No code needed.</li>
          <li><strong>Send from your system.</strong> POST rows as JSON to <code>/api/ingest/feeds/&lt;feed&gt;/rows</code>. The checks are the same.</li>
          <li><strong>Connect an AI assistant.</strong> Point it at the MCP server at <code>http://localhost:8200/mcp</code>.</li>
        </ol>
        <pre>{SNIPPET}</pre>
        <p className="muted small">Feeds in order: stores, products, daily sales, daily stock. Sales and stock refer to the stores and products you upload first.</p>
      </section>

      {error && (
        <section className="card" role="alert">
          <p className="error">{error}</p>
          <p className="muted">Uploads are switched on by the StormSense server setting <code>STORMSENSE_INGEST_ENABLED=1</code>. Restart the server after changing it.</p>
        </section>
      )}

      {feeds?.map((f) => <FeedCard key={f.feed} feed={f} onChanged={load} />)}
    </main>
  );
}
