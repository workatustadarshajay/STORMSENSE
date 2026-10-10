import { QueryClient } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import App from "../App";
import * as fx from "./fixtures";
import { problem, serve } from "./server";

const quiet = () => new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: 0 } } });
const open = (path: string) => render(<MemoryRouter initialEntries={[path]}><App client={quiet()} /></MemoryRouter>);

const storms = [
  { event_name: "Hurricane Marlow", start_date: "2026-09-14", end_date: "2026-09-18", stores: 4, lost_units: 1086, lost_usd: 171310,
    protected_units: 22, protected_usd: 2658, share_protected: 0.016 },
  { event_name: "Heat Dome Ridge", start_date: "2026-07-06", end_date: "2026-07-10", stores: 3, lost_units: 63, lost_usd: 7197,
    protected_units: 11, protected_usd: 2049, share_protected: 0.285 },
];

describe("Storm readiness on Today", () => {
  it("shows each store's readiness, lowest first, with its label", async () => {
    serve({ "GET /api/overview": () => fx.overview, "GET /api/stores": () => fx.stores, "GET /api/me": () => fx.planner });
    open("/");
    expect(await screen.findByRole("heading", { name: "Storm readiness" })).toBeInTheDocument();
    const orlando = await screen.findByRole("img", { name: /20 percent ready, At risk/ });
    expect(orlando).toBeInTheDocument();
    const names = screen.getAllByRole("link").map((a) => a.textContent ?? "");
    expect(names.findIndex((t) => t.includes("Orlando"))).toBeLessThan(names.findIndex((t) => t.includes("Jacksonville")));
  });
});

describe("Past storms, replayed", () => {
  it("explains the method and shows lost sales against what nearby stock could have covered", async () => {
    serve({ "GET /api/backtest": () => storms, "GET /api/me": () => fx.planner });
    open("/backtest");
    expect(await screen.findByText(/Stock at the start of the storm is the count the day before it/)).toBeInTheDocument();
    expect(await screen.findByRole("row", { name: /Hurricane Marlow/ })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "$171,310" })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "28%" })).toBeInTheDocument();
  });

  it("is linked from History", async () => {
    serve({ "GET /api/history": () => [], "GET /api/me": () => fx.planner });
    open("/history");
    expect(await screen.findByRole("link", { name: "How past storms would have gone" })).toHaveAttribute("href", "/backtest");
  });
});

describe("Export and print", () => {
  it("offers the week's plan as a CSV download and a print option", async () => {
    serve({ "GET /api/transfers": () => fx.transfers, "GET /api/me": () => fx.planner, "GET /api/overview": () => fx.overview });
    open("/transfers");
    const csv = await screen.findByRole("link", { name: "Download this week's plan (CSV)" });
    expect(csv).toHaveAttribute("href", "/api/transfers/export?status=PENDING");
    expect(screen.getByRole("button", { name: "Print or save as PDF" })).toBeInTheDocument();
  });
});

