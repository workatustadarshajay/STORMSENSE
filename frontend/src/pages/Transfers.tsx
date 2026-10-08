import { CheckCircle2, Info, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { DecisionResult, Transfer } from "../api/client";
import { useDecide, useMe, usePending } from "../api/hooks";
import { Dialog } from "../components/Dialog";
import { Empty, QueryView } from "../components/StateViews";
import { TransferCard } from "../components/TransferCard";
import { plural } from "../lib/format";

type Action = "approve" | "reject";

function DecisionDialog({ action, picked, onClose, onDone }: { action: Action | null; picked: Transfer[]; onClose: () => void; onDone: (r: DecisionResult) => void }) {
  const decide = useDecide();
  const [text, setText] = useState("");
  const approve = action === "approve";
  const ids = picked.map((t) => t.id);
  const shown = picked.slice(0, 4);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (decide.isPending) return; // a double-click does nothing
    decide.mutate(approve ? { action: "approve", ids, note: text.trim() } : { action: "reject", ids, reason: text.trim() }, { onSuccess: onDone });
  }

  return (
    <Dialog open={action !== null} onClose={onClose} title={approve ? `Approve ${plural(picked.length, "transfer")}?` : `Reject ${plural(picked.length, "transfer")}?`}>
      <form onSubmit={submit} className="mt-3">
        <p className="text-ink-soft">{approve ? "The stores will be told to start moving this stock." : "The stores won't be asked to move this stock."}</p>
        <ul className="mt-4 grid gap-1.5 border-l-4 border-line pl-4 font-semibold">
          {shown.map((t) => (
            <li key={t.id}>{t.headline}</li>
          ))}
          {picked.length > shown.length && <li className="text-muted">and {picked.length - shown.length} more</li>}
        </ul>
        <label className="mt-5 block">
          <span className="font-bold">{approve ? "Add a note (optional)" : "Why are you rejecting? (required)"}</span>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={280}
            rows={3}
            required={!approve}
            minLength={approve ? undefined : 3}
            className="mt-1.5 w-full rounded-xl border border-line bg-white p-3"
          />
        </label>
        {decide.isError && (
          <p role="alert" className="mt-3 rounded-xl bg-signal-tint p-3 text-sm font-semibold text-signal-deep">
            {decide.error.message}
          </p>
        )}
        <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button type="button" onClick={onClose} className="min-h-12 rounded-xl border border-line px-5 font-bold hover:bg-mist">
            Cancel
          </button>
          <button
            type="submit"
            disabled={decide.isPending}
            className={`min-h-12 rounded-xl px-6 font-extrabold text-white disabled:opacity-60 ${approve ? "bg-teal hover:bg-teal-deep" : "bg-signal-deep hover:bg-signal"}`}
          >
            {decide.isPending ? "Working…" : approve ? "Approve" : "Reject"}
          </button>
        </div>
      </form>
    </Dialog>
  );
}

function Group({ title, items, selectable, selected, toggle, selectAll }: {
  title: string; items: Transfer[]; selectable: boolean; selected: Set<string>; toggle: (id: string) => void; selectAll: () => void;
}) {
  if (!items.length) return null;
  const allIn = items.every((t) => selected.has(t.id));
  return (
    <section aria-labelledby={`g-${title}`} className="mt-8">
      <div className="flex items-end justify-between gap-3">
        <h2 id={`g-${title}`} className="text-2xl font-extrabold">
          {title} <span className="text-muted">({items.length})</span>
        </h2>
        {selectable && (
          <button type="button" onClick={selectAll} className="min-h-11 rounded-xl px-3 font-bold text-teal-deep underline underline-offset-4">
            {allIn ? "Clear these" : "Select all"}
          </button>
        )}
      </div>
      <div className="mt-3 grid gap-3">
        {items.map((t) => (
          <TransferCard key={t.id} t={t} selectable={selectable} selected={selected.has(t.id)} onToggle={() => toggle(t.id)} />
        ))}
      </div>
    </section>
  );
}

