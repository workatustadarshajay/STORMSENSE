// The backend's data-ingest routes. Changes need the same-origin header the backend checks for.
export type Column = { name: string; kind: string; required: boolean; help: string; choices: string[] };
export type Feed = {
  feed: string; title: string; what: string; kept: number; refused: number; updated: string | null;
  columns: Column[]; template: string;
};
export type Refusal = { line: number; reason: string };
export type UploadResult = {
  feed: string; kept: number; refused: number; refusals: Refusal[];
  missing_columns: string[]; ignored_columns: string[]; message: string;
};

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", "X-Requested-With": "stormsense", ...(init.headers ?? {}) },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body?.detail?.message ?? `The request failed (${res.status}).`);
  return body as T;
}

export const listFeeds = () => call<Feed[]>("/api/ingest/feeds");
export const uploadFile = (feed: string, csv: string, mapping: Record<string, string>) =>
  call<UploadResult>(`/api/ingest/feeds/${feed}/upload`, { method: "POST", body: JSON.stringify({ csv, mapping }) });
export const clearFeed = (feed: string) => call<{ message: string }>(`/api/ingest/feeds/${feed}`, { method: "DELETE" });
