import { ChevronDown, Sparkles } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import type { StormDeskPlan } from "../api/client";
import { useStormDesk } from "../api/hooks";
import { ErrorState } from "../components/StateViews";
import { TransferCard } from "../components/TransferCard";
import { plural } from "../lib/format";

const SUGGESTIONS = [
  "Prepare Florida for Sunday's storm",
  "What should move before the heat wave in Texas?",
  "Which stores need stock first this week?",
];

function Result({ r }: { r: StormDeskPlan }) {
  const plan = r.plan ?? [];
  const transfers = r.transfers ?? [];
  const steps = r.steps ?? [];
  if (!r.answered) {
    return (
      <div role="status" className="rounded-2xl border border-dashed border-line bg-paper p-6">
        <p className="font-bold">{r.message ?? "Storm desk could not make a plan."}</p>
      </div>
    );
  }
  return (
    <div className="grid gap-5">
      <section aria-labelledby="plan-h" className="rounded-2xl border border-line bg-paper p-5 sm:p-6">
        <h2 id="plan-h" className="text-xl font-extrabold">Suggested plan</h2>
        <div className="mt-3 grid gap-2.5 text-[17px] leading-relaxed text-ink-soft">
          {plan.map((sentence, i) => (
            <p key={i}>{sentence}</p>
          ))}
        </div>
        <p className="mt-4 rounded-xl bg-teal-tint p-3 text-sm font-semibold text-teal-deep">
          Nothing has changed. Approve or reject these moves on the Transfers screen.
        </p>
      </section>

      {transfers.length > 0 && (
        <section aria-labelledby="moves-h">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <h2 id="moves-h" className="text-xl font-extrabold">
              {plural(transfers.length, "move")} the plan refers to
            </h2>
            <Link to="/transfers" className="min-h-11 rounded-xl px-3 font-bold text-teal-deep underline underline-offset-4">
              Open Transfers
            </Link>
          </div>
          <div className="mt-3 grid gap-3">
            {transfers.map((t) => (
              <TransferCard key={t.id} t={t} selectable={false} selected={false} onToggle={() => {}} />
            ))}
          </div>
        </section>
      )}

      {(r.debate ?? []).length > 0 && (
        <details className="rounded-2xl border border-line bg-paper p-4" open>
          <summary className="flex min-h-11 cursor-pointer items-center justify-between gap-2 font-bold">
            How the crew reached this plan
            <ChevronDown className="size-5" aria-hidden />
          </summary>
          <ol className="mt-3 grid gap-4">
            {(r.debate ?? []).map((turn, i) => (
              <li key={i} className="grid gap-1 border-l-4 border-teal/40 pl-4">
                <span className="text-sm font-extrabold uppercase tracking-wide text-teal-deep">{turn.agent}</span>
                <p className="text-ink-soft">{turn.message}</p>
              </li>
            ))}
          </ol>
        </details>
      )}

      {steps.length > 0 && (
        <details className="rounded-2xl border border-line bg-paper p-4">
          <summary className="flex min-h-11 cursor-pointer items-center justify-between gap-2 font-bold">
            What storm desk checked ({steps.length})
            <ChevronDown className="size-5" aria-hidden />
          </summary>
          <ol className="mt-3 grid gap-2 text-ink-soft">
            {steps.map((s, i) => (
              <li key={i} className="flex flex-wrap gap-x-2">
                <span className="font-semibold text-ink">{s.what}:</span> {s.result}
              </li>
            ))}
          </ol>
        </details>
      )}
    </div>
  );
}

export default function StormDesk() {
  const desk = useStormDesk();
  const [goal, setGoal] = useState("");
  const [asked, setAsked] = useState<string | null>(null);

  function ask(text: string) {
    const g = text.trim();
    if (g.length < 3 || desk.isPending) return;
    setAsked(g);
    desk.mutate(g);
  }

  return (
    <>
      <h1 className="flex items-center gap-3 text-4xl font-extrabold">
        <Sparkles className="size-8 text-teal" aria-hidden /> Storm desk
      </h1>
      <p className="mt-2 max-w-prose text-muted">
        Tell it what you are preparing for. It checks the forecasts, stock and pending moves, then suggests what to review first.
        It can't approve anything.
      </p>

      <form
        className="mt-6 grid gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          ask(goal);
        }}
      >
        <label className="grid gap-1.5">
          <span className="font-bold">What do you need a plan for?</span>
          <textarea
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            maxLength={500}
            rows={2}
            placeholder="For example: Prepare Florida for Sunday's storm"
            className="w-full rounded-2xl border border-line bg-paper p-4 text-lg"
          />
        </label>
        <div className="flex flex-wrap gap-2">
          <ul className="flex flex-wrap gap-2" aria-label="Suggestions">
            {SUGGESTIONS.map((s) => (
              <li key={s}>
                <button type="button" onClick={() => { setGoal(s); ask(s); }} className="min-h-11 rounded-2xl border border-line bg-paper px-4 py-2 text-left font-semibold hover:border-teal hover:bg-teal-tint">
                  {s}
                </button>
              </li>
            ))}
          </ul>
        </div>
        <button
          type="submit"
          disabled={desk.isPending || goal.trim().length < 3}
          className="min-h-14 rounded-2xl bg-ink px-6 text-lg font-extrabold text-white disabled:bg-line disabled:text-muted"
        >
          {desk.isPending ? "Checking the data…" : "Make a plan"}
        </button>
      </form>

      <div className="mt-8" aria-live="polite">
        {desk.isPending && (
          <p role="status" className="font-semibold text-ink-soft">
            Checking forecasts, stock and pending moves for “{asked}”. This takes up to a minute.
          </p>
        )}
        {desk.isError && <ErrorState error={desk.error} retry={() => asked && desk.mutate(asked)} />}
        {desk.isSuccess && <Result r={desk.data} />}
      </div>
    </>
  );
}
