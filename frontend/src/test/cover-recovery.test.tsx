import { QueryClient } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import App from "../App";
import { serve } from "./server";

const quiet = () => new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: 0 } } });
const open = (path: string) => render(<MemoryRouter initialEntries={[path]}><App client={quiet()} /></MemoryRouter>);

const cover = {
  trigger: "Triggers when at least 2 stores in a region reach 39 mph wind or 3 inches of rain on the same forecast day.",
  cap_usd: 100000,
  note: "A simulation with illustrative thresholds. Not a quote and not a contract.",
  regions: [
    { region: "Florida", stores_hit: ["Orlando", "Tampa"], triggered: true, first_day: "2026-10-25", projected_lost_sales_usd: 42588.39, projected_short_units: 300, simulated_payout_usd: 42588.39 },
    { region: "Texas", stores_hit: [], triggered: false, first_day: null, projected_lost_sales_usd: 3672.9, projected_short_units: 20, simulated_payout_usd: 0 },
  ],
};

const recovery = {
  note: "The sample history has no decisions inside these storm windows.",
  events: [
    {
      event: { event_name: "Hurricane Marlow", start_date: "2026-09-14", end_date: "2026-09-18", stores: 4, lost_units: 1086, lost_usd: 171310, protected_units: 22, protected_usd: 2658, share_protected: 0.016 },
      unprotected_usd: 168652,
      stores_restocked: [],
    },
  ],
};

describe("Storm cover (simulation)", () => {
  it("shows which regions would trigger, and says it is not a contract", async () => {
    serve({ "GET /api/cover/simulation": () => cover });
    open("/cover");
    expect(await screen.findByRole("heading", { level: 1, name: "Storm cover (simulation)" })).toBeInTheDocument();
    expect(await screen.findByRole("region", { name: "Florida" })).toHaveTextContent("Would trigger");
    expect(screen.getByRole("region", { name: "Texas" })).toHaveTextContent("Would not trigger");
    expect(screen.getByText(/Not a quote and not a contract/)).toBeInTheDocument();
  });
});

describe("Past storm recovery", () => {
  it("shows what was lost, what was not protected, and says when restock is missing", async () => {
    serve({ "GET /api/recovery": () => recovery });
    open("/recovery");
    expect(await screen.findByRole("heading", { level: 2, name: "Hurricane Marlow" })).toBeInTheDocument();
    expect(screen.getByText("$168,652")).toBeInTheDocument();
    expect(screen.getByText(/No approved restock recorded/)).toBeInTheDocument();
  });

  it("is linked from business impact", async () => {
    serve({ "GET /api/impact": () => ({ source: "sample", as_of: "2026-10-14", headline: { protected_usd: 0, margin_usd: 0, trucking_usd: 0, net_usd: 0, co2_kg: 0, moves: 0, pending: 0, approved: 0, rejected: 0 }, assumptions: [], changes: { last_plan_at: null, moves_then: null, moves_now: 0 }, timeline: [] }) });
    open("/impact");
    expect(await screen.findByRole("link", { name: "Storm cover (simulation)" })).toHaveAttribute("href", "/cover");
    expect(screen.getByRole("link", { name: "Past storm recovery" })).toHaveAttribute("href", "/recovery");
  });
});
