"""Shortage and surplus detection, and transfer recommendations. Pure pandas: easy to test, cheap at this scale."""
from __future__ import annotations

import math
import uuid
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from .weather import weather_phrase, worst_event

KEYS = ["store_id", "product_id"]
DRIVER_CONDITIONS = {"wind": ["storm"], "rain": ["storm", "heavy_rain"], "heat": ["heat"]}


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(a))


def committed_from_recs(recs: pd.DataFrame, as_of: date) -> pd.DataFrame:
    """Approved transfers made against this snapshot count as stock arriving at (or leaving) a store."""
    cols = [*KEYS, "committed_in", "committed_out"]
    if recs is None or recs.empty:
        return pd.DataFrame({"store_id": pd.Series(dtype=str), "product_id": pd.Series(dtype=str),
                             "committed_in": pd.Series(dtype=float), "committed_out": pd.Series(dtype=float)})
    ok = recs[(recs["status"] == "APPROVED") & (pd.to_datetime(recs["as_of_date"]).dt.date == as_of)]
    inbound = ok.groupby(["dest_store_id", "product_id"])["qty"].sum().rename("committed_in").reset_index() \
        .rename(columns={"dest_store_id": "store_id"})
    outbound = ok.groupby(["source_store_id", "product_id"])["qty"].sum().rename("committed_out").reset_index() \
        .rename(columns={"source_store_id": "store_id"})
    return inbound.merge(outbound, on=KEYS, how="outer").fillna(0)[cols]


def compute_gaps(
    predictions: pd.DataFrame,
    inventory: pd.DataFrame,
    committed: pd.DataFrame,
    intervals: pd.DataFrame,
    settings: dict[str, float],
    as_of: date,
) -> pd.DataFrame:
    """Projected stock over the horizon per store and product, classified SHORTAGE / SURPLUS / BALANCED."""
    p = predictions.sort_values("forecast_date").copy()
    p["cum"] = p.groupby(KEYS)["predicted_units"].cumsum()
    week = p.groupby(KEYS)["predicted_units"].sum().rename("forecast_units").reset_index()
    horizon = p.groupby(KEYS)["forecast_date"].nunique().rename("days").reset_index()

    df = inventory[[*KEYS, "on_hand", "in_transit"]].merge(week, on=KEYS).merge(horizon, on=KEYS)
    df = df.merge(committed, on=KEYS, how="left")
    df[["committed_in", "committed_out"]] = df[["committed_in", "committed_out"]].astype(float).fillna(0.0)
    df = df.merge(intervals[["product_id", "ratio_p10", "ratio_p90"]], on="product_id", how="left")
    df[["ratio_p10", "ratio_p90"]] = df[["ratio_p10", "ratio_p90"]].fillna(1.0)

    df["available"] = df.on_hand + df.in_transit + df.committed_in - df.committed_out
    df["avg_daily"] = df.forecast_units / df.days
    df["safety_stock"] = settings["safety_stock_days"] * df.avg_daily
    df["days_of_cover"] = np.where(df.avg_daily > 0.01, df.available / df.avg_daily.clip(lower=0.01), 999.0).clip(max=999.0)

    path = p.merge(df[[*KEYS, "available", "safety_stock"]], on=KEYS)
    path["after"] = path.available - path.cum
    low = path[path.after < path.safety_stock].groupby(KEYS)["forecast_date"].min().rename("runs_low_date")
    out = path[path.after < 0].groupby(KEYS)["forecast_date"].min().rename("stockout_date")
    df = df.merge(low, on=KEYS, how="left").merge(out, on=KEYS, how="left")

    need = lambda f: (df.safety_stock - (df.available - f)).clip(lower=0)  # noqa: E731
    df["shortfall_units"] = need(df.forecast_units)
    df["shortfall_p10"] = need(df.forecast_units * df.ratio_p10)
    df["shortfall_p90"] = need(df.forecast_units * df.ratio_p90)
    df["lost_units"] = (df.forecast_units - df.available).clip(lower=0)
    df["spare_units"] = (df.available - df.forecast_units - df.safety_stock).clip(lower=0)
    df["forecast_p10"], df["forecast_p90"] = df.forecast_units * df.ratio_p10, df.forecast_units * df.ratio_p90

    df["status"] = np.select(
        [df.shortfall_units >= 1, (df.days_of_cover >= settings["surplus_threshold_days"]) & (df.spare_units >= 1)],
        ["SHORTAGE", "SURPLUS"], default="BALANCED",
    )
    df.insert(0, "as_of_date", as_of)
    cols = ["as_of_date", *KEYS, "on_hand", "in_transit", "committed_in", "committed_out", "available", "forecast_units",
            "forecast_p10", "forecast_p90", "avg_daily", "safety_stock", "days_of_cover", "runs_low_date", "stockout_date",
            "shortfall_units", "shortfall_p10", "shortfall_p90", "lost_units", "spare_units", "status"]
    num = df.select_dtypes("number").columns
    df[num] = df[num].round(2)
    for c in ("runs_low_date", "stockout_date"):
        df[c] = pd.to_datetime(df[c]).dt.date
    return df[cols].sort_values(KEYS).reset_index(drop=True)


