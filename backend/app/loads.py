"""Truck consolidation: moves on the same route can share a truck. This shows how many trips that would save.

Today each move is one truck trip (the same cost model as the business impact page). A truck carries
TRUCK_UNITS units. Moves on one route sharing a truck need ceil(total units / TRUCK_UNITS) trips. This only
suggests loads; it never changes a move.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from .carbon import KG_CO2E_PER_TRUCK_MILE, TRUCK_UNITS


def plan_loads(moves: list[Any], cost_per_mile: float) -> dict[str, Any]:
    routes: dict[tuple[str, str], list[Any]] = defaultdict(list)
    for m in moves:
        routes[(m.from_store.id, m.to_store.id)].append(m)
    out = []
    for group in routes.values():
        units = sum(int(m.qty) for m in group)
        miles = max(int(m.distance_miles) for m in group)
        trips_before = len(group)
        trips_after = math.ceil(units / TRUCK_UNITS)
        saved = max(0, trips_before - trips_after)
        out.append({
            "from_store": group[0].from_store.name, "to_store": group[0].to_store.name, "miles": miles, "units": units,
            "moves": [{"id": m.id, "product": m.product.name, "qty": int(m.qty)} for m in group],
            "trips_now": trips_before, "trips_together": trips_after,
            "saved_usd": round(saved * miles * cost_per_mile, 2), "saved_kg": round(saved * miles * KG_CO2E_PER_TRUCK_MILE, 1),
        })
    out.sort(key=lambda r: (-r["saved_usd"], r["from_store"]))
    return {
        "routes": out,
        "trips_now": sum(r["trips_now"] for r in out),
        "trips_together": sum(r["trips_together"] for r in out),
        "saved_usd": round(sum(r["saved_usd"] for r in out), 2),
        "saved_kg": round(sum(r["saved_kg"] for r in out), 1),
        "cost_per_mile": cost_per_mile,
        "truck_units": TRUCK_UNITS,
    }
