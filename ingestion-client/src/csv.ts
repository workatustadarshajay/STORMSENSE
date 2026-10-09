/** The header names of a CSV file. Quoted names with commas are not handled; the guide says so. */
export const headersOf = (text: string): string[] =>
  (text.replace(/^﻿/, "").split(/\r?\n/)[0] ?? "").split(",").map((h) => h.trim()).filter(Boolean);

/** Pairs each StormSense column with a file column whose name matches, ignoring case and extra spaces. */
export const autoMatch = (columns: string[], headers: string[]): Record<string, string> => {
  const norm = (s: string) => s.trim().toLowerCase().replace(/[\s_]+/g, " ");
  const found: Record<string, string> = {};
  for (const c of columns) {
    const hit = headers.find((h) => norm(h) === norm(c));
    if (hit) found[c] = hit;
  }
  return found;
};