def confidence_level(score: float) -> str:
    return "High" if score >= 0.7 else "Medium" if score >= 0.4 else "Low"


def route_penalties(route_preferences: pd.DataFrame | None) -> dict[tuple[str, str, str], tuple[float, str]]:
    """(source, destination, product) -> (penalty multiplier, plain note) from learned planner decisions."""
    if route_preferences is None or route_preferences.empty:
        return {}
    out = {}
    for r in route_preferences.itertuples():
        note = (f"Ranked lower: planners rejected a move on this route {int(r.rejections)} "
                f"time{'s' if int(r.rejections) != 1 else ''} recently")
        if isinstance(r.last_reason, str) and r.last_reason:
            note += f" (last reason: {r.last_reason.lower()})"
        out[(r.source_store_id, r.dest_store_id, r.product_id)] = (float(r.penalty), note + ".")
    return out


def closer_store_note(dest: str, source_miles: float, by_distance: list[tuple[str, float]], status: dict,
                      supply: dict, pack: int, plural: str, penalties: dict, pid: str, names: dict) -> str:
    """One line on the nearest store that is closer than the chosen source, and why it was not used."""
    for store, miles in by_distance:
        if miles >= source_miles:
            break
        if store == dest:
            continue
        name = names[store]
        if status.get(store) == "SHORTAGE":
            return f"{name} is closer but also short of {plural}."
        if supply.get(store, 0) < pack:
            return f"{name} is closer but has no spare {plural} to send."
        if (store, dest, pid) in penalties:
            return f"{name} is closer, but a planner rejected that route recently."
    return ""


