import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import App from "../App";
import { makeQueryClient } from "../api/hooks";

const open = (path: string) =>
  render(<MemoryRouter initialEntries={[path]}><App client={makeQueryClient()} /></MemoryRouter>);

describe("Landing page", () => {
  it("is the first screen at /, with a way into the planner", () => {
    open("/");
    expect(screen.getByRole("heading", { level: 1, name: "Move stock before the storm, not after." })).toBeInTheDocument();
    const links = screen.getAllByRole("link", { name: "Open today's plan" });
    expect(links.length).toBeGreaterThan(0);
    links.forEach((link) => expect(link).toHaveAttribute("href", "/today"));
    expect(screen.queryByRole("navigation", { name: "Main" })).not.toBeInTheDocument();
  });

  it("keeps the planner's Today screen at /today, inside the app shell", async () => {
    open("/today");
    expect((await screen.findAllByRole("navigation", { name: "Main" })).length).toBeGreaterThan(0);
    expect(screen.queryByRole("heading", { level: 1, name: "Move stock before the storm, not after." })).not.toBeInTheDocument();
  });
});
