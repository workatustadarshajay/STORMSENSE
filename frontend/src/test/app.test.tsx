import { QueryClient } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import App from "../App";
import { makeQueryClient } from "../api/hooks";
import * as fx from "./fixtures";
import { problem, serve } from "./server";

const quiet = () => new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: 0 } } });
function open(path = "/", client: ReturnType<typeof makeQueryClient> = quiet()) {
  return render(<MemoryRouter initialEntries={[path]}><App client={client} /></MemoryRouter>);
}
const BANNED = /\b(sql|delta|databricks|genie|mlflow|warehouse|sku|mape|wape|model|api)\b/i;

describe("Today", () => {
  it("greets by name and shows the three numbers and one button", async () => {
    serve();
    open("/");
    expect(await screen.findByRole("heading", { level: 1, name: /Good (morning|afternoon|evening), Ava/ })).toBeInTheDocument();
    const glance = screen.getByRole("region", { name: "Today at a glance" });
    expect(within(glance).getByText("urgent transfers").previousSibling).toHaveTextContent("2");
    expect(within(glance).getByText("stores running low").previousSibling).toHaveTextContent("4");
    expect(within(glance).getByText("storm expected")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Review transfers" })).toHaveAttribute("href", "/transfers");
  });
});

describe("Transfers", () => {
  it("groups by urgency and reads like sentences", async () => {
    serve();
    open("/transfers");
    expect(await screen.findByRole("heading", { name: "Move 54 1000W generators from Jacksonville to Orlando" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Urgent \(2\)/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /This week \(1\)/ })).toBeInTheDocument();
    expect(screen.getByText("Keeps shelves above the safe level")).toBeInTheDocument();
  });

  it("approves several: select, confirm, then a clear result", async () => {
    const user = userEvent.setup();
    const server = serve();
    open("/transfers");
    await user.click(await screen.findByRole("checkbox", { name: /Move 54/ }));
    await user.click(screen.getByRole("checkbox", { name: /Move 31/ }));
    const bar = screen.getByRole("region", { name: "Selected transfers" });
    expect(within(bar).getByText("2 selected")).toBeInTheDocument();
    await user.click(within(bar).getByRole("button", { name: "Approve 2" }));

    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByRole("heading", { name: "Approve 2 transfers?" })).toBeInTheDocument();
    await user.type(within(dialog).getByLabelText(/Add a note/), "Trucks are booked");
    await user.click(within(dialog).getByRole("button", { name: "Approve" }));

    expect(await screen.findByText("2 transfers approved.")).toBeInTheDocument();
    const post = server.calls.find((c) => c.method === "POST");
    expect(post?.path).toBe("/api/transfers/approve");
    expect(post?.body).toEqual({ ids: ["TR-AAAAAAAAAA", "TR-BBBBBBBBBB"], note: "Trucks are booked" });
    expect(screen.queryByText("2 selected")).not.toBeInTheDocument();
  });

  it("says plainly when someone else already handled one", async () => {
    const user = userEvent.setup();
    serve({ "POST /api/transfers/approve": (b) => fx.decided((b as { ids: string[] }).ids, ["TR-BBBBBBBBBB"]) });
    open("/transfers");
    await user.click(await screen.findByRole("checkbox", { name: /Move 54/ }));
    await user.click(screen.getByRole("checkbox", { name: /Move 31/ }));
    await user.click(screen.getByRole("button", { name: "Approve 2" }));
    await user.click(within(await screen.findByRole("dialog")).getByRole("button", { name: "Approve" }));
    expect(await screen.findByText("1 transfer approved. 1 was already handled by someone else.")).toBeInTheDocument();
  });

  it("a double-click on Approve sends one request", async () => {
    const user = userEvent.setup();
    let release: () => void = () => {};
    const gate = new Promise<void>((r) => (release = r));
    const server = serve({ "POST /api/transfers/approve": () => gate.then(() => fx.decided(["TR-AAAAAAAAAA"])) });
    open("/transfers");
    await user.click(await screen.findByRole("checkbox", { name: /Move 54/ }));
    await user.click(screen.getByRole("button", { name: "Approve 1" }));
    const confirm = within(await screen.findByRole("dialog")).getByRole("button", { name: "Approve" });
    await user.dblClick(confirm);
    release();
    await screen.findByText("1 transfer approved.");
    expect(server.calls.filter((c) => c.method === "POST")).toHaveLength(1);
  });

  it("rejecting needs a reason and records it", async () => {
    const user = userEvent.setup();
    const server = serve();
    open("/transfers");
    await user.click(await screen.findByRole("checkbox", { name: /Move 55/ }));
    await user.click(screen.getByRole("button", { name: "Reject" }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByRole("button", { name: "Reject" })).toBeDisabled();
    await user.selectOptions(within(dialog).getByRole("combobox"), "STORE_CLOSED");
    await user.type(within(dialog).getByLabelText(/Anything to add/), "Store is closed");
    await user.click(within(dialog).getByRole("button", { name: "Reject" }));
    await screen.findByText("1 transfer rejected.");
    expect(server.calls.find((c) => c.method === "POST")?.body).toEqual({ ids: ["TR-CCCCCCCCCC"], reason: "Store is closed", reason_code: "STORE_CLOSED" });
  });

  it("viewers can look but not decide", async () => {
    serve({ "GET /api/me": () => fx.viewer });
    open("/transfers");
    await screen.findByRole("heading", { name: /Move 54/ });
    expect(screen.queryAllByRole("checkbox")).toHaveLength(0);
    expect(screen.getByText(/only planners can approve or reject/)).toBeInTheDocument();
  });

  it("shows the server's explanation if a decision is refused", async () => {
    const user = userEvent.setup();
    serve({ "POST /api/transfers/approve": () => problem(403, "read_only", "Your account can view transfers but not approve or reject them.") });
    open("/transfers");
    await user.click(await screen.findByRole("checkbox", { name: /Move 54/ }));
    await user.click(screen.getByRole("button", { name: "Approve 1" }));
    await user.click(within(await screen.findByRole("dialog")).getByRole("button", { name: "Approve" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("can view transfers but not approve");
  });
});

describe("states", () => {
  it("shows a loading state first", () => {
    serve({ "GET /api/transfers?status=PENDING": () => new Promise(() => {}) });
    open("/transfers");
    expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
  });

  it("explains an empty list and points to the next step", async () => {
    serve({ "GET /api/transfers?status=PENDING": () => [] });
    open("/transfers");
    expect(await screen.findByText("You're all caught up")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "See store forecasts" })).toBeInTheDocument();
  });

  it("shows a friendly waiting state while data wakes up", async () => {
    serve({ "GET /api/overview": () => problem(503, "warming_up", "Getting things ready.") });
    open("/", makeQueryClient());
    expect(await screen.findByText("Getting things ready")).toBeInTheDocument();
  });

  it("offers a retry on errors", async () => {
    const user = userEvent.setup();
    let fail = true;
    serve({ "GET /api/history": () => (fail ? problem(502, "unavailable", "We couldn't load that right now. Please try again.") : fx.history) });
    open("/history");
    expect(await screen.findByRole("alert")).toHaveTextContent("We couldn't load that right now");
    fail = false;
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("Approved")).toBeInTheDocument();
  });

  it("asks to sign in again when the session is gone", async () => {
    serve({ "GET /api/overview": () => problem(401, "signed_out", "Please sign in again to continue.") });
    open("/");
    expect(await screen.findByText("Please sign in again")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reload" })).toBeInTheDocument();
  });
});

describe("Stores, Ask and History", () => {
  it("opens on the store in the most trouble and marks when it runs low", async () => {
    serve();
    open("/stores");
    expect(await screen.findByText("Runs low Thursday")).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Store" })).toHaveValue("S01");
    expect(screen.getByText(/lifting demand/)).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /Thursday 6 \(runs low\)/ })).toBeInTheDocument();
  });

  it("switches store", async () => {
    const user = userEvent.setup();
    serve();
    open("/stores");
    await screen.findByText("Runs low Thursday");
    await user.selectOptions(screen.getByRole("combobox", { name: "Store" }), "S04");
    expect(await screen.findByText("Extra stock")).toBeInTheDocument();
  });

  it("answers in a sentence and a table", async () => {
    const user = userEvent.setup();
    serve();
    open("/ask");
    await user.click(await screen.findByRole("button", { name: "Which stores will run out of generators this week?" }));
    expect(await screen.findByText(/2 stores will run low on generators/)).toBeInTheDocument();
    const table = screen.getByRole("table");
    expect(within(table).getByText("Tampa")).toBeInTheDocument();
  });

  it("falls back kindly", async () => {
    const user = userEvent.setup();
    serve({ "POST /api/ask": () => ({ answered: false, answer: "I couldn't answer that one. Try asking about stores, products or transfers.", table: null }) });
    open("/ask");
    await user.type(await screen.findByLabelText("Your question"), "What is the meaning of life?");
    await user.click(screen.getByRole("button", { name: "Ask" }));
    expect(await screen.findByText(/Try asking about stores/)).toBeInTheDocument();
  });

  it("lists past decisions with who made them", async () => {
    serve();
    open("/history");
    expect(await screen.findByText(/Ava Planner on/)).toBeInTheDocument();
    expect(screen.getByText(/Jordan Admin on/)).toBeInTheDocument();
    expect(screen.getByText("“Truck unavailable”")).toBeInTheDocument();
  });
});

describe("plain language", () => {
  it.each(["/", "/transfers", "/stores", "/ask", "/history"])("%s never shows technical words", async (path) => {
    serve();
    const { container } = open(path);
    await waitFor(() => expect(screen.queryByRole("status", { busy: true })).not.toBeInTheDocument());
    await screen.findByRole("heading", { level: 1 });
    const labels = [...container.querySelectorAll("[aria-label],[aria-labelledby],[title],[placeholder]")].map(
      (el) => el.getAttribute("aria-label") ?? el.getAttribute("title") ?? el.getAttribute("placeholder") ?? "",
    );
    const visible = [container.textContent ?? "", ...labels].join(" ");
    expect(visible.match(BANNED)).toBeNull();
  });
});
