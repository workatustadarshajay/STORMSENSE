"""Learning from planner decisions: rejected routes are ranked lower, and recent decisions count most.

Each rejection adds weight that halves every HALF_LIFE_DAYS. The penalty is 1 + total weight, capped, so a route
rejected twice last week ranks well below a route that was never rejected, and an old rejection fades away.
The learned penalties only change the order of the recommended sources. They never create or remove a move.
"""
from __future__ import annotations

from datetime import date, datetime

import pandas as pd

REASONS = {
    "TRUCK_UNAVAILABLE": "truck unavailable",
    "STORE_CLOSED": "store closed",
    "ALREADY_COVERED": "already covered",
    "ROUTE_TOO_SLOW": "route too slow",
    "OTHER": "other",
}
WINDOW_DAYS = 60
HALF_LIFE_DAYS = 14.0
MAX_PENALTY = 4.0
COLUMNS = ["source_store_id", "dest_store_id", "product_id", "penalty", "rejections", "last_reason", "last_rejected"]


def compute_route_preferences(rejections: pd.DataFrame, as_of: date, now: datetime | None = None) -> pd.DataFrame:
    """rejections: one row per rejected transfer with source_store_id, dest_store_id, product_id, reason_code, decided_at.

    Ages are measured to `now` (the run time), so a planner's decision made today counts today, even though the
    stock data is dated yesterday.
    """
    if rejections.empty:
        return pd.DataFrame(columns=COLUMNS)
    r = rejections.copy()
    r["decided_at"] = pd.to_datetime(r["decided_at"])
    reference = pd.Timestamp(now) if now is not None else pd.Timestamp(as_of) + pd.Timedelta(days=1)
    age = (reference - r["decided_at"]).dt.total_seconds() / 86400
    r = r[(age >= 0) & (age <= WINDOW_DAYS)].assign(age=age)
    if r.empty:
        return pd.DataFrame(columns=COLUMNS)
    r["weight"] = 0.5 ** (r["age"] / HALF_LIFE_DAYS)
    rows = []
    for (src, dst, pid), g in r.groupby(["source_store_id", "dest_store_id", "product_id"]):
        latest = g.sort_values("decided_at").iloc[-1]
        rows.append({
            "source_store_id": src, "dest_store_id": dst, "product_id": pid,
            "penalty": round(min(MAX_PENALTY, 1.0 + float(g["weight"].sum())), 3),
            "rejections": int(len(g)),
            "last_reason": REASONS.get(latest["reason_code"], "other") if isinstance(latest["reason_code"], str) else "",
            "last_rejected": latest["decided_at"],
        })
    return pd.DataFrame(rows, columns=COLUMNS)
