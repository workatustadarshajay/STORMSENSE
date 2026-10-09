import { QueryClient } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import App from "../App";
import * as fx from "./fixtures";
import { serve } from "./server";

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
