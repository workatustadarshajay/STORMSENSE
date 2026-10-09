import { Link } from "react-router-dom";
import type { Overview } from "../api/client";
import { useMe, useOverview, useStores } from "../api/hooks";
import { QueryView } from "../components/StateViews";
import { greeting, longDate, plural, shortDay, parseDay } from "../lib/format";

const KIND = { storm: "Storm", heavy_rain: "Heavy rain", heat: "Heat wave" } as const;

function Figure({ value, label, hint, urgent }: { value: string | number; label: string; hint?: string; urgent?: boolean }) {
  return (
    <div className="px-3 py-1 text-center first:pl-0 last:pr-0 sm:px-6">
      <p className={`text-5xl font-extrabold leading-none tracking-tight sm:text-6xl ${urgent ? "text-signal" : "text-ink"}`}>{value}</p>
      <p className="mt-2 text-sm font-semibold leading-snug text-ink-soft">{label}</p>
      {hint && <p className="mt-1 text-xs leading-snug text-muted">{hint}</p>}
    </div>
  );
}

const BAR = { ready: "bg-teal", watch: "bg-heat", risk: "bg-signal" } as const;

function Readiness() {
  const stores = useStores();
  return (
    <section aria-labelledby="ready-h" className="mt-10">
      <h2 id="ready-h" className="text-xl font-extrabold">Storm readiness</h2>
      <p className="mt-1 text-sm text-muted">Share of each store's products with enough stock to last the storm and a safety margin.</p>
      <QueryView query={stores} rows={3}>
        {(list) => (
          <ul className="mt-4 space-y-3">
            {[...list].sort((a, b) => a.readiness - b.readiness).map((s) => {
              const tone = s.readiness >= 80 ? BAR.ready : s.readiness >= 50 ? BAR.watch : BAR.risk;
              return (
                <li key={s.id}>
                  <Link to={`/stores?store=${s.id}`} className="grid grid-cols-[6.5rem_1fr_auto] items-center gap-3 rounded-lg hover:opacity-90">
                    <span className="font-bold">{s.name}</span>
                    <span className="h-3 overflow-hidden rounded-full bg-line" role="img" aria-label={`${s.readiness} percent ready, ${s.readiness_label}`}>
                      <span className={`block h-full rounded-full ${tone}`} style={{ width: `${s.readiness}%` }} />
                    </span>
                    <span className="w-28 text-right text-sm font-extrabold">
                      {s.readiness}% <span className="font-semibold text-muted">· {s.readiness_label}</span>
                    </span>
                  </Link>
                  <p className="mt-0.5 pl-[6.5rem] text-xs text-muted">
                    {s.storm_days > 0 ? `${s.storm_days} day${s.storm_days === 1 ? "" : "s"} of storm or heavy rain ahead` : "No storm or heavy rain in the week ahead"}
                  </p>
                </li>
              );
            })}
          </ul>
        )}
      </QueryView>
    </section>
  );
}

function Body({ o, name }: { o: Overview; name: string }) {
  const worst = (["storm", "heavy_rain", "heat"] as const).find((k) => o.alerts.some((a) => a.kind === k));
  const alert = o.next_alert;
  return (
    <>
      <section data-sky={worst ?? "clear"} className="sky -mx-4 -mt-6 rounded-b-[2rem] px-6 pb-9 pt-8 lg:mx-0 lg:rounded-3xl lg:px-10 lg:py-12">
        <p className="text-sm font-semibold opacity-80">{longDate(new Date())}</p>
        <h1 className="mt-1 text-4xl font-extrabold sm:text-5xl">{greeting(name)}</h1>
        <p className="mt-6 text-2xl font-bold leading-tight">{o.next_action.title}</p>
        <p className="mt-1.5 opacity-90">{o.next_action.detail}</p>
      </section>

      <section aria-label="Today at a glance" className="settle mt-8 grid grid-cols-3 divide-x divide-line">
        <Figure value={o.urgent_transfers} urgent={o.urgent_transfers > 0} label={o.urgent_transfers === 1 ? "urgent transfer" : "urgent transfers"} />
        <Figure value={o.stores_at_risk} label={o.stores_at_risk === 1 ? "store running low" : "stores running low"} />
        {alert ? (
          <Figure value={shortDay(alert.date.toString())} label={`${KIND[alert.kind].toLowerCase()} expected`} hint={alert.detail} />
        ) : (
          <Figure value="None" label="weather alerts this week" />
        )}
      </section>

      <Readiness />

      <Link
        to={o.next_action.path}
        className="mt-10 flex min-h-14 items-center justify-center rounded-2xl bg-ink px-6 text-lg font-extrabold text-white transition-colors hover:bg-teal-deep"
      >
        {o.next_action.button}
      </Link>
      {o.pending_transfers > 0 && (
        <p className="mt-3 text-center text-sm text-muted">{plural(o.pending_transfers, "transfer")} waiting in total</p>
      )}
      {o.as_of && <p className="mt-8 text-center text-xs text-muted">Based on stock counted {longDate(parseDay(o.as_of.toString()))}</p>}
    </>
  );
}

export default function Today() {
  const me = useMe();
  const overview = useOverview();
  return (
    <QueryView query={overview} rows={2}>
      {(o) => <Body o={o} name={me.data?.name ?? "there"} />}
    </QueryView>
  );
}
