"""Builds backend/app/fixtures.json: the same tables the notebooks produce, for running the app with no workspace.

    python databricks/scripts/make_fixtures.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "databricks"))

from stormsense_core import backtest, features, model, planning, reference, synth  # noqa: E402

END = date(2026, 10, 7)  # Wednesday; the mock source shifts dates by whole weeks, so weekdays stay right
USERS = [  # fictional accounts for running locally
    ("ava.planner@stormsense.test", "Ava Planner", "planner"),
    ("sam.viewer@stormsense.test", "Sam Viewer", "viewer"),
    ("jordan.admin@stormsense.test", "Jordan Admin", "admin"),
]


def records(df: pd.DataFrame) -> list[dict]:
    return df.astype(object).where(df.notna(), None).to_dict("records")


def main() -> None:
    t = synth.generate(END).tables
    feats = features.build_features(t["sales_history"], t["weather_observed"], t["weather_forecast"], END)
    trained = model.fit(feats)
    fut = feats[feats["is_future"]].copy()
    fut["predicted_units"] = trained.model.predict(fut[features.FEATURES]).clip(min=0).round(2)
    preds = fut.rename(columns={"date": "forecast_date"})[["store_id", "product_id", "forecast_date", "predicted_units"]]
    preds = preds.assign(as_of_date=END)
    inv = t["inventory_snapshot"]
    inv = inv[inv["snapshot_date"] == END]
    settings = {k: float(v) for k, v in reference.SETTINGS.items()}
    gaps = planning.compute_gaps(preds, inv, planning.committed_from_recs(None, END), trained.intervals, settings, END)
    run_ts = datetime(END.year, END.month, END.day) + timedelta(days=1, hours=6)
    recs = planning.recommend_transfers(gaps, reference.stores_df(), reference.products_df(), t["weather_forecast"], settings, END, run_ts)

    def stable_id(r: pd.Series) -> str:
        key = f"{r.as_of_date}|{r.source_store_id}|{r.dest_store_id}|{r.product_id}"
        return "TR-" + hashlib.sha1(key.encode()).hexdigest()[:10].upper()

    recs["rec_id"] = recs.apply(stable_id, axis=1)

    # A few decisions from last week, so History has something real to show.
    past = recs.sample(3, random_state=4).copy()
    past["as_of_date"] = END - timedelta(days=7)
    past["rec_id"] = past.apply(stable_id, axis=1)
    past["created_at"] = run_ts - timedelta(days=7)
    past["status"] = ["APPROVED", "APPROVED", "REJECTED"]
    past["decided_by"] = ["ava.planner@stormsense.test", "jordan.admin@stormsense.test", "ava.planner@stormsense.test"]
    past["decided_at"] = [run_ts - timedelta(days=7) + timedelta(hours=h) for h in (2, 3, 4)]
    past["decision_note"] = [None, "Route confirmed with the store", "Truck unavailable this week"]
    past["urgency"] = "NORMAL"
    recs = pd.concat([recs, past], ignore_index=True)

    wx = t["weather_forecast"]
    day = pd.to_datetime(wx["forecast_date"])
    wx = wx[(day > pd.Timestamp(END)) & (day <= pd.Timestamp(END) + pd.Timedelta(days=7))]
    out = {
        "as_of": END.isoformat(),
        "tables": {
            "stores": records(reference.stores_df()[["store_id", "name", "city", "region"]]),
            "products": records(reference.products_df()[["product_id", "name", "name_plural", "weather_driver", "unit_price"]]),
            "settings": records(reference.settings_df()),
            "app_users": [{"email": e, "display_name": n, "role": r} for e, n, r in USERS],
            "weather_forecast": records(wx[["store_id", "forecast_date", "temp_max_f", "rain_in", "wind_max_mph", "condition",
                                           "event_name"]]),
            "predictions": records(preds),
            "inventory_gaps": records(gaps),
            "transfer_recommendations": records(recs),
            "backtest_results": records(backtest.replay_all(t["weather_observed"], t["sales_history"], t["inventory_snapshot"],
                                                             reference.products_df(), reference.stores_df())),
        },
    }
    target = ROOT / "backend" / "app" / "fixtures.json"
    target.write_text(json.dumps(out, default=str, indent=None, separators=(",", ":")))
    print(f"wrote {target.relative_to(ROOT)} ({target.stat().st_size // 1024} KB): {len(recs)} transfers, {len(gaps)} stock rows")


if __name__ == "__main__":
    main()
