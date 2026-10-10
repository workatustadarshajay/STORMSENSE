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
export type Upload = { csv: string } | { xlsx_base64: string };
export const uploadFile = (feed: string, file: Upload, mapping: Record<string, string>) =>
  call<UploadResult>(`/api/ingest/feeds/${feed}/upload`, { method: "POST", body: JSON.stringify({ ...file, mapping }) });

/** Base64 of raw bytes, in chunks so large workbooks do not overflow the call stack. */
export function toBase64(bytes: ArrayBuffer): string {
  const view = new Uint8Array(bytes);
  let binary = "";
  for (let i = 0; i < view.length; i += 0x8000) binary += String.fromCharCode(...view.subarray(i, i + 0x8000));
  return btoa(binary);
}
export const clearFeed = (feed: string) => call<{ message: string }>(`/api/ingest/feeds/${feed}`, { method: "DELETE" });
