"""Estimated carbon for a stock transfer. A planning estimate, not a measurement.

Assumptions, shown to planners as a footnote in the app:
- A loaded medium-duty truck emits about 0.9 kg CO2e per mile.
- A full truck carries about 200 units of mixed stock.
A move's share of a truck is qty / TRUCK_UNITS, so its estimate is miles x 0.9 x share.
# ponytail: assumes every truck is full; a half-empty trip costs more per unit. Upgrade with real load data.
"""

from __future__ import annotations

KG_CO2E_PER_TRUCK_MILE = 0.9
TRUCK_UNITS = 200


def estimate_kg_co2e(qty: int, distance_miles: int) -> float:
    return round(distance_miles * KG_CO2E_PER_TRUCK_MILE * qty / TRUCK_UNITS, 1)
