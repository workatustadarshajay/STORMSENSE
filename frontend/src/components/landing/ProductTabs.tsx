import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";

// A working preview of the planner screens, built from the same sample figures the app shows.
const TABS = ["Today", "Transfers", "Stores", "Ask", "History"] as const;
type Tab = (typeof TABS)[number];

function Stat({ value, label, tone }: { value: string; label: string; tone: string }) {
  return (
    <div className="rounded-2xl bg-mist p-4">
      <p className={`text-3xl font-extrabold ${tone}`}>{value}</p>
      <p className="mt-1 text-sm text-muted">{label}</p>
    </div>
  );
}

function TodayPanel() {
  return (
    <div className="grid gap-4">
      <div className="grid grid-cols-3 gap-3">
        <Stat value="7" label="urgent transfers" tone="text-[#b3321f]" />
        <Stat value="5" label="stores running low" tone="text-ink" />
        <Stat value="Thu" label="heat wave expected" tone="text-[#7a4a00]" />
      </div>
      <div className="rounded-2xl border border-line p-4">
        <p className="text-sm font-semibold text-muted">Next weather alert</p>
        <p className="mt-1 font-bold">Heat Dome Sol, Thursday</p>
        <p className="text-sm text-muted">Houston, Dallas and Austin in Texas</p>
      </div>
      <span className="inline-flex w-fit items-center rounded-xl bg-ink px-5 py-3 font-bold text-white">Review transfers</span>
    </div>
  );
}

const MOVES = [
  { title: "Move 54 1000W generators from Jacksonville to Orlando", reason: "Tropical Storm Odalys is expected on Sunday. Orlando will sell about 56 and has 19.", state: "Pending" },
  { title: "Move 130 20x30 tarps from Jacksonville to Tampa", reason: "Tampa will sell about 135 this week and has 47.", state: "Pending" },
  { title: "Move 31 1000W generators from Miami to Tampa", reason: "Tampa runs low on Saturday.", state: "Pending" },
];

