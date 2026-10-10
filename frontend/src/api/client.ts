import type { components } from "./schema";

type S = components["schemas"];
export type Me = S["Me"];
export type Overview = S["Overview"];
export type Transfer = S["Transfer"];
export type DecisionResult = S["DecisionResult"];
export type StoreSummary = S["StoreSummary"];
export type StoreForecast = S["StoreForecast"];
export type ProductForecast = S["ProductForecast"];
export type InventoryItem = S["InventoryItem"];
export type AskResponse = S["AskResponse"];
export type WeatherAlert = S["WeatherAlert"];
export type StormDeskPlan = S["StormDeskPlan"];
export type WhatIfResult = S["WhatIfResult"];
export type WhatIfRequest = S["WhatIfRequest"];
export type RejectReason = S["RejectRequest"]["reason_code"];
/** live = the real forecast; demo = a demo storm placed on the Florida stores. */
export type WeatherMode = "live" | "demo";
const weatherQuery = (mode: WeatherMode) => (mode === "demo" ? "?weather=demo" : "");
export type BacktestStorm = S["BacktestStorm"];
export type MarkdownSuggestion = S["MarkdownSuggestion"];
export type Health = S["Health"];
export type Analysis = S["Analysis"];
export type PlanStatus = S["PlanStatus"];
export type DemoAlertResult = S["DemoAlertResult"];

/** A problem the server explained in plain words. */
export class ApiError extends Error {
  constructor(readonly status: number, readonly code: string, message: string) {
    super(message);
  }
}

/** Which data the planner chose: "sample" or "live". Missing means the copy's default. */
export const SOURCE_KEY = "stormsense.source";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const source = typeof localStorage === "undefined" ? null : localStorage.getItem(SOURCE_KEY);
  let res: Response;
  try {
    res = await fetch(path, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "stormsense",
        ...(source ? { "X-Data-Source": source } : {}),
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError(0, "offline", "You seem to be offline. Check your connection and try again.");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const detail = body?.detail;
    throw new ApiError(
      res.status,
      detail?.code ?? "unknown",
      detail?.message ?? "Something went wrong. Please try again.",
    );
  }
  return res.json() as Promise<T>;
}

const post = <T>(path: string, body: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(body) });
const query = (params: Record<string, string | undefined>) => {
  const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v) as [string, string][]).toString();
  return q ? `?${q}` : "";
};

export const api = {
  me: () => request<Me>("/api/me"),
  health: () => request<Health>("/api/health"),
  ingestAnalysis: () => request<Analysis>("/api/ingest/analysis"),
  planStatus: () => request<PlanStatus>("/api/ingest/plan/status"),
  decideMarkdown: (store_id: string, product_id: string, decision: "APPROVED" | "REJECTED") =>
    post<MarkdownSuggestion>("/api/markdowns/decision", { store_id, product_id, decision }),
  overview: (weather: WeatherMode = "live") => request<Overview>(`/api/overview${weatherQuery(weather)}`),
  transfers: (status?: Transfer["status"], urgency?: Transfer["urgency"]) =>
    request<Transfer[]>(`/api/transfers${query({ status, urgency })}`),
  approve: (ids: string[], note?: string) => post<DecisionResult>("/api/transfers/approve", { ids, note: note || null }),
  reject: (ids: string[], reason: string, reasonCode?: RejectReason) =>
    post<DecisionResult>("/api/transfers/reject", { ids, reason, reason_code: reasonCode ?? null }),
  stores: (weather: WeatherMode = "live") => request<StoreSummary[]>(`/api/stores${weatherQuery(weather)}`),
  forecast: (storeId: string) => request<StoreForecast>(`/api/stores/${storeId}/forecast`),
  history: () => request<Transfer[]>("/api/history"),
  backtest: () => request<BacktestStorm[]>("/api/backtest"),
  demoAlert: () => post<DemoAlertResult>("/api/demo/alert", {}),
  markdowns: (weather: WeatherMode = "live") => request<MarkdownSuggestion[]>(`/api/markdowns${weatherQuery(weather)}`),
  ask: (question: string) => post<AskResponse>("/api/ask", { question }),
  stormDesk: (goal: string) => post<StormDeskPlan>("/api/storm-desk", { goal }),
  whatIf: (body: WhatIfRequest) => post<WhatIfResult>("/api/what-if", body),
};