describe("Weather switch on Today", () => {
  it("shows the demo storm with a clear label, and switches back to live weather", async () => {
    const user = userEvent.setup();
    const server = serve({
      "GET /api/overview?weather=demo": () => ({ ...fx.overview, weather_source: "demo" }),
      "GET /api/stores?weather=demo": () => fx.stores,
      "GET /api/me": () => fx.planner,
    });
    open("/?weather=demo");
    expect(await screen.findByText(/Demo storm: a storm is placed on the Florida stores/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Demo storm" })).toHaveAttribute("aria-pressed", "true");
    await user.click(screen.getByRole("button", { name: "Live weather" }));
    expect(screen.queryByText(/Demo storm: a storm is placed/)).not.toBeInTheDocument();
    expect(server.calls.some((c) => c.path === "/api/overview")).toBe(true);
  });
});

describe("Price markdowns on Today", () => {
  it("shows each suggestion with its discount and the cash it adds, and says nothing is changed", async () => {
    serve({
      "GET /api/overview": () => fx.overview, "GET /api/stores": () => fx.stores, "GET /api/me": () => fx.planner,
      "GET /api/markdowns": () => [{
        store: { id: "S01", name: "Orlando" }, product: { id: "P01", name: "1000W generator", name_plural: "1000W generators" },
        spare_units: 30, current_price: 1299, discount_pct: 10, new_price: 1169.1, units_cleared: 30, clears_all: true,
        extra_cash_usd: 260.48, note: "Mark 1000W generators down 10% to $1169.10 to sell about 30 of 30 in 14 days, about $260 more than holding them.",
      }],
    });
    open("/");
    expect(await screen.findByText("Orlando: 1000W generators, 10% off")).toBeInTheDocument();
    expect(screen.getByText("+$260")).toBeInTheDocument();
    expect(screen.getByText(/does not change prices in the stores/)).toBeInTheDocument();
  });
});

describe("Markdowns in demo weather", () => {
  it("shows the demo response assumption when demo weather is on", async () => {
    serve({
      "GET /api/overview?weather=demo": () => ({ ...fx.overview, weather_source: "demo" }), "GET /api/stores?weather=demo": () => fx.stores,
      "GET /api/me": () => fx.planner,
      "GET /api/markdowns?weather=demo": () => [{
        store: { id: "S04", name: "Jacksonville" }, product: { id: "P01", name: "1000W generator", name_plural: "1000W generators" },
        spare_units: 39, current_price: 1299, discount_pct: 20, new_price: 1039.2, units_cleared: 39, clears_all: true,
        extra_cash_usd: 1500, note: "Mark 1000W generators down 20% to $1039.20.", assumption: "Demo: each 10% off lifts sales by 40%.",
      }],
    });
    open("/?weather=demo");
    expect(await screen.findByText("Jacksonville: 1000W generators, 20% off")).toBeInTheDocument();
    expect(screen.getByText(/Demo response: each 10% off is assumed to lift sales by 40%/)).toBeInTheDocument();
  });
});


describe("Demo storm email", () => {
  it("sends the demo storm alert when the planner clicks the button, and confirms it", async () => {
    const user = userEvent.setup();
    const server = serve({
      "GET /api/overview?weather=demo": () => ({ ...fx.overview, weather_source: "demo" }),
      "GET /api/stores?weather=demo": () => fx.stores,
      "GET /api/me": () => fx.planner,
      "POST /api/demo/alert": () => ({ started: true, message: "Started. Databricks sends the email within a few minutes." }),
    });
    open("/?weather=demo");
    await user.click(await screen.findByRole("button", { name: "Email this storm alert" }));
    expect(await screen.findByText(/Started. Databricks sends the email/)).toBeInTheDocument();
    expect(server.calls.some((c) => c.method === "POST" && c.path === "/api/demo/alert")).toBe(true);
  });
});

describe("Data shown: sample or live", () => {
  it("disables live where the copy is not connected to the workspace", async () => {
    serve({ "GET /api/health": () => ({ status: "ok", mode: "mock", warehouse: "not_checked" }), "GET /api/me": () => fx.planner });
    open("/");
    const live = await screen.findByRole("button", { name: "Live workspace" });
    await waitFor(() => expect(live).toBeDisabled());
    expect(screen.getByRole("button", { name: "Sample data" })).toHaveAttribute("aria-pressed", "true");
  });
  it("switches to live and remembers the choice when the workspace is connected", async () => {
    const user = userEvent.setup();
    localStorage.clear();
    serve({ "GET /api/health": () => ({ status: "ok", mode: "databricks", warehouse: "not_checked" }), "GET /api/me": () => fx.planner });
    open("/");
    const live = await screen.findByRole("button", { name: "Live workspace" });
    await waitFor(() => expect(live).toBeEnabled());
    await user.click(live);
    expect(localStorage.getItem("stormsense.source")).toBe("live");
    expect(live).toHaveAttribute("aria-pressed", "true");
    localStorage.clear();
  });
});

describe("Show my uploaded data", () => {
  it("shows the analysis of uploaded data, with the short items first", async () => {
    serve({
      "GET /api/ingest/analysis": () => ({
        as_of: "2026-10-07", window_days: 28, stores: 10, products: 5, pairs: 50, short: 1, watch: 0, sold_units: 1000,
        sales_value_usd: 20000, stock_value_usd: 5000, by_store: [{ store: "Orlando", short_items: 1, stock_value_usd: 800 }],
        items: [{ store: "Orlando", product: "1000W generator", on_hand: 16, sold_per_day: 6.2, days_of_cover: 2.6, status: "Short", stock_value_usd: 800, sales_value_usd: 9000 }],
      }),
      "GET /api/me": () => fx.planner,
    });
    open("/your-data");
    expect(await screen.findByText("1000W generator")).toBeInTheDocument();
    expect(screen.getByText("Short")).toBeInTheDocument();
    expect(screen.getByText(/This is a simple check, not the forecast/)).toBeInTheDocument();
  });
  it("asks for the upload first when no data has been uploaded", async () => {
    serve({ "GET /api/ingest/analysis": () => problem(404, "not_ready", "Upload your stores, products, daily sales and daily stock files first."), "GET /api/me": () => fx.planner });
    open("/your-data");
    expect(await screen.findByText("No uploaded data yet.", {}, { timeout: 3000 })).toBeInTheDocument();
  });
  it("is reached from Today with a button", async () => {
    serve({ "GET /api/me": () => fx.planner });
    open("/");
    expect(await screen.findByRole("link", { name: "Show my uploaded data" })).toHaveAttribute("href", expect.stringContaining("#analysis"));
  });
});

describe("Your uploads as a data source", () => {
  it("offers your uploads once a plan exists, and a link can pick it", async () => {
    localStorage.clear();
    serve({
      "GET /api/health": () => ({ status: "ok", mode: "mock", warehouse: "not_checked" }),
      "GET /api/ingest/plan/status": () => ({ ready: true, as_of: "2026-10-07", summary: null, net_benefit: null }),
      "GET /api/me": () => fx.planner,
    });
    window.history.replaceState(null, "", "/?data=upload");
    open("/");
    const uploads = await screen.findByRole("button", { name: "Your uploads" });
    await waitFor(() => expect(uploads).toHaveAttribute("aria-pressed", "true"));
    expect(localStorage.getItem("stormsense.source")).toBe("upload");
    window.history.replaceState(null, "", "/");
    localStorage.clear();
  });
  it("keeps your uploads off until a plan is built", async () => {
    localStorage.clear();
    serve({
      "GET /api/health": () => ({ status: "ok", mode: "mock", warehouse: "not_checked" }),
      "GET /api/ingest/plan/status": () => ({ ready: false, as_of: null, summary: null, net_benefit: null }),
      "GET /api/me": () => fx.planner,
    });
    open("/");
    const uploads = await screen.findByRole("button", { name: "Your uploads" });
    await waitFor(() => expect(uploads).toBeDisabled());
  });
});


describe("Analysis and business impact", () => {
  it("shows the plan's charts, each with its numbers in a table", async () => {
    serve({
      "GET /api/analysis/charts": () => ({
        as_of: "2026-10-07", stock_available: 1200,
        demand_by_day: [{ date: "2026-10-08", units: 300 }],
        shortages_by_store: [{ store: "Orlando", count: 4 }],
        transfers_by_urgency: [{ urgency: "URGENT", moves: 1, protected_usd: 2308 }],
        protected_by_product: [{ product: "Generators", protected_usd: 2308 }],
      }),
      "GET /api/me": () => fx.planner,
    });
    open("/analysis");
    expect(await screen.findByText("Demand this week")).toBeInTheDocument();
    expect(screen.getByText("Shortages by store")).toBeInTheDocument();
    expect(screen.getAllByText("Show as a table")).toHaveLength(4);
  });
  it("explains the money, what changed, the assumptions and the timeline in plain words", async () => {
    serve({
      "GET /api/impact": () => ({
        source: "upload", as_of: "2026-10-07",
        headline: { protected_usd: 24944, margin_usd: 7483, trucking_usd: 4175, net_usd: 3308, co2_kg: 512, moves: 11, pending: 10, approved: 1, rejected: 0 },
        assumptions: ["Margin on sales is 30% (your figure, or the default)."],
        changes: { last_plan_at: "2026-10-08T09:12:00", moves_then: 11, moves_now: 10 },
        timeline: [{ at: "2026-10-08T09:12:00", kind: "plan_built", actor: "upload app", detail: "Built the plan: 11 moves, 11 products short." }],
      }),
      "GET /api/me": () => fx.planner,
    });
    open("/impact");
    expect(await screen.findByText("Estimated profit")).toBeInTheDocument();
    expect(screen.getByText(/The last plan was built 2026-10-08 at 09:12:00/)).toBeInTheDocument();
    expect(screen.getByText("Built the plan: 11 moves, 11 products short.")).toBeInTheDocument();
    expect(screen.getAllByText("Your uploads").length).toBeGreaterThan(0);
  });
});

describe("Morning briefing", () => {
  it("shows the headline and the plain lines at the top of Today", async () => {
    serve({
      "GET /api/briefing": () => ({ headline: "Review 2 urgent moves first.", lines: ["2 urgent, 9 waiting for a decision in total."] }),
      "GET /api/me": () => fx.planner,
    });
    open("/");
    expect(await screen.findByText("Review 2 urgent moves first.")).toBeInTheDocument();
    expect(screen.getByText("2 urgent, 9 waiting for a decision in total.")).toBeInTheDocument();
    expect(screen.getByText("Your morning briefing")).toBeInTheDocument();
  });
});

describe("Storm response", () => {
  const draftFixture = {
    id: "SR-TEST0001", status: "draft", source: "sample", storm: "Tropical Storm Odalys", weekday: "Sunday", onset: "2026-10-11",
    stores: ["Orlando", "Tampa"],
    moves: [
      { id: "TR-AAAA000001", headline: "Move 54 1000W generators from Jacksonville to Orlando", urgency: "URGENT", qty: 54, sales_protected_usd: 18578, distance_miles: 140, co2_kg: 41, reason: "Storm on Sunday." },
      { id: "TR-BBBB000002", headline: "Move 14 coolers from Miami to Tampa", urgency: "NORMAL", qty: 14, sales_protected_usd: 900, distance_miles: 210, co2_kg: 13, reason: "Demand rising." },
    ],
    protected_usd: 19478, co2_kg: 54, markdowns_open: 1,
    store_notes: [{ store: "Orlando", text: "Storm expected Sunday." }],
    created_at: "2026-10-10T08:00:00", decided_by: null, decided_at: null, approved: 0, rejected: 0,
  };
  it("shows the draft's moves, keeps all of them by default, and approves the chosen ones", async () => {
    const user = userEvent.setup();
    const server = serve({
      "POST /api/response/draft": () => draftFixture,
      "POST /api/response/SR-TEST0001/decide": () => ({ ...draftFixture, status: "decided", approved: 1, rejected: 1, decided_by: "Ava" }),
      "GET /api/me": () => fx.planner,
    });
    open("/response");
    expect(await screen.findByText("Move 54 1000W generators from Jacksonville to Orlando")).toBeInTheDocument();
    await user.click(screen.getByRole("checkbox", { name: /Keep: Move 14 coolers/ }));
    await user.click(screen.getByRole("button", { name: "Approve 1, reject 1" }));
    expect(await screen.findByText(/Decided by Ava: 1 approved, 1 rejected/)).toBeInTheDocument();
    const body = server.calls.find((c) => c.path === "/api/response/SR-TEST0001/decide")?.body as { approve_ids: string[] };
    expect(body.approve_ids).toEqual(["TR-AAAA000001"]);
  });
  it("tells the planner on Today that a storm response is ready, and sends them to review it", async () => {
    serve({
      "POST /api/response/draft": () => draftFixture,
      "GET /api/overview": () => ({ ...fx.overview, alerts: [{ date: "2026-10-11", weekday: "Sunday", kind: "storm", title: "Tropical Storm Odalys expected Sunday", detail: "", stores: ["Orlando"] }] }),
      "GET /api/me": () => fx.planner,
    });
    open("/");
    expect(await screen.findByText(/2 moves are drafted for tropical storm odalys, protecting/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Review the storm response" })).toHaveAttribute("href", "/response");
  });
});
