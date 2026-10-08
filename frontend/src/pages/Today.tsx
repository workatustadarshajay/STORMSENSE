import { Link } from "react-router-dom";
import type { Overview } from "../api/client";
import { useMe, useOverview } from "../api/hooks";
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
