import { useEffect, useMemo, useRef, useState } from "react";
import { usePending } from "../api/hooks";
import { plural } from "../lib/format";

const KEY = "stormsense.seen-moves";

/** Tells a planner what changed since they last opened Today: new moves, and moves no longer waiting. */
export function SinceLastVisit() {
  const pending = usePending();
  const ids = useMemo(() => pending.data?.map((t) => t.id), [pending.data]);
  const [news, setNews] = useState<{ added: number; gone: number } | null>(null);
  const checked = useRef(false);

  useEffect(() => {
    if (!ids || checked.current) return;
    checked.current = true;
    let seen: unknown = null;
    try {
      seen = JSON.parse(window.localStorage.getItem(KEY) ?? "null");
    } catch {
      seen = null;
    }
    if (Array.isArray(seen)) {
      const before = new Set(seen as string[]);
      const now = new Set(ids);
      const added = ids.filter((id) => !before.has(id)).length;
      const gone = (seen as string[]).filter((id) => !now.has(id)).length;
      if (added || gone) setNews({ added, gone });
    }
    try {
      window.localStorage.setItem(KEY, JSON.stringify(ids));
    } catch {
      /* private browsing: the banner just will not remember next time */
    }
  }, [ids]);

  if (!news) return null;
  return (
    <section role="status" aria-label="Since your last visit" className="mt-6 rounded-2xl border border-teal/40 bg-teal-tint p-4 text-sm">
      <strong>Since your last visit:</strong>{" "}
      {news.added > 0 ? `${plural(news.added, "new move")} waiting.` : "No new moves."}{" "}
      {news.gone > 0 ? `${plural(news.gone, "move")} no longer waiting, decided or covered.` : ""}
    </section>
  );
}
