"""Sample data: 12 months of weather, sales and stock where demand is caused by weather.

Everything is seeded and anchored to `end` (the last day of history), so a run is reproducible.
Demand never depends on randomness alone: wind and rain lift generators, plywood, tarps and pumps
one to two days *before* they arrive, heat lifts coolers, and named events are injected so the model
has clear spikes to learn from.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

from .reference import products_df, stores_df
from .weather import classify

SEED = 20260101
HISTORY_DAYS = 365
FORECAST_DAYS = 10  # 7 forecast days plus 3 days of look-ahead for the lead features


# ---- Climate -------------------------------------------------------------------------------

CLIMATE = {
    "Florida": dict(mean=82, amp=8, peak=200, anom=2.5, wind=11, rain_mean=0.5,
                    wet=lambda m: 0.5 if 6 <= m <= 9 else 0.2),
    "Texas": dict(mean=80, amp=18, peak=205, anom=4.0, wind=13, rain_mean=0.45,
                  wet=lambda m: 0.28 if m in (4, 5, 6) else 0.17),
    "California": dict(mean=73, amp=10, peak=210, anom=3.0, wind=9, rain_mean=0.4,
                       wet=lambda m: 0.2 if m in (11, 12, 1, 2, 3) else 0.01),
}
TEMP_OFFSET = {"Sacramento": 7, "San Diego": -4, "Houston": 3, "Dallas": 1, "Miami": 2, "Jacksonville": -3, "Tampa": 0.5}


@dataclass(frozen=True)
class Event:
    name: str
    kind: str
    stores: dict[str, float]  # store name -> intensity (0-1)
    month_day: tuple[int, int] | None = None  # history: latest occurrence before `end`
    offset: int | None = None  # forecast: days after `end`


PROFILES = {
    "hurricane": dict(wind=[35, 55, 80, 60, 35], rain=[0.8, 2.5, 6.0, 3.0, 0.8]),
    "tropical_storm": dict(wind=[35, 62, 48], rain=[0.6, 3.2, 1.4]),
    "severe_storm": dict(wind=[40, 58, 45], rain=[0.4, 1.8, 0.6]),
    "atmospheric_river": dict(wind=[25, 38, 32, 22], rain=[1.2, 3.5, 4.5, 2.0]),
    "heat_wave": dict(temp=[10, 14, 16, 15, 11]),
}

EVENTS = [
    Event("Hurricane Marlow", "hurricane", {"Tampa": 1.0, "Orlando": 0.9, "Miami": 0.75, "Jacksonville": 0.6}, (9, 14)),
    Event("Tropical Storm Ines", "tropical_storm", {"Houston": 1.0, "Austin": 0.6, "Dallas": 0.4}, (8, 24)),
    Event("Heat Dome Ridge", "heat_wave", {"Dallas": 1.0, "Austin": 0.9, "Houston": 0.8}, (7, 6)),
    Event("Atmospheric River Kestrel", "atmospheric_river", {"Los Angeles": 1.0, "San Diego": 0.8, "Sacramento": 0.7}, (1, 9)),
    Event("Severe Storm Delta", "severe_storm", {"Dallas": 1.0, "Austin": 0.8, "Houston": 0.7}, (4, 17)),
    # Upcoming: gives the planner something to act on.
    Event("Tropical Storm Odalys", "tropical_storm",
          {"Tampa": 1.0, "Orlando": 0.85, "Jacksonville": 0.45, "Miami": 0.5}, offset=3),
    Event("Heat Dome Sol", "heat_wave", {"Dallas": 1.0, "Austin": 0.9, "Houston": 0.8}, offset=1),
]


def _event_start(ev: Event, end: date) -> date:
    if ev.offset is not None:
        return end + timedelta(days=ev.offset)
    length = len(next(iter(PROFILES[ev.kind].values())))
    start = date(end.year, *ev.month_day)
    while start + timedelta(days=length) > end:  # whole event must be in the past
        start = date(start.year - 1, *ev.month_day)
    return start


def simulate_weather(end: date, days: int = HISTORY_DAYS, seed: int = SEED) -> pd.DataFrame:
    """True weather for [end-days+1, end+FORECAST_DAYS], one row per store and day."""
    dates = pd.date_range(end - timedelta(days=days - 1), end + timedelta(days=FORECAST_DAYS))
    n, doy, month = len(dates), dates.dayofyear.values, dates.month.values
    stores = stores_df()
    regional: dict[str, dict[str, np.ndarray]] = {}
    for i, region in enumerate(CLIMATE):
        rng, c = np.random.default_rng(seed + 1000 * i), CLIMATE[region]
        anom, wet = np.zeros(n), np.zeros(n, dtype=bool)
        for t in range(1, n):
            anom[t] = 0.8 * anom[t - 1] + rng.normal(0, c["anom"] * 0.6)
            p = c["wet"](month[t])
            wet[t] = rng.random() < (min(0.9, p + 0.25) if wet[t - 1] else p * 0.8)
        regional[region] = dict(anom=anom, wet=wet, gust=rng.gamma(5, 0.12, n))

    frames = []
    for i, s in enumerate(stores.itertuples()):
        rng, c, r = np.random.default_rng(seed + 100 + i), CLIMATE[s.region], regional[s.region]
        tmax = c["mean"] + c["amp"] * np.cos(2 * np.pi * (doy - c["peak"]) / 365) + r["anom"] \
            + TEMP_OFFSET.get(s.name, 0) + rng.normal(0, 1.2, n)
        rain = np.where(r["wet"] & (rng.random(n) < 0.85), np.minimum(rng.exponential(c["rain_mean"], n), 3.5), 0.0)
        wind = c["wind"] * (0.5 + 0.5 * r["gust"] / 0.6) * rng.gamma(8, 1 / 8, n) + np.where(rain > 0, rng.uniform(3, 9, n), 0)
        df = pd.DataFrame({"store_id": s.store_id, "date": dates, "temp_max_f": tmax,
                           "rain_in": rain, "wind_max_mph": wind, "event_name": None})
        for ev in EVENTS:
            if s.name not in ev.stores:
                continue
            f, prof = ev.stores[s.name], PROFILES[ev.kind]
            for k in range(len(next(iter(prof.values())))):
                row = df.index[df["date"] == pd.Timestamp(_event_start(ev, end) + timedelta(days=k))]
                if not len(row):
                    continue
                j = row[0]
                if "wind" in prof:
                    df.at[j, "wind_max_mph"] = max(df.at[j, "wind_max_mph"], prof["wind"][k] * f)
                    df.at[j, "rain_in"] = max(df.at[j, "rain_in"], prof["rain"][k] * f)
                if "temp" in prof:
                    df.at[j, "temp_max_f"] = df.at[j, "temp_max_f"] + prof["temp"][k] * f
                df.at[j, "event_name"] = ev.name
        frames.append(df)

    out = pd.concat(frames, ignore_index=True)
    for col in ("temp_max_f", "rain_in", "wind_max_mph"):
        out[col] = out[col].astype(float).round(1)
    out["temp_min_f"] = (out["temp_max_f"] - 18).round(1)
    out["condition"] = [classify(w, r, t) for w, r, t in zip(out.wind_max_mph, out.rain_in, out.temp_max_f)]
    return out


def forecast_from_truth(truth: pd.DataFrame, end: date, seed: int = SEED) -> pd.DataFrame:
    """What a weather provider would have said on `end`: truth plus error that grows with lead time."""
    rng = np.random.default_rng(seed + 7)
    fut = truth[truth["date"] > pd.Timestamp(end)].copy()
    h = ((fut["date"] - pd.Timestamp(end)).dt.days).astype(float).values
    fut["temp_max_f"] = (fut["temp_max_f"] + rng.normal(0, 1.5 + 0.6 * h)).round(1)
    fut["wind_max_mph"] = np.maximum(0, fut["wind_max_mph"] + rng.normal(0, 2 + 1.5 * h)).round(1)
    fut["rain_in"] = (fut["rain_in"] * np.exp(rng.normal(0, 0.1 + 0.07 * h))).round(1)
    fut["temp_min_f"] = (fut["temp_max_f"] - 18).round(1)
    fut["condition"] = [classify(w, r, t) for w, r, t in zip(fut.wind_max_mph, fut.rain_in, fut.temp_max_f)]
    issued = datetime(end.year, end.month, end.day) + timedelta(days=1, hours=6)
    fut["issued_at"], fut["issued_date"] = issued, issued.date()
    return fut.rename(columns={"date": "forecast_date"}).reset_index(drop=True)


# ---- Demand --------------------------------------------------------------------------------

REGION_MULT = {("Florida", "P01"): 1.2, ("Florida", "P03"): 1.2, ("Texas", "P05"): 1.3, ("Texas", "P04"): 1.1,
               ("California", "P04"): 0.6, ("California", "P01"): 0.7}
# Monday..Sunday
DOW = {"P01": [1, 1, 1, 1, 1.05, 1.15, 1.1], "P02": [0.9, 0.9, 0.9, 0.95, 1.1, 1.4, 1.3],
       "P03": [0.95, 0.95, 0.95, 1, 1.05, 1.2, 1.15], "P04": [1, 1, 1, 1, 1, 1.1, 1.1],
       "P05": [0.85, 0.85, 0.9, 0.95, 1.15, 1.4, 1.3]}


def _lead(x: np.ndarray, k: int) -> np.ndarray:
    return np.concatenate([x[k:], np.repeat(x[-1], k)]) if k else x


def expected_demand(truth: pd.DataFrame) -> pd.DataFrame:
    """Expected units per store, product and day, caused by that day's weather and the next two days'."""
    stores, products = stores_df().set_index("store_id"), products_df()
    hol = set(USFederalHolidayCalendar().holidays(truth["date"].min(), truth["date"].max()))
    rows = []
    for sid, g in truth.sort_values("date").groupby("store_id"):
        s = stores.loc[sid]
        d = g["date"]
        wind, rain, temp = g["wind_max_mph"].values, g["rain_in"].values, g["temp_max_f"].values
        storm = [np.clip((_lead(wind, k) - 25) / 40, 0, 1) + 0.5 * np.clip(_lead(rain, k) / 4, 0, 1) for k in range(3)]
        storm_sig = np.max([w * x for w, x in zip((1.0, 0.85, 0.6), storm)], axis=0)
        rain_sig = np.max([w * np.clip(_lead(rain, k) / 3, 0, 1) for k, w in enumerate((1.0, 0.7, 0.4))], axis=0)
        heat_sig = np.clip((temp - 86) / 14, 0, 1.3)
        summer = (1 + np.cos(2 * np.pi * (d.dt.dayofyear.values - 200) / 365)) / 2
        is_hol = d.isin(hol).values
        for p in products.itertuples():
            wx = {"P01": 1 + 6.0 * storm_sig, "P02": 1 + 4.5 * storm_sig,
                  "P03": 1 + 3.0 * np.maximum(rain_sig, 0.5 * storm_sig),
                  "P04": 1 + 4.5 * rain_sig, "P05": 1 + 2.0 * heat_sig}[p.product_id]
            season = 0.6 + 0.8 * summer if p.product_id == "P05" else 1.0
            lam = (p.base_daily_rate * s.size_factor * REGION_MULT.get((s.region, p.product_id), 1.0)
                   * np.array(DOW[p.product_id])[d.dt.dayofweek.values] * season * wx
                   * np.where(is_hol & (p.product_id in ("P02", "P05")), 1.2, 1.0))
            rows.append(pd.DataFrame({"store_id": sid, "product_id": p.product_id, "date": d.values, "lam": lam}))
    return pd.concat(rows, ignore_index=True)


# ---- Stock ---------------------------------------------------------------------------------

# Weeks of forecast demand on hand in the latest snapshot. Below ~1.3 a store runs short,
# above ~3.0 it has extra. Everything not listed is comfortably stocked.
COVER = {
    # Florida: the storm lands on the west coast; the east and north have room to spare.
    ("Orlando", "P01"): 0.30, ("Orlando", "P02"): 0.40, ("Orlando", "P03"): 0.45, ("Orlando", "P04"): 0.55,
    ("Tampa", "P01"): 0.45, ("Tampa", "P02"): 0.50, ("Tampa", "P03"): 0.35, ("Tampa", "P04"): 0.40,
    ("Jacksonville", "P01"): 4.0, ("Jacksonville", "P02"): 4.0, ("Jacksonville", "P03"): 4.2, ("Jacksonville", "P04"): 4.0,
    ("Miami", "P01"): 3.8, ("Miami", "P02"): 3.8, ("Miami", "P03"): 3.9, ("Miami", "P04"): 3.8,
    # Texas: a heat dome over Dallas and Austin.
    ("Dallas", "P05"): 0.35, ("Austin", "P05"): 0.55, ("Houston", "P05"): 3.9,
    ("Houston", "P01"): 3.9, ("Austin", "P02"): 3.8,
    # California: calm week.
    ("Los Angeles", "P01"): 4.0, ("Los Angeles", "P02"): 3.8, ("Los Angeles", "P03"): 3.8,
    ("San Diego", "P03"): 0.6, ("Sacramento", "P04"): 3.9, ("Sacramento", "P05"): 4.0,
}
LEAD_TIME_DAYS = 3


def simulate_inventory(sales: pd.DataFrame, truth: pd.DataFrame, end: date, seed: int = SEED) -> pd.DataFrame:
    """Daily end-of-day stock with a reorder-point policy, then a latest snapshot with built-in imbalance."""
    stores, products = stores_df().set_index("store_id"), products_df().set_index("product_id")
    rng = np.random.default_rng(seed + 11)
    wide = sales.pivot(index="sale_date", columns=["store_id", "product_id"], values="units").sort_index()
    out = []
    for (sid, pid), units in wide.items():
        u = units.values.astype(float)
        avg = pd.Series(u).rolling(28, min_periods=7).mean().bfill().values
        on_hand, pipeline, snaps = 12 * products.loc[pid, "base_daily_rate"] * stores.loc[sid, "size_factor"], [], []
        for t in range(len(u)):
            on_hand = max(0.0, on_hand + sum(q for a, q in pipeline if a == t) - u[t])
            pipeline = [(a, q) for a, q in pipeline if a > t]
            transit = sum(q for _, q in pipeline)
            if on_hand + transit < 6 * avg[t]:
                qty = round(12 * avg[t] - on_hand - transit)
                pipeline.append((t + LEAD_TIME_DAYS, qty))
                transit += qty
            snaps.append((round(on_hand), round(transit)))
        out.append(pd.DataFrame({"store_id": sid, "product_id": pid, "snapshot_date": units.index,
                                 "on_hand": [a for a, _ in snaps], "in_transit": [b for _, b in snaps]}))
    inv = pd.concat(out, ignore_index=True)

    # Latest snapshot: stock expressed as weeks of the coming week's demand.
    lam = expected_demand(truth)
    week = lam[(lam["date"] > pd.Timestamp(end)) & (lam["date"] <= pd.Timestamp(end) + pd.Timedelta(days=7))]
    week = week.groupby(["store_id", "product_id"])["lam"].sum()
    last = inv["snapshot_date"] == pd.Timestamp(end)
    for i in inv.index[last]:
        sid, pid = inv.at[i, "store_id"], inv.at[i, "product_id"]
        factor = COVER.get((stores.at[sid, "name"], pid), float(rng.uniform(1.8, 2.4)))
        total = max(0, round(week[(sid, pid)] * factor))
        transit = round(total * 0.15)
        inv.at[i, "on_hand"], inv.at[i, "in_transit"] = total - transit, transit
    return inv


# ---- Everything ----------------------------------------------------------------------------

@dataclass
class SampleData:
    end: date
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)


def generate(end: date, seed: int = SEED) -> SampleData:
    """All sample tables, with dates as `datetime.date` so they land as DATE columns."""
    truth = simulate_weather(end, seed=seed)
    lam = expected_demand(truth)
    hist = lam[lam["date"] <= pd.Timestamp(end)].copy()
    hist["units"] = np.random.default_rng(seed + 5).poisson(
        hist["lam"].values * np.exp(np.random.default_rng(seed + 6).normal(0, 0.10, len(hist)))
    )
    price = products_df().set_index("product_id")["unit_price"]
    sales = hist.rename(columns={"date": "sale_date"})[["store_id", "product_id", "sale_date", "units"]].reset_index(drop=True)
    sales["revenue_usd"] = (sales["units"] * sales["product_id"].map(price)).round(2)

    observed = truth[truth["date"] <= pd.Timestamp(end)].rename(columns={"date": "obs_date"})
    forecast = forecast_from_truth(truth, end, seed)
    inventory = simulate_inventory(sales, truth, end, seed)

    def as_date(df: pd.DataFrame, *cols: str) -> pd.DataFrame:
        df = df.copy()
        for c in cols:
            df[c] = pd.to_datetime(df[c]).dt.date
        return df

    cols = ["store_id", "{d}", "temp_max_f", "temp_min_f", "rain_in", "wind_max_mph", "condition", "event_name"]
    return SampleData(end, {
        "weather_observed": as_date(observed[[c.format(d="obs_date") for c in cols]], "obs_date"),
        "weather_forecast": as_date(forecast[[c.format(d="forecast_date") for c in cols] + ["issued_at", "issued_date"]],
                                    "forecast_date", "issued_date"),
        "sales_history": as_date(sales, "sale_date"),
        "inventory_snapshot": as_date(inventory, "snapshot_date"),
    })
