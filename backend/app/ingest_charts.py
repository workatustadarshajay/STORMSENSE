"""Chart data for your uploads: sales and stock by day, stock cover by store, status counts, and what was loaded."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .ingest import FEEDS, IngestStore
from .ingest_analysis import pair_table


def upload_charts(store: IngestStore) -> dict[str, Any]:
    sales = store.read("sales")
    stock = store.read("stock")
    completeness = []
    for key in FEEDS:
        saved = store.read(key)
        completeness.append({"feed": FEEDS[key].title, "kept": len(saved["rows"]) if saved else 0,
                             "refused": saved["refused"] if saved else 0, "loaded": saved is not None})
    out: dict[str, Any] = {"completeness": completeness, "sales_by_day": [], "stock_by_day": [],
                           "cover_by_store": [], "status_counts": {"Short": 0, "Watch": 0, "Plenty": 0, "No sales": 0}}
    if sales:
        df = pd.DataFrame(sales["rows"])
        df["sale_date"] = pd.to_datetime(df["sale_date"])
        daily = df.groupby("sale_date")["units"].apply(lambda s: float(s.astype(float).sum()))
        out["sales_by_day"] = [{"date": d.date().isoformat(), "units": round(v)} for d, v in daily.items()]
    if stock:
        df = pd.DataFrame(stock["rows"])
        df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
        daily = df.groupby("snapshot_date")["on_hand"].apply(lambda s: float(s.astype(float).sum()))
        out["stock_by_day"] = [{"date": d.date().isoformat(), "on_hand": round(v)} for d, v in daily.items()]
    pairs = pair_table(store)
    if pairs is not None and len(pairs):
        for status in out["status_counts"]:
            out["status_counts"][status] = int((pairs["status"] == status).sum())
        # The lowest days of stock left in each store: the number that matters most in a storm.
        known = pairs.dropna(subset=["days_of_cover"])
        if len(known):
            lowest = known.groupby("store")["days_of_cover"].min().sort_values()
            out["cover_by_store"] = [{"store": s, "days": round(float(v), 1)} for s, v in lowest.items()]
    return out