export default function Transfers() {
  const me = useMe();
  const pending = usePending();
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [action, setAction] = useState<Action | null>(null);
  const [result, setResult] = useState<DecisionResult | null>(null);
  const canDecide = me.data?.can_approve ?? false;

  const rows = useMemo(() => pending.data ?? [], [pending.data]);
  // Forget selections that someone else just handled.
  useEffect(() => {
    setSelected((s) => {
      const live = new Set(rows.map((t) => t.id));
      const next = new Set([...s].filter((id) => live.has(id)));
      return next.size === s.size ? s : next;
    });
  }, [rows]);

  const toggle = (id: string) =>
    setSelected((s) => {
      const next = new Set(s);
      if (!next.delete(id)) next.add(id);
      return next;
    });
  const toggleGroup = (items: Transfer[]) =>
    setSelected((s) => {
      const next = new Set(s);
      const all = items.every((t) => next.has(t.id));
      items.forEach((t) => (all ? next.delete(t.id) : next.add(t.id)));
      return next;
    });
  const picked = rows.filter((t) => selected.has(t.id));

  return (
    <>
      <h1 className="text-4xl font-extrabold">Transfers</h1>
      <p className="mt-1 text-muted">Moves that keep shelves full before the weather hits.</p>

      {me.data && !canDecide && (
        <p className="mt-5 flex items-start gap-2.5 rounded-2xl bg-rain-tint p-4 font-semibold text-rain">
          <Info className="mt-0.5 size-5 shrink-0" aria-hidden />
          You can look at transfers, but only planners can approve or reject them.
        </p>
      )}

      {result && (
        <div role="status" className="mt-5 flex items-start gap-3 rounded-2xl bg-teal-tint p-4 text-teal-deep">
          <CheckCircle2 className="mt-0.5 size-6 shrink-0" aria-hidden />
          <div className="flex-1">
            <p className="font-extrabold">{result.message}</p>
            {result.changed.length > 0 && (
              <Link to="/history" className="text-sm font-bold underline underline-offset-4">
                See it in history
              </Link>
            )}
          </div>
          <button type="button" onClick={() => setResult(null)} aria-label="Dismiss message" className="grid size-11 place-items-center rounded-xl hover:bg-white/60">
            <X className="size-5" aria-hidden />
          </button>
        </div>
      )}

      <QueryView
        query={pending}
        isEmpty={(d) => d.length === 0}
        empty={
          <div className="mt-8">
            <Empty title="You're all caught up" action={<Link to="/stores" className="inline-flex min-h-12 items-center rounded-xl bg-ink px-5 font-bold text-white">See store forecasts</Link>}>
              No transfers are waiting for a decision.
            </Empty>
          </div>
        }
      >
        {(data) => (
          <>
            <Group
              title="Urgent"
              items={data.filter((t) => t.urgency === "URGENT")}
              selectable={canDecide}
              selected={selected}
              toggle={toggle}
              selectAll={() => toggleGroup(data.filter((t) => t.urgency === "URGENT"))}
            />
            <Group
              title="This week"
              items={data.filter((t) => t.urgency !== "URGENT")}
              selectable={canDecide}
              selected={selected}
              toggle={toggle}
              selectAll={() => toggleGroup(data.filter((t) => t.urgency !== "URGENT"))}
            />
          </>
        )}
      </QueryView>

      {picked.length > 0 && (
        <div
          role="region"
          aria-label="Selected transfers"
          className="fixed inset-x-3 bottom-[calc(4.75rem+env(safe-area-inset-bottom))] z-20 mx-auto flex max-w-2xl items-center gap-3 rounded-2xl bg-ink p-3 text-white shadow-2xl lg:bottom-6 lg:left-[calc(16rem+0.75rem)]"
        >
          <p className="flex-1 pl-2 font-bold">{picked.length} selected</p>
          <button type="button" onClick={() => setAction("reject")} className="min-h-12 rounded-xl border border-white/30 px-4 font-bold hover:bg-white/10">
            Reject
          </button>
          <button type="button" onClick={() => setAction("approve")} className="min-h-12 rounded-xl bg-glow px-5 font-extrabold text-ink hover:bg-white">
            Approve {picked.length}
          </button>
        </div>
      )}

      <DecisionDialog
        action={action}
        picked={picked}
        onClose={() => setAction(null)}
        onDone={(r) => {
          setResult(r);
          setSelected(new Set());
          setAction(null);
        }}
      />
    </>
  );
}
