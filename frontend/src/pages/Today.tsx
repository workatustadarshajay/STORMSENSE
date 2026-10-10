import { Link, useSearchParams } from "react-router-dom";
import type { Overview, WeatherMode } from "../api/client";
import { useDemoAlert, useMarkdowns, useMe, useOverview, useStores } from "../api/hooks";
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

function WeatherSwitch({ mode, onChange }: { mode: WeatherMode; onChange: (m: WeatherMode) => void }) {
  const options: [WeatherMode, string][] = [["live", "Live weather"], ["demo", "Demo storm"]];
  return (
    <div className="mt-6 flex flex-wrap items-center gap-3" role="group" aria-label="Weather shown on this page">
      <span className="text-sm font-semibold text-muted">Weather</span>
      {options.map(([value, label]) => (
        <button
          key={value}
          type="button"
          aria-pressed={mode === value}
          onClick={() => onChange(value)}
          className={`min-h-11 rounded-xl border px-4 font-bold ${mode === value ? "border-ink bg-ink text-white" : "border-line bg-paper text-ink hover:border-teal"}`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function Readiness({ weather }: { weather: WeatherMode }) {
  const stores = useStores(weather);
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

function DemoEmail() {
  const send = useDemoAlert();
  return (
    <div className="mt-3 flex flex-wrap items-center gap-3">
      <button
        type="button"
        disabled={send.isPending}
        onClick={() => send.mutate()}
        className="min-h-11 rounded-xl bg-ink px-4 font-bold text-white disabled:bg-line disabled:text-muted"
      >
        {send.isPending ? "Sending…" : "Email this storm alert"}
      </button>
      {send.isSuccess && <p role="status" className="font-semibold text-teal-deep">{send.data.message}</p>}
      {send.isError && <p role="alert" className="font-semibold text-signal-deep">{send.error.message}</p>}
    </div>
  );
}

function Markdowns({ weather }: { weather: WeatherMode }) {
  const items = useMarkdowns(weather);
  return (
    <section aria-labelledby="md-h" className="mt-10">
      <h2 id="md-h" className="text-xl font-extrabold">Price markdowns</h2>
      <p className="mt-1 text-sm text-muted">
        Surplus stock that would not sell at full price in two weeks. Each suggestion is only shown when a discount brings in more cash than holding. Nothing is changed here.
      </p>
      {weather === "demo" && (
        <p className="mt-2 text-sm font-semibold text-heat">Demo response: each 10% off is assumed to lift sales by 40%, so more markdowns can pay. Live weather uses 15%.</p>
      )}
      <QueryView query={items} rows={2} isEmpty={(d) => d.length === 0} empty={<p className="mt-4 text-muted">No markdowns needed this week.</p>}>
        {(list) => (
          <ul className="mt-4 divide-y divide-line rounded-2xl border border-line bg-paper">
            {list.map((m) => (
              <li key={`${m.store.id}-${m.product.id}`} className="grid gap-1 p-4 sm:grid-cols-[1fr_auto] sm:items-center">
                <div>
                  <p className="font-bold">
                    {m.store.name}: {m.product.name_plural}, {m.discount_pct}% off
                  </p>
                  <p className="text-sm text-muted">{m.note}</p>
                </div>
                <p className="text-right text-sm font-extrabold text-teal-deep">+${Math.round(m.extra_cash_usd).toLocaleString("en-US")}</p>
              </li>
            ))}
          </ul>
        )}
      </QueryView>
    </section>
  );
}

function Body({ o, name, weather, onWeather }: { o: Overview; name: string; weather: WeatherMode; onWeather: (m: WeatherMode) => void }) {
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

      <WeatherSwitch mode={weather} onChange={onWeather} />
      {weather === "demo" && (
        <p role="status" className="mt-3 rounded-2xl bg-heat-tint p-4 font-semibold text-heat">
          Demo storm: a storm is placed on the Florida stores for the next two days. Stock figures and transfers still come from the live plan.
        </p>
      )}
      {weather === "demo" && <DemoEmail />}

      <section aria-label="Today at a glance" className="settle mt-8 grid grid-cols-3 divide-x divide-line">
        <Figure value={o.urgent_transfers} urgent={o.urgent_transfers > 0} label={o.urgent_transfers === 1 ? "urgent transfer" : "urgent transfers"} />
        <Figure value={o.stores_at_risk} label={o.stores_at_risk === 1 ? "store running low" : "stores running low"} />
        {alert ? (
          <Figure value={shortDay(alert.date.toString())} label={`${KIND[alert.kind].toLowerCase()} expected`} hint={alert.detail} />
        ) : (
          <Figure value="None" label="weather alerts this week" />
        )}
      </section>

      <Readiness weather={weather} />
      <Markdowns weather={weather} />

      <Link
        to={o.next_action.path}
        className="mt-10 flex min-h-14 items-center justify-center rounded-2xl bg-ink px-6 text-lg font-extrabold text-white transition-colors hover:bg-teal-deep"
      >
        {o.next_action.button}
      </Link>
      {o.pending_transfers > 0 && (
        <p className="mt-3 text-center text-sm text-muted">{plural(o.pending_transfers, "transfer")} waiting in total</p>
      )}
      <Link
        to="/your-data"
        className="mt-4 flex min-h-12 items-center justify-center rounded-2xl border border-line bg-paper px-6 font-bold text-teal-deep hover:border-teal hover:bg-teal-tint"
      >
        Show my uploaded data
      </Link>
      {o.as_of && <p className="mt-8 text-center text-xs text-muted">Based on stock counted {longDate(parseDay(o.as_of.toString()))}</p>}
    </>
  );
}

export default function Today() {
  const me = useMe();
  const [params, setParams] = useSearchParams();
  const weather: WeatherMode = params.get("weather") === "demo" ? "demo" : "live";
  const overview = useOverview(weather);
  return (
    <QueryView query={overview} rows={2}>
      {(o) => (
        <Body
          o={o}
          name={me.data?.name ?? "there"}
          weather={weather}
          onWeather={(m) => setParams(m === "demo" ? { weather: "demo" } : {})}
        />
      )}
    </QueryView>
  );
}
