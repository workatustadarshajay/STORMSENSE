"""Demo weather: a storm placed on the Florida stores for the next two days, so planners can see one without waiting.

It changes what the weather-driven screens show (alerts, readiness, store forecast weather). It does not change the
transfers: those come from the live plan the daily job built, and the app says so.
"""

from __future__ import annotations

from typing import Literal

from .sources.base import Row

WeatherSource = Literal["live", "demo"]
DEMO_REGION = "Florida"
DEMO_FIRST_DAY = 1   # index into the forecast days: 0 is the first forecast day, so 1 is tomorrow
DEMO_DAYS = 2
DEMO_WIND_MPH = 58.0
DEMO_RAIN_IN = 2.5
DEMO_NAME = "Demo storm"


def with_demo_storm(rows: list[Row], region_of: dict[str, str]) -> list[Row]:
    """Copies of the weather rows, with the demo storm on the Florida stores for the demo days."""
    days = sorted({str(r["forecast_date"]) for r in rows})
    storm_days = set(days[DEMO_FIRST_DAY:DEMO_FIRST_DAY + DEMO_DAYS])
    out = []
    for r in rows:
        row = dict(r)
        if region_of.get(r["store_id"]) == DEMO_REGION and str(r["forecast_date"]) in storm_days:
            row.update(condition="storm", wind_max_mph=max(float(r["wind_max_mph"] or 0), DEMO_WIND_MPH),
                       rain_in=max(float(r["rain_in"] or 0), DEMO_RAIN_IN), event_name=DEMO_NAME)
        out.append(row)
    return out
