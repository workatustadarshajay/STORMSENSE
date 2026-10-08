import { describe, expect, it } from "vitest";
import { greeting, money, personFromEmail, plural } from "./format";

describe("format", () => {
  it("formats money, names and plurals", () => {
    expect(money(18577.6)).toBe("$18,578");
    expect(personFromEmail("ava.planner@stormsense.test")).toBe("Ava Planner");
    expect(personFromEmail(null)).toBe("Someone");
    expect(plural(1, "transfer")).toBe("1 transfer");
    expect(plural(3, "transfer")).toBe("3 transfers");
  });
  it("greets by time of day", () => {
    expect(greeting("Ava Planner", new Date(2026, 9, 8, 7))).toBe("Good morning, Ava");
    expect(greeting("Ava Planner", new Date(2026, 9, 8, 13))).toBe("Good afternoon, Ava");
    expect(greeting("Ava Planner", new Date(2026, 9, 8, 20))).toBe("Good evening, Ava");
  });
});
