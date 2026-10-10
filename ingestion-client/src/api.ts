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

// ---- checks, plan, analysis, cost inputs, demo, drop folder ----------------------------------
export type Checks = { sentences: string[] };
export type PlanStatus = {
  ready: boolean; as_of: string | null;
  summary: { as_of: string; stores: number; products: number; transfers: number; short: number; protected_usd: number; miles: number } | null;
  net_benefit: { margin_usd: number; trucking_usd: number; net_usd: number } | null;
};
export type AnalysisItem = {
  store: string; product: string; on_hand: number; sold_per_day: number; days_of_cover: number | null; status: string;
};
export type Analysis = {
  as_of: string; window_days: number; stores: number; products: number; pairs: number; short: number; watch: number;
  sold_units: number; sales_value_usd: number; stock_value_usd: number;
  by_store: { store: string; short_items: number; stock_value_usd: number }[];
  items: AnalysisItem[];
};
export type Economics = { truck_cost_per_mile: number; margin_pct: number };

export const checks = () => call<Checks>("/api/ingest/checks");
export const planStatus = () => call<PlanStatus>("/api/ingest/plan/status");
export const buildPlan = () => call<PlanStatus>("/api/ingest/plan", { method: "POST" });
export const analysis = () => call<Analysis>("/api/ingest/analysis");
export const economics = () => call<Economics>("/api/ingest/economics");
export const saveEconomics = (body: Economics) =>
  call<Economics>("/api/ingest/economics", { method: "PUT", body: JSON.stringify(body) });
export const loadDemo = () =>
  call<{ loaded: Record<string, number>; checks: string[]; plan: PlanStatus }>("/api/ingest/demo/load", { method: "POST" });
export const scanDrop = () => call<{ folder: string; loaded: string[] }>("/api/ingest/drop/scan", { method: "POST" });
export const emailPlanners = () => call<{ started: boolean; message: string }>("/api/demo/alert", { method: "POST" });
