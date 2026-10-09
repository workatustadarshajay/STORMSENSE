import { Link } from "react-router-dom";
import { Siren, Truck } from "lucide-react";
import type { Transfer } from "../api/client";
import { money } from "../lib/format";

const PIPS = { High: 3, Medium: 2, Low: 1 } as const;

export function Confidence({ level }: { level: Transfer["confidence"] }) {
  return (
    <span className="inline-flex items-center gap-1.5 font-semibold">
      <span aria-hidden className="flex gap-0.5">
        {[1, 2, 3].map((i) => (
          <span key={i} className={`size-2 rounded-full ${i <= PIPS[level] ? "bg-teal" : "bg-line"}`} />
        ))}
      </span>
      {level} confidence
    </span>
  );
}

export function Facts({ t }: { t: Transfer }) {
  return (
    <p className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1 text-sm text-ink-soft">
      <span>{t.sales_protected_usd > 0 ? `Protects about ${money(t.sales_protected_usd)} in sales` : "Keeps shelves above the safe level"}</span>
      <Confidence level={t.confidence} />
      {t.runs_low_day && <span>{t.to_store.name} runs low {t.runs_low_day}</span>}
    </p>
  );
}

function Route({ t }: { t: Transfer }) {
  return (
    <div aria-hidden className="mt-2 flex items-center gap-2 text-sm font-semibold text-muted">
      <span>{t.from_store.name}</span>
      <span className="relative h-px min-w-10 flex-1 bg-line">
        <Truck className="absolute -top-2.5 left-1/2 size-5 -translate-x-1/2 bg-paper px-0.5 text-teal" />
      </span>
      <span>{t.to_store.name}</span>
      <span className="text-xs font-medium">{t.distance_miles} mi</span>
      <span className="text-xs font-medium" title="A planning estimate: about 0.9 kg CO₂ per loaded truck-mile, with 200 units per truck.">
        about {Math.round(t.co2_kg)} kg CO₂
      </span>
    </div>
  );
}

export function TransferCard({ t, selectable, selected, onToggle }: { t: Transfer; selectable: boolean; selected: boolean; onToggle: () => void }) {
  const urgent = t.urgency === "URGENT";
  const titleId = `t-${t.id}`;
  return (
    <article
      className={`rounded-2xl border bg-paper transition-shadow ${urgent ? "border-l-[6px] border-line border-l-signal" : "border-l-[6px] border-line border-l-teal/50"} ${
        selected ? "ring-2 ring-teal" : ""
      }`}
    >
      <div className="flex gap-4 p-4 sm:p-5">
        {selectable && (
          <label className="-m-2 grid size-12 shrink-0 cursor-pointer place-items-center self-start">
            <input
              type="checkbox"
              checked={selected}
              onChange={onToggle}
              aria-labelledby={titleId}
              className="size-7 cursor-pointer accent-teal"
            />
          </label>
        )}
        <div className="min-w-0 flex-1">
          {urgent && (
            <p className="mb-1 inline-flex items-center gap-1.5 rounded-full bg-signal-tint px-2.5 py-0.5 text-sm font-bold text-signal-deep">
              <Siren className="size-4" aria-hidden /> Urgent
            </p>
          )}
          <h3 id={titleId} className="text-xl font-extrabold leading-snug">
            {t.headline}
          </h3>
          <Route t={t} />
          <p className="mt-3 text-ink-soft">{t.reason}</p>
          <Facts t={t} />
          <p className="mt-3 text-sm">
            <Link to={`/stores?store=${t.to_store.id}`} className="font-bold text-teal-deep underline underline-offset-4">
              See {t.to_store.name}'s forecast
            </Link>
          </p>
        </div>
      </div>
    </article>
  );
}
