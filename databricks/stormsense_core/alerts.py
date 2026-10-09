"""Official US weather warnings from the National Weather Service, and which of them are new.

The storm trigger calls this every few minutes. Only warnings that can change a stock plan count, and each
warning triggers a plan refresh once, the first time it is seen.
"""

from __future__ import annotations

import pandas as pd
import requests

NWS_ALERTS = "https://api.weather.gov/alerts/active"
# The NWS asks for an identifying User-Agent; a shared key is not needed.
HEADERS = {"User-Agent": "StormSense/1.0 (planning demo; contact via workspace owner)", "Accept": "application/geo+json"}
PLAN_CHANGING = (
    "Hurricane Warning", "Tropical Storm Warning", "Storm Warning", "Extreme Wind Warning",
    "Excessive Heat Warning", "Flash Flood Warning",
)
COLUMNS = ["alert_id", "event", "area", "onset", "severe"]


def parse_alerts(payload: dict) -> pd.DataFrame:
    """One row per active alert in an NWS GeoJSON response; `severe` marks the warnings that can change a plan."""
    rows = []
    for f in payload.get("features", []):
        p = f.get("properties", {})
        rows.append({
            "alert_id": f.get("id") or p.get("id") or "",
            "event": p.get("event", ""),
            "area": p.get("areaDesc", ""),
            "onset": p.get("onset") or p.get("effective") or "",
            "severe": p.get("event", "") in PLAN_CHANGING,
        })
    return pd.DataFrame(rows, columns=COLUMNS)


def new_severe(alerts: pd.DataFrame, seen: set[str]) -> pd.DataFrame:
    """Plan-changing warnings that have not triggered a refresh yet."""
    return alerts[alerts.severe & ~alerts.alert_id.isin(seen)].reset_index(drop=True)


def fetch_alerts(states: tuple[str, ...] = ("FL", "TX", "CA")) -> dict:
    resp = requests.get(NWS_ALERTS, params={"area": ",".join(states)}, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()