def recommend_transfers(
    gaps: pd.DataFrame,
    stores: pd.DataFrame,
    products: pd.DataFrame,
    weather_forecast: pd.DataFrame,
    settings: dict[str, float],
    as_of: date,
    run_ts: datetime,
    route_preferences: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Match surplus stores to shortage stores per product, nearest source first.

    Learned planner decisions (route_preferences) rank a rejected route lower; they never create or remove a move.
    """
    penalties = route_penalties(route_preferences)
    st = stores.set_index("store_id")
    pr = products.set_index("product_id")
    wx = weather_forecast.copy()
    wx["forecast_date"] = pd.to_datetime(wx["forecast_date"])
    horizon_end = pd.Timestamp(as_of) + timedelta(days=int(settings["forecast_horizon_days"]))
    urgent_by = as_of + timedelta(days=1 + int(settings["urgent_threshold_days"]))  # as_of is yesterday
    min_qty, max_miles = settings["min_transfer_qty"], settings["max_transfer_distance_miles"]

    rows = []
    for pid, g in gaps.groupby("product_id"):
        pack, price, plural = int(pr.at[pid, "pack_size"]), float(pr.at[pid, "unit_price"]), pr.at[pid, "name_plural"]
        floor_pack = lambda q: int(q // pack) * pack  # noqa: E731, B023 (used within this iteration)
        supply = {r.store_id: floor_pack(r.spare_units) for r in g[g.status == "SURPLUS"].itertuples()}
        status = dict(zip(g.store_id, g.status))
        short = g[g.status == "SHORTAGE"].assign(value=lambda d: d.lost_units * price + d.shortfall_units * 0.01)  # noqa: B023
        for d in short.sort_values("value", ascending=False).itertuples():
            need, lost_left = int(math.ceil(d.shortfall_units / pack) * pack), float(d.lost_units)
            sources = sorted(
                (s for s, q in supply.items() if q >= pack),
                key=lambda s: haversine_miles(st.at[s, "latitude"], st.at[s, "longitude"],
                                              st.at[d.store_id, "latitude"], st.at[d.store_id, "longitude"])
                * penalties.get((s, d.store_id, pid), (1.0, ""))[0],
            )
            score = min(1.0, d.shortfall_p10 / d.shortfall_units) if d.shortfall_units else 0.0
            in_week = (wx.forecast_date > pd.Timestamp(as_of)) & (wx.forecast_date <= horizon_end)
            weather = wx[(wx.store_id == d.store_id) & in_week]
            phrase = weather_phrase(worst_event(weather, DRIVER_CONDITIONS[pr.at[pid, "weather_driver"]]))
            by_distance = sorted(
                ((o, haversine_miles(st.at[o, "latitude"], st.at[o, "longitude"],
                                     st.at[d.store_id, "latitude"], st.at[d.store_id, "longitude"]))
                 for o in st.index), key=lambda x: x[1])
            for s in sources:
                miles = haversine_miles(st.at[s, "latitude"], st.at[s, "longitude"],
                                        st.at[d.store_id, "latitude"], st.at[d.store_id, "longitude"])
                if miles > max_miles or need <= 0:
                    continue
                qty = floor_pack(min(max(need, min_qty), supply[s]))
                if qty < min_qty:
                    continue
                closer = closer_store_note(d.store_id, miles, by_distance, status, supply, pack, plural, penalties, pid,
                                           st["name"].to_dict())
                protected = min(float(qty), lost_left)
                rows.append(dict(
                    rec_id="TR-" + uuid.uuid4().hex[:10].upper(), as_of_date=as_of,
                    source_store_id=s, dest_store_id=d.store_id, product_id=pid, qty=qty,
                    urgency="URGENT" if (pd.notna(d.stockout_date) and d.stockout_date <= urgent_by)
                    or d.lost_units * price >= settings["urgent_lost_sales_usd"] else "NORMAL",
                    confidence=round(score, 2), confidence_level=confidence_level(score),
                    reason=f"{phrase}. {st.at[d.store_id, 'name']} will sell about {round(d.forecast_units)} {plural} "
                           f"this week and has {round(d.available)}."
                           + (" " + penalties[(s, d.store_id, pid)][1] if (s, d.store_id, pid) in penalties else "")
                           + (" " + closer if closer else ""),
                    sales_protected_usd=round(protected * price, 2), distance_miles=round(miles),
                    runs_low_date=d.runs_low_date, status="PENDING", created_at=run_ts,
                    decided_by=None, decided_at=None, decision_note=None, decision_request_id=None,
                ))
                supply[s] -= qty
                need -= qty
                lost_left -= protected
    cols = ["rec_id", "as_of_date", "source_store_id", "dest_store_id", "product_id", "qty", "urgency", "confidence",
            "confidence_level", "reason", "sales_protected_usd", "distance_miles", "runs_low_date", "status", "created_at",
            "decided_by", "decided_at", "decision_note", "decision_request_id"]
    return pd.DataFrame(rows, columns=cols)
