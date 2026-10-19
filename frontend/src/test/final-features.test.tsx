import { QueryClient } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";
import App from "../App";
import * as fx from "./fixtures";
import { serve } from "./server";

const quiet = () => new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: 0 } } });
function open(path: string) {
  return render(<MemoryRouter initialEntries={[path]}><App client={quiet()} /></MemoryRouter>);
}

const suggestion = {
  store: { id: "S01", name: "Orlando" },
  product: { id: "P01", name: "1000W generator", name_plural: "1000W generators" },
  stockout_day: "Saturday",
  shortfall_units: 0,
  shortfall_low: 0,
  shortfall_high: 39,
  pending_inbound: 54,
  order_units: 39,
  why: "Pending moves cover 54 units.",
};

const best = (weather: string) => ({
  weather,
  ranking: [{ product: { id: "P03", name: "20x30 tarp", name_plural: "20x30 tarps" }, units: 724, stores: 10 }],
  next_alert: "Heat Dome Sol expected Thursday",
  what_next: "Next alert: Heat Dome Sol expected Thursday. Usually follows it: 120-quart coolers.",
});

beforeEach(() => {
  window.localStorage.clear();
});

describe("Still short after these moves", () => {
  it("suggests a safety order and says nothing is placed", async () => {
    serve({ "GET /api/orders/suggested": () => [suggestion] });
    open("/transfers");
    const panel = await screen.findByRole("region", { name: "Still short after these moves" });
    expect(panel).toHaveTextContent("Order 39");
    expect(panel).toHaveTextContent("Nothing is ordered from here.");
    expect(panel).toHaveTextContent("Orlando: 1000W generators");
  });

  it("says so when pending moves cover every store", async () => {
    serve({ "GET /api/orders/suggested": () => [] });
    open("/transfers");
    expect(await screen.findByText(/The pending moves cover every store/)).toBeInTheDocument();
  });
});

describe("Lowest CO₂ first", () => {
  it("switches the toggle and says so", async () => {
    serve();
    open("/transfers");
    const toggle = await screen.findByRole("button", { name: "Lowest CO₂ first" });
    expect(toggle).toHaveAttribute("aria-pressed", "false");
    await userEvent.click(toggle);
    expect(screen.getByRole("button", { name: "Showing lowest CO₂ first" })).toHaveAttribute("aria-pressed", "true");
  });
});

describe("Best sellers by weather", () => {
  it("ranks products for the weather chosen, and shows what comes next", async () => {
    const server = serve({
      "GET /api/best-sellers?weather=heat": () => best("heat"),
      "GET /api/best-sellers?weather=wind": () => best("wind"),
    });
    open("/stores");
    const panel = await screen.findByRole("region", { name: "Best sellers by weather" });
    await waitFor(() => expect(panel).toHaveTextContent("20x30 tarps"));
    expect(panel).toHaveTextContent("What comes next:");

    await userEvent.click(screen.getByRole("button", { name: "Wind and storms" }));
    await waitFor(() => expect(server.calls.some((c) => c.path === "/api/best-sellers?weather=wind")).toBe(true));
    expect(screen.getByRole("button", { name: "Wind and storms" })).toHaveAttribute("aria-pressed", "true");
  });
});

describe("Since your last visit", () => {
  it("reports moves that are new and moves that are no longer waiting", async () => {
    const [first] = fx.transfers;
    window.localStorage.setItem("stormsense.seen-moves", JSON.stringify(["TR-GONE", first.id]));
    serve();
    open("/today");
    const banner = await screen.findByRole("status", { name: "Since your last visit" });
    expect(banner).toHaveTextContent("no longer waiting");
    expect(banner).toHaveTextContent("1 move no longer waiting");
  });

  it("stays quiet on the first visit", async () => {
    serve();
    open("/today");
    await screen.findByRole("heading", { level: 1, name: /Good (morning|afternoon|evening), Ava/ });
    expect(screen.queryByRole("status", { name: "Since your last visit" })).not.toBeInTheDocument();
    await waitFor(() => expect(window.localStorage.getItem("stormsense.seen-moves")).not.toBeNull());
  });
});
