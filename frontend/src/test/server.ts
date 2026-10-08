import { vi } from "vitest";
import * as fx from "./fixtures";

type Handler = (body: unknown) => unknown;
export interface Server { calls: { method: string; path: string; body: unknown }[]; }

const json = (data: unknown, status = 200, headers?: Record<string, string>) =>
  new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json", ...headers } });

export const problem = (status: number, code: string, message: string) => json({ detail: { code, message } }, status);

/** A tiny stand-in for the backend. `routes` overrides any endpoint, keyed like "GET /api/overview". */
export function serve(routes: Record<string, Handler> = {}): Server {
  const server: Server = { calls: [] };
  const defaults: Record<string, Handler> = {
    "GET /api/me": () => fx.planner,
    "GET /api/overview": () => fx.overview,
    "GET /api/transfers?status=PENDING": () => fx.transfers,
    "GET /api/history": () => fx.history,
    "GET /api/stores": () => fx.stores,
    "GET /api/stores/S01/forecast": () => fx.forecast(fx.stores[0]),
    "GET /api/stores/S04/forecast": () => fx.forecast(fx.stores[1]),
    "POST /api/transfers/approve": (b) => fx.decided((b as { ids: string[] }).ids),
    "POST /api/transfers/reject": (b) => ({ ...fx.decided((b as { ids: string[] }).ids), action: "REJECTED", message: "1 transfer rejected." }),
    "POST /api/ask": () => fx.answer,
  };
  vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
    const method = init?.method ?? "GET";
    const body = init?.body ? JSON.parse(init.body as string) : undefined;
    server.calls.push({ method, path: url, body });
    const handler = routes[`${method} ${url}`] ?? defaults[`${method} ${url}`];
    if (!handler) return problem(404, "not_found", `no stub for ${method} ${url}`);
    const out = await handler(body);
    return out instanceof Response ? out : json(out);
  }));
  return server;
}
