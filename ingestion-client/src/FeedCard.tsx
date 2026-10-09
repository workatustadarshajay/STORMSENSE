import { useState } from "react";
import { autoMatch, headersOf } from "./csv";
import { clearFeed, type Feed, type UploadResult, uploadFile } from "./api";

function download(name: string, text: string) {
  const url = URL.createObjectURL(new Blob([text], { type: "text/csv" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

export function FeedCard({ feed, onChanged }: { feed: Feed; onChanged: () => void }) {
  const [csv, setCsv] = useState<string | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [result, setResult] = useState<UploadResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const headers = csv ? headersOf(csv) : [];
  const missing = feed.columns.filter((c) => c.required && !mapping[c.name]).map((c) => c.name);

  const choose = async (file: File) => {
    const text = await file.text();
    setCsv(text);
    setResult(null);
    setError(null);
    setMapping(autoMatch(feed.columns.map((c) => c.name), headersOf(text)));
  };
  const send = async () => {
    if (!csv) return;
    setBusy(true);
    setError(null);
    try {
      setResult(await uploadFile(feed.feed, csv, mapping));
      onChanged();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const clear = async () => {
    setError(null);
    try {
      await clearFeed(feed.feed);
      setResult(null);
      onChanged();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <article className="card" aria-labelledby={`feed-${feed.feed}`}>
      <div className="row between">
        <h2 id={`feed-${feed.feed}`}>{feed.title}</h2>
        <span className="muted">
          {feed.kept} rows kept{feed.refused ? `, ${feed.refused} refused` : ""}
          {feed.updated ? `, updated ${feed.updated.replace("T", " ")}` : ""}
        </span>
      </div>
      <p>{feed.what}</p>

      <div className="row wrap">
        <button type="button" className="secondary" onClick={() => download(`${feed.feed}-template.csv`, feed.template)}>
          Download template
        </button>
        <label className="button">
          Choose a CSV file
          <input type="file" accept=".csv,text/csv" className="visually-hidden"
            onChange={(e) => e.target.files?.[0] && choose(e.target.files[0])} />
        </label>
        {feed.kept > 0 && <button type="button" className="link" onClick={clear}>Clear this file</button>}
      </div>

      {csv && (
        <section className="mapping" aria-label={`Match columns for ${feed.title}`}>
          <h3>Match your columns</h3>
          <p className="muted">Each field needs a column from your file. Matching names are filled in for you.</p>
          <div className="grid">
            {feed.columns.map((c) => (
              <label key={c.name} className="field">
                <span><strong>{c.name}</strong>{c.required ? "" : " (optional)"}</span>
                <span className="muted small">{c.help}</span>
                <select value={mapping[c.name] ?? ""} onChange={(e) => setMapping({ ...mapping, [c.name]: e.target.value })}>
                  <option value="">{c.required ? "Choose a column" : "Leave blank"}</option>
                  {headers.map((h) => <option key={h} value={h}>{h}</option>)}
                </select>
              </label>
            ))}
          </div>
          <button type="button" disabled={busy || missing.length > 0} onClick={send}>
            {busy ? "Checking…" : "Upload and check"}
          </button>
          {missing.length > 0 && <p className="muted">Choose a column for: {missing.join(", ")}.</p>}
        </section>
      )}

      {result && (
        <div role="status" className="result">
          <p><strong>{result.message}</strong></p>
          {result.ignored_columns.length > 0 && <p className="muted">Not used: {result.ignored_columns.join(", ")}</p>}
          {result.refusals.length > 0 && (
            <ul>{result.refusals.map((r) => <li key={r.line}>Line {r.line}: {r.reason}</li>)}</ul>
          )}
        </div>
      )}
      {error && <p role="alert" className="error">{error}</p>}
    </article>
  );
}
