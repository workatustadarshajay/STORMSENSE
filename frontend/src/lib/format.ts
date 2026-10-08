export const money = (n: number) => `$${Math.round(n).toLocaleString("en-US")}`;

/** "2026-10-08" as a local date (no time zone surprises). */
export function parseDay(iso: string): Date {
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  return new Date(y, m - 1, d);
}

export const longDate = (d: Date) => d.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });
export const shortDay = (iso: string) => parseDay(iso).toLocaleDateString("en-US", { weekday: "short" });

export function when(iso: string | null | undefined): string {
  if (!iso) return "";
  return new Date(iso).toLocaleString("en-US", { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

export function greeting(name: string, now = new Date()): string {
  const h = now.getHours();
  const part = h < 12 ? "morning" : h < 18 ? "afternoon" : "evening";
  return `Good ${part}, ${name.split(" ")[0]}`;
}

/** "ava.planner@stormsense.test" -> "Ava Planner" */
export function personFromEmail(email: string | null | undefined): string {
  if (!email) return "Someone";
  return email.split("@")[0].split(/[._-]/).map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
}

export const plural = (n: number, one: string, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;
