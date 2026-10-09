import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const PAGES = [
  ["Today", "/"],
  ["Transfers", "/transfers"],
  ["Store forecast", "/stores"],
  ["Ask", "/ask"],
  ["History", "/history"],
  ["Storm desk", "/storm-desk"],
  ["What if", "/what-if"],
] as const;
const BANNED = /\b(sql|delta|databricks|genie|mlflow|warehouse|sku|mape|wape|model|api)\b/i;

/** Collects browser errors, which includes content-security-policy violations. */
function watchErrors(page: Page) {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  return errors;
}

async function headlineOf(page: Page, index: number) {
  const id = await page.getByRole("checkbox").nth(index).getAttribute("aria-labelledby");
  return page.locator(`[id="${id}"]`).innerText();
}

test("a planner approves two transfers and finds them in history", async ({ page, request }) => {
  const errors = watchErrors(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(/Good (morning|afternoon|evening), Ava/);
  await page.getByRole("link", { name: "Review transfers" }).click();
  await expect(page).toHaveURL(/\/transfers$/);

  const picked = [await headlineOf(page, 0), await headlineOf(page, 1)];
  await page.getByRole("checkbox").nth(0).check();
  await page.getByRole("checkbox").nth(1).check();
  await page.getByRole("button", { name: "Approve 2" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("heading", { name: "Approve 2 transfers?" })).toBeVisible();
  await dialog.getByRole("button", { name: "Approve" }).click();
  await expect(page.getByRole("status").filter({ hasText: "2 transfers approved." })).toBeVisible();
  for (const headline of picked) await expect(page.getByRole("heading", { name: headline })).toHaveCount(0);

  await page.goto("/history");
  for (const headline of picked) await expect(page.getByText(headline)).toBeVisible();
  const history: { headline: string; decided_by: string; status: string }[] = await (await request.get("/api/history")).json();
  const mine = history.filter((h) => picked.includes(h.headline));
  expect(mine).toHaveLength(2);
  expect(mine.every((h) => h.decided_by === "ava.planner@stormsense.test" && h.status === "APPROVED")).toBe(true);
  expect(errors).toEqual([]);
});

test("two people approving the same transfer: the second is told, nothing doubles", async ({ browser }) => {
  const [a, b] = await Promise.all([browser.newContext(), browser.newContext()]);
  const [pa, pb] = [await a.newPage(), await b.newPage()];
  await Promise.all([pa.goto("/transfers"), pb.goto("/transfers")]);
  const headline = await headlineOf(pa, 0);
  for (const p of [pa, pb]) await p.getByRole("checkbox", { name: headline }).check();

  await pa.getByRole("button", { name: "Approve 1" }).click();
  await pa.getByRole("dialog").getByRole("button", { name: "Approve" }).click();
  await expect(pa.getByText("1 transfer approved.")).toBeVisible();

  await pb.getByRole("button", { name: "Approve 1" }).click();
  await pb.getByRole("dialog").getByRole("button", { name: "Approve" }).click();
  await expect(pb.getByText("1 was already handled by someone else.")).toBeVisible();
  await expect(pb.getByText(/transfer approved\./)).toHaveCount(0);
  await a.close();
  await b.close();
});

test("a viewer can look but not decide", async ({ browser }) => {
  const ctx = await browser.newContext({ extraHTTPHeaders: { "X-Forwarded-Email": "sam.viewer@stormsense.test" } });
  const page = await ctx.newPage();
  await page.goto("/transfers");
  await expect(page.getByText(/only planners can approve or reject/)).toBeVisible();
  await expect(page.getByRole("checkbox")).toHaveCount(0);
  const refused = await page.request.post("/api/transfers/approve", { data: { ids: ["TR-0000000000"] }, headers: { "X-Requested-With": "stormsense" } });
  expect(refused.status()).toBe(403);
  await ctx.close();
});

test("Ask answers in a sentence and a table", async ({ page }) => {
  await page.goto("/ask");
  await page.getByRole("button", { name: "Which stores will run out of generators this week?" }).click();
  await expect(page.getByText(/will run low on 1000W generators this week/)).toBeVisible();
  expect(await page.getByRole("table").getByRole("row").count()).toBeGreaterThan(1);
});

test("the store forecast says when a product runs low", async ({ page }) => {
  await page.goto("/stores");
  await expect(page.getByText(/Runs low \w+day/).first()).toBeVisible();
  await expect(page.getByRole("list", { name: "Weather this week" }).getByRole("listitem")).toHaveCount(7);
});

for (const [name, path] of PAGES) {
  test(`${name}: accessible, plain-spoken and error-free`, async ({ page }) => {
    const errors = watchErrors(page);
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await page.waitForLoadState("networkidle");

    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "best-practice"]).analyze();
    const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(serious.map((v) => `${v.id}: ${v.nodes[0]?.html}`)).toEqual([]);

    const text = await page.locator("body").innerText();
    const labels = await page.locator("[aria-label]").evaluateAll((els) => els.map((e) => e.getAttribute("aria-label")));
    expect(`${text} ${labels.join(" ")}`.match(BANNED)).toBeNull();
    expect(errors).toEqual([]);
  });
}

test("the keyboard reaches everything: skip link first, focus is visible", async ({ page, isMobile }) => {
  test.skip(isMobile, "keyboard flow is for desktop");
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to content" })).toBeFocused();
  await page.keyboard.press("Enter");
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Review transfers" })).toBeFocused();
});

test("security headers ship with the app", async ({ request }) => {
  const res = await request.get("/");
  expect(res.headers()["content-security-policy"]).toContain("default-src 'self'");
  expect(res.headers()["x-frame-options"]).toBe("DENY");
});
