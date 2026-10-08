"""One feature row per store, product and date, built only from what is known at prediction time.

No leakage, by construction:
* Sales-based features are lagged by 7 days (the forecast horizon). A row for date d only sees sales up to d-7,
  so the same row can be built today for any of the next 7 days and for any day in the past.
* Weather features for day d and the three days after it are *forecast-time* information: for future days they come
  from the provider forecast; for history they are the observed weather with forecast-sized error added, so training
  and validation do not assume a perfect forecast.
* The target (units sold on d) never appears in any feature of any row.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

LAG = 7
NOISE_LEAD_DAYS = 4  # typical forecast lead used to size the error added to historical weather
WEATHER_COLS = ["temp_max_f", "rain_in", "wind_max_mph"]
CATEGORICAL = ["store_code", "product_code"]
FEATURES = CATEGORICAL + [
    "dow", "month", "is_weekend", "is_holiday",
    *WEATHER_COLS, "wind_lead_max", "rain_lead_sum", "temp_lead_delta",
    "sales_lag7", "avg7_lag7", "avg28_lag7",
]


def _lead(x: pd.Series, k: int) -> pd.Series:
    return x.shift(-k).fillna(x.iloc[-1])


def with_forecast_error(weather: pd.DataFrame, seed: int = 11) -> pd.DataFrame:
    """Make observed weather look like a forecast made NOISE_LEAD_DAYS ahead."""
    rng, w, h = np.random.default_rng(seed), weather.copy(), NOISE_LEAD_DAYS
    w["temp_max_f"] += rng.normal(0, 1.5 + 0.6 * h, len(w))
    w["wind_max_mph"] = np.maximum(0, w["wind_max_mph"] + rng.normal(0, 2 + 1.5 * h, len(w)))
    w["rain_in"] = w["rain_in"] * np.exp(rng.normal(0, 0.1 + 0.07 * h, len(w)))
    return w


def build_features(
    sales: pd.DataFrame,
    observed: pd.DataFrame,
    forecast: pd.DataFrame,
    as_of: date,
    horizon: int = 7,
) -> pd.DataFrame:
    """Feature table for [first date with 34 days of history, as_of + horizon]. `units` is NaN for future dates."""
    obs = observed.rename(columns={"obs_date": "date"})[["store_id", "date", *WEATHER_COLS]].copy()
    obs["date"] = pd.to_datetime(obs["date"])
    fc = forecast.rename(columns={"forecast_date": "date"})
    fc = fc[fc["issued_at"] == fc["issued_at"].max()][["store_id", "date", *WEATHER_COLS]].copy()
    fc["date"] = pd.to_datetime(fc["date"])
    weather = pd.concat([with_forecast_error(obs), fc], ignore_index=True).sort_values(["store_id", "date"])

    parts = []
    for sid, w in weather.groupby("store_id"):
        w = w.set_index("date")
        out = pd.DataFrame(index=w.index)
        out[WEATHER_COLS] = w[WEATHER_COLS]
        out["wind_lead_max"] = pd.concat([_lead(w["wind_max_mph"], 1), _lead(w["wind_max_mph"], 2)], axis=1).max(axis=1)
        out["rain_lead_sum"] = sum(_lead(w["rain_in"], k) for k in (1, 2, 3))
        out["temp_lead_delta"] = _lead(w["temp_max_f"], 2) - w["temp_max_f"]
        out["store_id"] = sid
        parts.append(out.reset_index())
    wx = pd.concat(parts, ignore_index=True)

    s = sales.rename(columns={"sale_date": "date"}).copy()
    s["date"] = pd.to_datetime(s["date"])
    horizon_end = pd.Timestamp(as_of) + pd.Timedelta(days=horizon)
    days = pd.date_range(s["date"].min(), horizon_end)

    rows = []
    for (sid, pid), g in s.groupby(["store_id", "product_id"]):
        u = g.set_index("date")["units"].reindex(days)  # NaN for future days
        past = u.shift(LAG)  # value known at prediction time for the target day
        frame = pd.DataFrame({
            "store_id": sid, "product_id": pid, "date": days, "units": u.values,
            "sales_lag7": past.values,
            "avg7_lag7": past.rolling(7).mean().values,
            "avg28_lag7": past.rolling(28).mean().values,
        })
        rows.append(frame)
    df = pd.concat(rows, ignore_index=True).merge(wx, on=["store_id", "date"], how="left")
    df = df.dropna(subset=["avg28_lag7"]).copy()

    hol = set(USFederalHolidayCalendar().holidays(days.min(), days.max()))
    df["dow"], df["month"] = df["date"].dt.dayofweek, df["date"].dt.month
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    df["is_holiday"] = df["date"].isin(hol).astype(int)
    df["store_code"] = df["store_id"].str[1:].astype(int)
    df["product_code"] = df["product_id"].str[1:].astype(int)
    df["is_future"] = df["date"] > pd.Timestamp(as_of)
    return df.sort_values(["store_id", "product_id", "date"]).reset_index(drop=True)
