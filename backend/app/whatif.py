"""What-if storm simulator. It only computes; it never writes.

A scenario raises wind and rain for a chosen stretch of the coming week. Both the normal week and the storm week are
scored by the same forecaster, so the difference is the storm's effect alone. Sales lost are counted against the stock
each store has on hand and on the way, at the product's price.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

# Must match stormsense_core.features.FEATURES (a test checks this).
FEATURES = [
    "store_code", "product_code", "dow", "month", "is_weekend", "is_holiday", "temp_max_f", "rain_in", "wind_max_mph",
    "wind_lead_max", "rain_lead_sum", "temp_lead_delta", "sales_lag7", "avg7_lag7", "avg28_lag7",
]
WIND_MPH_AT_FULL_STRENGTH = 50.0  # strength 100 adds this much wind on each storm day
RAIN_IN_AT_FULL_STRENGTH = 5.0  # strength 100 adds this much rain on each storm day
MAX_ROWS_SHOWN = 12

Scorer = Callable[[pd.DataFrame], np.ndarray]


@dataclass(frozen=True)
class Scenario:
    strength: int  # 0 to 100
    start_day: int  # 0 means tomorrow
    days: int  # 1 to 4
    region: str | None = None  # None means every store


def recompute_leads(rows: pd.DataFrame) -> pd.DataFrame:
    """Lead-time weather features from each store's day-by-day weather, the same way the feature build makes them."""
    out = rows.copy()
    out["date"] = pd.to_datetime(out["date"])
    out = out.sort_values(["store_id", "product_id", "date"])
    for _, idx in out.groupby(["store_id", "product_id"]).groups.items():
        g = out.loc[idx]
        wind, rain, temp = g["wind_max_mph"], g["rain_in"], g["temp_max_f"]
        out.loc[idx, "wind_lead_max"] = pd.concat([wind.shift(-1), wind.shift(-2)], axis=1).max(axis=1).ffill().values
        out.loc[idx, "rain_lead_sum"] = (rain.shift(-1).fillna(0) + rain.shift(-2).fillna(0) + rain.shift(-3).fillna(0)).values
        out.loc[idx, "temp_lead_delta"] = (temp.shift(-2).ffill() - temp).values
    return out


def apply_scenario(rows: pd.DataFrame, sc: Scenario, as_of: date) -> pd.DataFrame:
    """Storm weather on the scenario days, with the lead-time features recomputed. Strength 0 gives the normal week."""
    df = rows.copy()
    df["date"] = pd.to_datetime(df["date"])
    start_d = as_of + timedelta(days=1 + sc.start_day)
    end_d = start_d + timedelta(days=sc.days - 1)
    start, end = pd.Timestamp(start_d), pd.Timestamp(end_d)
    storm_days = (df["date"] >= start) & (df["date"] <= end)
    df.loc[storm_days, "wind_max_mph"] = df.loc[storm_days, "wind_max_mph"] + WIND_MPH_AT_FULL_STRENGTH * sc.strength / 100
    df.loc[storm_days, "rain_in"] = df.loc[storm_days, "rain_in"] + RAIN_IN_AT_FULL_STRENGTH * sc.strength / 100
    return recompute_leads(df)


def impact(rows: pd.DataFrame, normal: np.ndarray, storm: np.ndarray, available: dict[tuple[str, str], float],
           prices: dict[str, float], names: dict[str, str]) -> dict:
    """Sales lost with and without the storm, per store and product, after the stock each store already has."""
    df = rows[["store_id", "product_id"]].assign(normal=normal, storm=storm)
    per = df.groupby(["store_id", "product_id"]).agg(normal=("normal", "sum"), storm=("storm", "sum")).reset_index()
    per["available"] = [available.get((s, p), 0.0) for s, p in zip(per.store_id, per.product_id)]
    per["lost_normal"] = (per.normal - per.available).clip(lower=0)
    per["lost_storm"] = (per.storm - per.available).clip(lower=0)
    per["extra_lost_units"] = per.lost_storm - per.lost_normal
    per["extra_lost_usd"] = per.extra_lost_units * per.product_id.map(prices).fillna(0.0)
    per = per.sort_values("extra_lost_usd", ascending=False)
    rows_out = [{
        "store": names.get(r.store_id, r.store_id), "product": names.get(r.product_id, r.product_id),
        "normal_units": round(float(r.normal)), "storm_units": round(float(r.storm)), "on_hand": round(float(r.available)),
        "extra_lost_usd": round(float(r.extra_lost_usd), 2),
    } for r in per.head(MAX_ROWS_SHOWN).itertuples()]
    return {
        "normal_units": round(float(per.normal.sum())),
        "storm_units": round(float(per.storm.sum())),
        "extra_demand_units": round(float((per.storm - per.normal).sum())),
        "extra_lost_usd": round(float(per.extra_lost_usd.sum()), 2),
        "stock_to_move_units": round(float(per.extra_lost_units.clip(lower=0).sum())),
        "rows": rows_out,
    }


def run(rows: pd.DataFrame, sc: Scenario, as_of: date, score: Scorer, available: dict, prices: dict, names: dict) -> dict:
    """Score the normal week and the storm week with the same forecaster, and report what the storm costs."""
    normal_rows = apply_scenario(rows, Scenario(0, sc.start_day, sc.days, sc.region), as_of)
    storm_rows = apply_scenario(rows, sc, as_of)
    normal = score(normal_rows[FEATURES])
    storm = score(storm_rows[FEATURES])
    result = impact(storm_rows, normal, storm, available, prices, names)
    result["window"] = _window(as_of, sc)
    return result


def _window(as_of: date, sc: Scenario) -> str:
    start = as_of + timedelta(days=1 + sc.start_day)
    end = start + timedelta(days=sc.days - 1)
    return start.strftime("%A") if sc.days == 1 else f"{start.strftime('%A')} to {end.strftime('%A')}"


class EndpointScorer:
    """Scores feature rows with the forecaster's serving endpoint (a scale-to-zero model endpoint in the workspace)."""

    def __init__(self, api_client: object, endpoint: str) -> None:
        self.api, self.endpoint = api_client, endpoint

    def __call__(self, frame: pd.DataFrame) -> np.ndarray:
        body = {"dataframe_split": {"columns": list(frame.columns), "data": frame.astype(float).values.tolist()}}
        out = self.api.do("POST", f"/serving-endpoints/{self.endpoint}/invocations", body=body)
        return np.clip(np.asarray(out["predictions"], dtype=float), 0.0, None)
