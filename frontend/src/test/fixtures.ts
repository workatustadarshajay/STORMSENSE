import type { AskResponse, DecisionResult, Me, Overview, StoreForecast, StoreSummary, Transfer } from "../api/client";

export const planner: Me = { email: "ava.planner@stormsense.test", name: "Ava Planner", role: "planner", can_approve: true, data_label: "sample" };
export const viewer: Me = { email: "sam.viewer@stormsense.test", name: "Sam Viewer", role: "viewer", can_approve: false, data_label: "sample" };

const generator = { id: "P01", name: "1000W generator", name_plural: "1000W generators" };
const tarp = { id: "P03", name: "20x30 tarp", name_plural: "20x30 tarps" };
const ref = (id: string, name: string) => ({ id, name });

const base = {
  confidence: "Medium" as const, sales_protected_usd: 18578, distance_miles: 125, runs_low_day: "Thursday", status: "PENDING" as const,
  created_at: "2026-10-08T06:00:00", reason: "Tropical Storm Odalys expected Sunday. Orlando will sell about 56 1000W generators this week and has 19.",
};

export const transfers: Transfer[] = [
  { ...base, id: "TR-AAAAAAAAAA", headline: "Move 54 1000W generators from Jacksonville to Orlando", product: generator, from_store: ref("S04", "Jacksonville"), to_store: ref("S01", "Orlando"), qty: 54, urgency: "URGENT" },
  { ...base, id: "TR-BBBBBBBBBB", headline: "Move 31 1000W generators from Miami to Tampa", product: generator, from_store: ref("S03", "Miami"), to_store: ref("S02", "Tampa"), qty: 31, urgency: "URGENT", confidence: "Low", sales_protected_usd: 6372 },
  { ...base, id: "TR-CCCCCCCCCC", headline: "Move 55 20x30 tarps from Jacksonville to Tampa", product: tarp, from_store: ref("S04", "Jacksonville"), to_store: ref("S02", "Tampa"), qty: 55, urgency: "NORMAL", confidence: "High", sales_protected_usd: 0 },
];

export const history: Transfer[] = [
  { ...transfers[0], id: "TR-DDDDDDDDDD", status: "APPROVED", decided_by: "ava.planner@stormsense.test", decided_at: "2026-10-06T15:10:00", note: "Route confirmed" },
  { ...transfers[1], id: "TR-EEEEEEEEEE", status: "REJECTED", decided_by: "jordan.admin@stormsense.test", decided_at: "2026-10-06T16:00:00", note: "Truck unavailable" },
];

export const overview: Overview = {
  urgent_transfers: 2, pending_transfers: 3, stores_at_risk: 4, as_of: "2026-10-07",
  next_alert: { date: "2026-10-11", weekday: "Sunday", kind: "storm", title: "Tropical Storm Odalys expected Sunday", detail: "Tampa and Orlando in Florida", stores: ["Tampa", "Orlando"] },
  alerts: [{ date: "2026-10-11", weekday: "Sunday", kind: "storm", title: "Tropical Storm Odalys expected Sunday", detail: "Tampa and Orlando in Florida", stores: ["Tampa", "Orlando"] }],
  next_action: { title: "Review 2 urgent transfers", detail: "Moving this stock protects about $25,000 in sales.", button: "Review transfers", path: "/transfers" },
};

export const stores: StoreSummary[] = [
  { id: "S01", name: "Orlando", city: "Orlando", region: "Florida", running_low: 4 },
  { id: "S04", name: "Jacksonville", city: "Jacksonville", region: "Florida", running_low: 0 },
];

const days = ["2026-10-08", "2026-10-09", "2026-10-10", "2026-10-11", "2026-10-12", "2026-10-13", "2026-10-14"];
const weekdays = ["Thursday", "Friday", "Saturday", "Sunday", "Monday", "Tuesday", "Wednesday"];
export const forecast = (store: StoreSummary): StoreForecast => ({
  store, as_of: "2026-10-07",
  weather: days.map((date, i) => ({ date, weekday: weekdays[i], condition: i === 3 ? "storm" : "clear", label: i === 3 ? "Storm" : "Clear", temp_max_f: 84, wind_max_mph: i === 3 ? 56 : 10, rain_in: 0 })),
  products: [{
    product: generator, days: days.map((date, i) => ({ date, weekday: weekdays[i], units: 6 + i })), total_units: 56, range_low: 28, range_high: 95,
    available: 19, status: store.running_low ? "RUNNING_LOW" : "EXTRA", runs_low_day: store.running_low ? "Thursday" : null,
    why: "Storm on Sunday, with winds up to 56 mph, is lifting demand for 1000W generators.",
  }],
});

export const answer: AskResponse = {
  answered: true, answer: "2 stores will run low on generators this week, starting with Orlando on Thursday.",
  table: { columns: ["Store", "Runs low"], rows: [["Orlando", "Thursday"], ["Tampa", "Saturday"]] },
};

export const decided = (ids: string[], skipped: string[] = []): DecisionResult => {
  const changed = ids.filter((i) => !skipped.includes(i));
  const parts = [changed.length ? `${changed.length} transfer${changed.length === 1 ? "" : "s"} approved.` : "", skipped.length ? `${skipped.length} ${skipped.length === 1 ? "was" : "were"} already handled by someone else.` : ""];
  return { action: "APPROVED", changed, skipped, message: parts.filter(Boolean).join(" ") };
};

export const whatIfResult = {
  answered: true,
  window: "Saturday to Monday",
  sentence: "A storm of strength 80 from Saturday to Monday would add about 1922 units of demand. Without moving stock, about $53,223 in sales would be lost. Moving about 595 units of stock would cover it.",
  normal_units: 1717, storm_units: 3639, extra_demand_units: 1922, extra_lost_usd: 53223, stock_to_move_units: 595,
  rows: [{ store: "Orlando", product: "1000W generator", normal_units: 25, storm_units: 52, on_hand: 18, extra_lost_usd: 13603.28 }],
  plan_change: {
    as_of: "2026-10-08", before_version: 5, before_time: "2026-10-09T04:55:20Z", now_version: 6, now_time: "2026-10-09T05:33:58Z",
    shortage_stores_before: 11, shortage_stores_now: 9, units_short_before: 652, units_short_now: 184,
    sentence: "The stock plan changed after the last daily run: 9 stores now show a shortage, compared with 11 before it.",
  },
  message: null,
};

export const planPlan = () => ({ answered: true, plan: ["Review the Tampa move."], steps: [], transfers: [], message: null });
