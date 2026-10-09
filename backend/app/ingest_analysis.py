"""A plain analysis of your uploaded data: how fast each product sells, and how many days its stock lasts.

Sells per day is the last 28 days of sales divided by 28. Days of cover is the latest stock count divided by that.
Short means under a week of cover, Watch means under three weeks, anything else is Plenty. This is a simple
analysis; the forecast in the planner is the model-based one.
"""

from __future__ import annotations

import pandas as pd

from .ingest import IngestStore

WINDOW_DAYS = 28
SHORT_DAYS = 7
WATCH_DAYS = 21


def analyse(store: IngestStore) -> dict | None:
    """The analysis, or None until the stores, products, sales and stock files are all uploaded."""
    saved = {f: store.read(f) for f in ("stores", "products", "sales", "stock")}
    if any(v is None for v in saved.values()):
        return None
    stores = pd.DataFrame(saved["stores"]["rows"])
    products = pd.DataFrame(saved["products"]["rows"])
    sales = pd.DataFrame(saved["sales"]["rows"])
    stock = pd.DataFrame(saved["stock"]["rows"])
    if sales.empty or stock.empty:
        return None

    sales["sale_date"] = pd.to_datetime(sales["sale_date"])
    sales["units"] = sales["units"].astype(float)
    last = sales["sale_date"].max()
    recent = sales[sales["sale_date"] > last - pd.Timedelta(days=WINDOW_DAYS)]
    sold = recent.groupby(["store_id", "product_id"])["units"].sum()

    stock["snapshot_date"] = pd.to_datetime(stock["snapshot_date"])
    latest = stock.sort_values("snapshot_date").groupby(["store_id", "product_id"]).last()["on_hand"].astype(float)

    price = products.set_index("product_id")["unit_price"].astype(float)
    store_name = stores.set_index("store_id")["name"]
    product_name = products.set_index("product_id")["name"]

    pairs = sold.index.union(latest.index)
    rows = []
    for store_id, product_id in pairs:
        per_day = float(sold.get((store_id, product_id), 0.0)) / WINDOW_DAYS
        on_hand = float(latest.get((store_id, product_id), 0.0))
        unit = float(price.get(product_id, 0.0))
        cover = on_hand / per_day if per_day > 0 else None
        if cover is None:
            status = "No sales"
        elif cover < SHORT_DAYS:
            status = "Short"
        elif cover < WATCH_DAYS:
            status = "Watch"
        else:
            status = "Plenty"
        rows.append({
            "store": str(store_name.get(store_id, store_id)), "store_id": store_id,
            "product": str(product_name.get(product_id, product_id)),
            "on_hand": round(on_hand), "sold_per_day": round(per_day, 1),
            "days_of_cover": round(cover, 1) if cover is not None else None, "status": status,
            "stock_value_usd": round(on_hand * unit, 2), "sales_value_usd": round(float(sold.get((store_id, product_id), 0.0)) * unit, 2),
        })

    frame = pd.DataFrame(rows)
    by_store = (frame.groupby(["store_id", "store"]).agg(
        short_items=("status", lambda s: int((s == "Short").sum())),
        stock_value_usd=("stock_value_usd", "sum")).reset_index().sort_values("short_items", ascending=False))
    flagged = frame[frame["status"].isin(["Short", "Watch"])].sort_values(
        ["days_of_cover", "store"], na_position="last").head(50)
    return {
        "as_of": last.date().isoformat(), "window_days": WINDOW_DAYS,
        "stores": len(stores), "products": len(products), "pairs": len(rows),
        "short": int((frame["status"] == "Short").sum()), "watch": int((frame["status"] == "Watch").sum()),
        "sold_units": round(float(recent["units"].sum())),
        "sales_value_usd": round(float(frame["sales_value_usd"].sum()), 2),
        "stock_value_usd": round(float(frame["stock_value_usd"].sum()), 2),
        "by_store": by_store.drop(columns=["store_id"]).to_dict("records"),
        "items": flagged.drop(columns=["store_id"]).to_dict("records"),
    }
