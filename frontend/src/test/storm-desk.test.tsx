import { QueryClient } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import App from "../App";
import * as fx from "./fixtures";
import { problem, serve } from "./server";

const quiet = () => new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: 0 } } });
const open = (path = "/storm-desk") =>
  render(<MemoryRouter initialEntries={[path]}><App client={quiet()} /></MemoryRouter>);

const plan = {
  answered: true,
  plan: ["Heavy rain is expected in Tampa on Saturday.", "Review TR-AAAAAAAAAA first."],
  steps: [{ what: "Overview", result: "8 urgent, 14 waiting" }, { what: "Pending transfers", result: "3 transfers" }],
  transfers: [fx.transfers[0]],
  message: null,
};

describe("Storm desk", () => {
  it("makes a plan, shows the moves it refers to and what it checked", async () => {
    const user = userEvent.setup();
    const server = serve({ "POST /api/storm-desk": () => plan });
    open();
    await user.type(screen.getByLabelText("What do you need a plan for?"), "Prepare Florida for Sunday's storm");
    await user.click(screen.getByRole("button", { name: "Make a plan" }));

    expect(await screen.findByRole("heading", { name: "Suggested plan" })).toBeInTheDocument();
    expect(screen.getByText("Heavy rain is expected in Tampa on Saturday.")).toBeInTheDocument();
    expect(screen.getByText(/Nothing has changed/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /1 move the plan refers to/ })).toBeInTheDocument();
    expect(screen.getByText("What storm desk checked (2)")).toBeInTheDocument();
    expect(server.calls.find((c) => c.path === "/api/storm-desk")?.body).toEqual({ goal: "Prepare Florida for Sunday's storm" });
  });

  it("runs a suggested question with one click", async () => {
    const user = userEvent.setup();
    serve({ "POST /api/storm-desk": () => plan });
    open();
    await user.click(screen.getByRole("button", { name: "Which stores need stock first this week?" }));
    expect(await screen.findByRole("heading", { name: "Suggested plan" })).toBeInTheDocument();
  });

  it("explains when storm desk is not available, in plain words", async () => {
    const user = userEvent.setup();
    serve({ "POST /api/storm-desk": () => ({ answered: false, plan: [], steps: [], transfers: [], message: "Storm desk needs the live workspace. It isn't available with sample data." }) });
    open();
    await user.type(screen.getByLabelText("What do you need a plan for?"), "Prepare Florida");
    await user.click(screen.getByRole("button", { name: "Make a plan" }));
    expect(await screen.findByText(/needs the live workspace/)).toBeInTheDocument();
  });

  it("shows a friendly error and a retry when the request fails", async () => {
    const user = userEvent.setup();
    serve({ "POST /api/storm-desk": () => problem(429, "slow_down", "Storm desk has been asked a lot. Wait a minute, then try again.") });
    open();
    await user.type(screen.getByLabelText("What do you need a plan for?"), "Prepare Florida");
    await user.click(screen.getByRole("button", { name: "Make a plan" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("asked a lot");
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("is linked from Transfers and never uses technical words", async () => {
    serve({ "POST /api/storm-desk": () => plan });
    open("/transfers");
    const link = await screen.findByRole("link", { name: "Get a plan from storm desk" });
    expect(link).toHaveAttribute("href", "/storm-desk");
    const main = screen.getByRole("main");
    expect(within(main).queryByText(/\b(sql|databricks|model|api|warehouse)\b/i)).toBeNull();
  });
});