function TransfersPanel() {
  const [approved, setApproved] = useState<number[]>([]);
  return (
    <ul className="grid gap-3">
      {MOVES.map((m, i) => {
        const done = approved.includes(i);
        return (
          <li key={m.title} className="rounded-2xl border border-line p-4">
            <p className="font-bold leading-snug">{m.title}</p>
            <p className="mt-1 text-sm text-muted">{m.reason}</p>
            <div className="mt-3 flex items-center gap-3">
              <button
                type="button"
                disabled={done}
                onClick={() => setApproved((a) => [...a, i])}
                className="min-h-10 rounded-xl bg-teal px-4 text-sm font-bold text-white transition-colors hover:bg-teal-deep disabled:bg-line disabled:text-muted"
              >
                {done ? "Approved" : "Approve"}
              </button>
              <span className="text-xs font-semibold text-muted">{done ? "Recorded" : m.state}</span>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function StoresPanel() {
  const rows = [
    { store: "Orlando", product: "1000W generators", when: "Thursday", short: 53, width: 78 },
    { store: "Tampa", product: "1000W generators", when: "Saturday", short: 44, width: 62 },
  ];
  return (
    <div className="grid gap-4">
      {rows.map((r) => (
        <div key={r.store} className="rounded-2xl border border-line p-4">
          <div className="flex items-baseline justify-between">
            <p className="font-bold">{r.store}</p>
            <p className="text-sm font-semibold text-[#b3321f]">Runs low {r.when}</p>
          </div>
          <p className="text-sm text-muted">{r.product}</p>
          <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-mist">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${r.width}%` }}
              transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
              className="h-full rounded-full bg-[#b3321f]"
            />
          </div>
          <p className="mt-2 text-xs text-muted">{r.short} units short this week</p>
        </div>
      ))}
    </div>
  );
}

const QUESTION = "Which stores will run out of generators this week?";

function AskPanel() {
  const reduce = useReducedMotion();
  const [typed, setTyped] = useState(reduce ? QUESTION.length : 0);
  const done = typed >= QUESTION.length;

  useEffect(() => {
    if (reduce || typed >= QUESTION.length) return;
    const t = setTimeout(() => setTyped((n) => n + 1), 38);
    return () => clearTimeout(t);
  }, [typed, reduce]);

  return (
    <div className="grid gap-4">
      <div className="ml-auto max-w-[85%] rounded-2xl rounded-tr-md bg-ink px-4 py-3 font-semibold text-white">
        {QUESTION.slice(0, typed)}
        {!done && <span aria-hidden className="ml-0.5 inline-block w-[2px] animate-pulse bg-white align-middle">&nbsp;</span>}
      </div>
      <AnimatePresence>
        {done && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="rounded-2xl border border-line p-4">
            <p className="font-bold">2 stores will run low on 1000W generators this week, starting with Orlando on Thursday.</p>
            <table className="mt-4 w-full text-left text-sm">
              <thead className="text-muted">
                <tr>
                  <th className="py-1.5 font-semibold">Store</th>
                  <th className="py-1.5 font-semibold">Runs low</th>
                  <th className="py-1.5 text-right font-semibold">Units short</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-t border-line">
                  <td className="py-2">Orlando</td>
                  <td className="py-2">Thursday</td>
                  <td className="py-2 text-right font-bold">53</td>
                </tr>
                <tr className="border-t border-line">
                  <td className="py-2">Tampa</td>
                  <td className="py-2">Saturday</td>
                  <td className="py-2 text-right font-bold">44</td>
                </tr>
              </tbody>
            </table>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function HistoryPanel() {
  const items = [
    { who: "Ava Planner", what: "Approved 2 moves", when: "sample history" },
    { who: "Jordan Admin", what: "Approved 1 move", when: "sample history" },
    { who: "Ava Planner", what: "Rejected 1 move", when: "sample history" },
  ];
  return (
    <ol className="relative grid gap-5 border-l-2 border-line pl-6">
      {items.map((it) => (
        <li key={it.what + it.when} className="relative">
          <span aria-hidden className="absolute -left-[31px] top-1.5 size-3 rounded-full bg-teal" />
          <p className="font-bold">{it.what}</p>
          <p className="text-sm text-muted">
            {it.who}, {it.when}
          </p>
        </li>
      ))}
      <li className="text-sm text-muted">A repeat approval is refused: "already handled by someone else".</li>
    </ol>
  );
}

const PANELS: Record<Tab, () => JSX.Element> = {
  Today: TodayPanel,
  Transfers: TransfersPanel,
  Stores: StoresPanel,
  Ask: AskPanel,
  History: HistoryPanel,
};

export default function ProductTabs() {
  const [tab, setTab] = useState<Tab>("Today");
  const base = useId();
  const refs = useRef<Record<string, HTMLButtonElement | null>>({});
  const Panel = PANELS[tab];

  function onKey(e: KeyboardEvent<HTMLDivElement>) {
    const i = TABS.indexOf(tab);
    const next = e.key === "ArrowRight" ? (i + 1) % TABS.length : e.key === "ArrowLeft" ? (i - 1 + TABS.length) % TABS.length : null;
    if (next === null) return;
    setTab(TABS[next]);
    refs.current[TABS[next]]?.focus();
  }

  return (
    <section id="product" aria-labelledby="product-h" className="bg-paper px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <h2 id="product-h" className="max-w-2xl text-3xl font-extrabold tracking-tight sm:text-4xl">
          Try the planner screens.
        </h2>
        <p className="mt-4 max-w-xl text-lg text-muted">Each screen uses the same sample figures as the app. Nothing here changes real data.</p>

        <div className="mt-12 grid gap-8 lg:grid-cols-[0.42fr_1fr]">
          <div role="tablist" aria-orientation="vertical" aria-label="Planner screens" onKeyDown={onKey} className="flex flex-row gap-2 overflow-x-auto lg:flex-col">
            {TABS.map((t) => (
              <button
                key={t}
                ref={(el) => {
                  refs.current[t] = el;
                }}
                id={`${base}-${t}`}
                role="tab"
                type="button"
                aria-selected={tab === t}
                aria-controls={`${base}-panel`}
                tabIndex={tab === t ? 0 : -1}
                onClick={() => setTab(t)}
                className={`relative min-h-12 shrink-0 rounded-2xl px-5 text-left font-bold transition-colors ${
                  tab === t ? "bg-ink text-white" : "text-ink hover:bg-mist"
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          <div id={`${base}-panel`} role="tabpanel" aria-labelledby={`${base}-${tab}`} className="min-h-[360px] rounded-3xl border border-line bg-mist p-6 shadow-[0_24px_60px_rgba(16,27,43,0.08)] sm:p-8">
            <div className="mb-5 flex items-center justify-between">
              <p className="text-lg font-extrabold">{tab}</p>
              <span className="rounded-full border border-line bg-paper px-2.5 py-0.5 text-xs font-semibold text-muted">Sample data</span>
            </div>
            <AnimatePresence mode="wait">
              <motion.div key={tab} initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }} transition={{ duration: 0.25 }}>
                <Panel />
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
