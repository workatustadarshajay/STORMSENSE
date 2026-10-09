import { QueryClient } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import App from "../App";
import * as fx from "./fixtures";
import { problem, serve } from "./server";

const quiet = () => new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: 0 } } });
const open = (path: string) => render(<MemoryRouter initialEntries={[path]}><App client={quiet()} /></MemoryRouter>);

describe("What if a storm comes", () => {
  it("runs a scenario and shows the cost of doing nothing, labelled as an estimate", async () => {
    const user = userEvent.setup();
    const server = serve({ "POST /api/what-if": () => fx.whatIfResult });
    open("/what-if");
    await user.click(screen.getByRole("button", { name: "Run the storm" }));
    expect(await screen.findByText("$53,223")).toBeInTheDocument();
    expect(screen.getByText(/would add about 1922 units/)).toBeInTheDocument();
    expect(screen.getByText("Orlando")).toBeInTheDocument();
    expect(screen.getByText(/What changed in the stock plan/)).toBeInTheDocument();
    expect(screen.getByText(/estimates from the forecaster/)).toBeInTheDocument();
    const body = server.calls.find((c) => c.path === "/api/what-if")?.body as { strength: number; start_day: number; days: number; region: string | null };
    expect(body).toEqual({ strength: 70, start_day: 1, days: 2, region: null });
  });

  it("sends the slider, timing, length and region the planner chose", async () => {
    const user = userEvent.setup();
    const server = serve({ "POST /api/what-if": () => fx.whatIfResult });
    open("/what-if");
    await user.selectOptions(screen.getByRole("combobox", { name: "When it hits" }), "0");
    await user.selectOptions(screen.getByRole("combobox", { name: "How many days" }), "3");
    await user.selectOptions(screen.getByRole("combobox", { name: "Where" }), "Texas");
    await user.click(screen.getByRole("button", { name: "Run the storm" }));
    await screen.findByText("$53,223");
    expect(server.calls.find((c) => c.path === "/api/what-if")?.body).toEqual({ strength: 70, start_day: 0, days: 3, region: "Texas" });
  });

  it("explains that sample data cannot be simulated", async () => {
    const user = userEvent.setup();
    serve({ "POST /api/what-if": () => ({ answered: false, message: "The storm simulator needs the live workspace. It isn't available with sample data." }) });
    open("/what-if");
    await user.click(screen.getByRole("button", { name: "Run the storm" }));
    expect(await screen.findByText(/needs the live workspace/)).toBeInTheDocument();
  });

  it("shows a friendly error when the simulator is busy", async () => {
    const user = userEvent.setup();
    serve({ "POST /api/what-if": () => problem(429, "slow_down", "That's a lot of simulations. Wait a minute, then try again.") });
    open("/what-if");
    await user.click(screen.getByRole("button", { name: "Run the storm" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("a lot of simulations");
  });
});

describe("Rejecting a move asks for a reason", () => {
  it("keeps Reject disabled until a reason is chosen, then records it", async () => {
    const user = userEvent.setup();
    const server = serve({ "POST /api/transfers/reject": () => ({ action: "REJECTED", changed: [fx.transfers[0].id], skipped: [], message: "1 transfer rejected." }) });
    open("/transfers");
    await user.click(await screen.findByRole("checkbox", { name: /Move 54/ }));
    await user.click(screen.getByRole("button", { name: "Reject" }));
    const dialog = await screen.findByRole("dialog");
    const reject = () => dialog.querySelector("button[type=submit]") as HTMLButtonElement;
    expect(reject()).toBeDisabled();
    await user.selectOptions(dialog.querySelector("select") as HTMLSelectElement, "TRUCK_UNAVAILABLE");
    expect(reject()).toBeEnabled();
    await user.click(reject());
    await screen.findByText("1 transfer rejected.");
    const sent = server.calls.find((c) => c.path === "/api/transfers/reject")?.body as { reason_code: string };
    expect(sent.reason_code).toBe("TRUCK_UNAVAILABLE");
  });
});

describe("Storm desk shows the crew's debate", () => {
  it("lists each agent's turn", async () => {
    const user = userEvent.setup();
    serve({
      "POST /api/storm-desk": () => ({
        ...fx.planPlan(), debate: [
          { agent: "Forecaster", message: "Draft about Tampa." },
          { agent: "Risk checker", message: "This move leaves Miami short." },
          { agent: "Summary writer", message: "Review the Tampa move." },
        ],
      }),
    });
    open("/storm-desk");
    await user.type(screen.getByLabelText("What do you need a plan for?"), "Prepare Florida");
    await user.click(screen.getByRole("button", { name: "Make a plan" }));
    expect(await screen.findByText("How the crew reached this plan")).toBeInTheDocument();
    expect(screen.getByText("This move leaves Miami short.")).toBeInTheDocument();
    expect(screen.getByText("Risk checker")).toBeInTheDocument();
  });
});
