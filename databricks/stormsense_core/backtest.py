"""Replays past storms with what really sold, and asks how much of the lost sales planned moves could have protected.

Method, stated plainly on the page:
- Stock at the start of a storm is the last on-hand count before it.
- Lost sales are the units sold during the storm beyond that stock. No restocking during the storm is assumed.
- Protection is a move from the nearest store with stock left over after its own sales, within the distance limit.
This uses what really sold, so it is an upper bound: the best planning could have done with perfect information.
# ponytail: ignores pack sizes and truck limits, so it overstates protection slightly. Add them when a planner asks.
"""

from __future__ import annotations

import pandas as pd

from .planning import haversine_miles

COLUMNS = ["event_name", "start_date", "end_date", "stores", "lost_units", "lost_usd",
           "protected_units", "protected_usd", "share_protected"]


def storm_events(observed: pd.DataFrame) -> list[dict]:
    """Each named weather event, its dates, and the stores it reached."""
    named = observed.dropna(subset=["event_name"])
    return [
        {"event_name": name, "start": g.obs_date.min(), "end": g.obs_date.max(), "stores": sorted(g.store_id.unique())}
        for name, g in named.groupby("event_name")
    ]


def replay(event: dict, sales: pd.DataFrame, inventory: pd.DataFrame, products: pd.DataFrame, stores: pd.DataFrame,
           max_miles: float = 300.0) -> dict:
    """Lost sales in the storm, and how much a nearby store with spare stock could have covered."""
    start, end = pd.Timestamp(event["start"]), pd.Timestamp(event["end"])
    price = products.set_index("product_id")["unit_price"]

    stock = (inventory[pd.to_datetime(inventory.snapshot_date) < start]
             .sort_values("snapshot_date").groupby(["store_id", "product_id"]).last()["on_hand"])
    in_storm = sales[(pd.to_datetime(sales.sale_date) >= start) & (pd.to_datetime(sales.sale_date) <= end)]
    sold = in_storm.groupby(["store_id", "product_id"])["units"].sum()
    frame = pd.DataFrame({"stock": stock, "sold": sold}).fillna(0.0)
    frame["lost"] = (frame.sold - frame.stock).clip(lower=0)
    frame["spare"] = (frame.stock - frame.sold).clip(lower=0)
    frame = frame.reset_index()
    loc = stores.set_index("store_id")[["latitude", "longitude"]]
    hit = set(event["stores"])

    protected_units, protected_usd = 0.0, 0.0
    for pid, g in frame.groupby("product_id"):
        spare = {r.store_id: r.spare for r in g.itertuples() if r.spare > 0}
        for need in g[g.store_id.isin(hit) & (g.lost > 0)].sort_values("lost", ascending=False).itertuples():
            left = need.lost
            near = sorted(
                (s for s in spare if s != need.store_id and spare[s] > 0),
                key=lambda s: haversine_miles(loc.at[s, "latitude"], loc.at[s, "longitude"],
                                              loc.at[need.store_id, "latitude"], loc.at[need.store_id, "longitude"]),
            )
            for s in near:
                miles = haversine_miles(loc.at[s, "latitude"], loc.at[s, "longitude"],
                                        loc.at[need.store_id, "latitude"], loc.at[need.store_id, "longitude"])
                if miles > max_miles or left <= 0:
                    continue
                take = min(left, spare[s])
                spare[s] -= take
                left -= take
                protected_units += take
                protected_usd += take * float(price[pid])
    lost_mask = frame.store_id.isin(hit)
    lost_units = float(frame.loc[lost_mask, "lost"].sum())
    lost_usd = float((frame.loc[lost_mask, "lost"] * frame.loc[lost_mask, "product_id"].map(price)).sum())
    return {
        "event_name": event["event_name"], "start_date": start.date(), "end_date": end.date(), "stores": len(hit),
        "lost_units": round(lost_units), "lost_usd": round(lost_usd, 2),
        "protected_units": round(protected_units),
        "protected_usd": round(protected_usd, 2),
        "share_protected": round(protected_usd / lost_usd, 3) if lost_usd else 0.0,
    }


def replay_all(observed: pd.DataFrame, sales: pd.DataFrame, inventory: pd.DataFrame, products: pd.DataFrame,
               stores: pd.DataFrame) -> pd.DataFrame:
    rows = [replay(ev, sales, inventory, products, stores) for ev in storm_events(observed)]
    return pd.DataFrame(rows, columns=COLUMNS).sort_values("lost_usd", ascending=False).reset_index(drop=True)
