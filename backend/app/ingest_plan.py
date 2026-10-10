"""Turns your uploaded files into a plan the planner screens can show: a simple forecast, stock gaps and transfers.

It uses the same planning rules as the sample build (stormsense_core.planning). The forecast is deliberately simple:
for each product and store, the average sales on the same weekday over the last four weeks. It is not the trained
model, and the planner says so. Stock gaps use a fixed spread around that forecast (70% to 130%).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .ingest import IngestStore

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "databricks") not in sys.path:
    sys.path.insert(0, str(REPO / "databricks"))

from stormsense_core import planning, reference  # noqa: E402

LOOKBACK_DAYS = 28
RATIO_P10, RATIO_P90 = 0.7, 1.3
PLAN_FILE = "plan.json"
DEFAULT_ECONOMICS = {"truck_cost_per_mile": 2.5, "margin_pct": 30.0}


class PlanNotReady(ValueError):
    """Raised with a plain message when the uploads are not enough to plan yet."""


def _frame(store: IngestStore, feed: str) -> pd.DataFrame:
    saved = store.read(feed)
    if saved is None:
        raise PlanNotReady(f"Upload your {feed} file first.")
    return pd.DataFrame(saved["rows"])


def _json_default(o: Any) -> Any:
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return str(o)


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return json.loads(json.dumps(df.astype(object).where(df.notna(), None).to_dict("records"), default=_json_default))


def build(store: IngestStore) -> dict[str, Any]:
    """Plans from the uploaded files and returns the tables plus a summary. Raises PlanNotReady when files are missing."""
    stores, products = _frame(store, "stores"), _frame(store, "products")
    sales, stock = _frame(store, "sales"), _frame(store, "stock")
    if sales.empty:
        raise PlanNotReady("Your sales file has no rows yet.")
    if stock.empty:
        raise PlanNotReady("Your stock file has no rows yet.")

    stores["latitude"], stores["longitude"] = stores["latitude"].astype(float), stores["longitude"].astype(float)
    products["unit_price"] = products["unit_price"].astype(float)
    products["pack_size"] = products["pack_size"].astype(int)
    sales["sale_date"] = pd.to_datetime(sales["sale_date"])
    sales["units"] = sales["units"].astype(float)
    as_of = sales["sale_date"].max()

    # Same-weekday average over the lookback window.
    window = pd.date_range(as_of - pd.Timedelta(days=LOOKBACK_DAYS - 1), as_of)
    weeks_per_weekday = pd.Series(window.dayofweek).value_counts().to_dict()
    recent = sales[sales["sale_date"] >= window[0]].assign(weekday=lambda d: d["sale_date"].dt.dayofweek)
    by_day = recent.groupby(["store_id", "product_id", "weekday"])["units"].sum().to_dict()

    pairs = [(s, p) for s in stores["store_id"] for p in products["product_id"]]
    horizon = [as_of + timedelta(days=i) for i in range(1, 8)]
    preds = pd.DataFrame(
        [
            {
                "store_id": s,
                "product_id": p,
                "forecast_date": d,
                "as_of_date": as_of,
                "predicted_units": by_day.get((s, p, d.dayofweek), 0.0) / weeks_per_weekday[d.dayofweek],
            }
            for s, p in pairs
            for d in horizon
        ]
    )

    # Latest stock count per store and product; a pair with no count is planned at zero, and the checks say so.
    stock["snapshot_date"] = pd.to_datetime(stock["snapshot_date"])
    if "in_transit" not in stock:
        stock["in_transit"] = 0
    latest = stock.sort_values("snapshot_date").groupby(["store_id", "product_id"]).last().reset_index()
    inv = pd.DataFrame(pairs, columns=["store_id", "product_id"]).merge(latest, how="left", on=["store_id", "product_id"])
    inv[["on_hand", "in_transit"]] = inv[["on_hand", "in_transit"]].astype(float).fillna(0.0)

    settings = {k: float(v) for k, v in reference.SETTINGS.items()}
    intervals = pd.DataFrame({"product_id": products["product_id"], "ratio_p10": RATIO_P10, "ratio_p90": RATIO_P90})
    gaps = planning.compute_gaps(preds, inv, planning.committed_from_recs(None, as_of.date()), intervals, settings, as_of.date())
    weather = pd.DataFrame(columns=["store_id", "forecast_date", "condition", "event_name", "wind_max_mph", "rain_in", "temp_max_f"])
    run_ts = datetime.combine((as_of + timedelta(days=1)).date(), time(6))
    recs = planning.recommend_transfers(gaps, stores, products, weather, settings, as_of.date(), run_ts)

    app_users = json.loads((Path(__file__).parent / "fixtures.json").read_text())["tables"]["app_users"]
    settings_rows = [{"key": k, "value": str(v)} for k, v in settings.items()] + [{"key": "data_label", "value": "uploaded"}]
    tables = {
        "stores": _records(stores),
        "products": _records(products),
        "settings": settings_rows,
        "app_users": app_users,
        "weather_forecast": [],
        "predictions": _records(preds),
        "inventory_gaps": _records(gaps),
        "transfer_recommendations": _records(recs),
    }
    summary = {
        "as_of": as_of.date().isoformat(),
        "stores": len(stores),
        "products": len(products),
        "transfers": len(recs),
        "short": int((gaps["status"] == "SHORTAGE").sum()),
        "protected_usd": round(float(recs["sales_protected_usd"].sum()), 2) if len(recs) else 0.0,
        "miles": float(recs["distance_miles"].sum()) if len(recs) else 0.0,
    }
    return {"as_of": summary["as_of"], "tables": tables, "summary": summary}


def save(store: IngestStore, plan: dict[str, Any]) -> Path:
    path = store.folder / PLAN_FILE
    path.write_text(json.dumps(plan, default=_json_default))
    return path


def economics(store: IngestStore) -> dict[str, float]:
    p = store.folder / "economics.json"
    return {**DEFAULT_ECONOMICS, **json.loads(p.read_text())} if p.exists() else dict(DEFAULT_ECONOMICS)


def net_benefit(summary: dict[str, Any], econ: dict[str, float]) -> dict[str, float]:
    """Protected sales times the margin, less one truck trip per transfer at the cost per mile. An estimate."""
    margin = summary["protected_usd"] * econ["margin_pct"] / 100
    cost = summary["miles"] * econ["truck_cost_per_mile"]
    return {"margin_usd": round(margin, 2), "trucking_usd": round(cost, 2), "net_usd": round(margin - cost, 2)}
