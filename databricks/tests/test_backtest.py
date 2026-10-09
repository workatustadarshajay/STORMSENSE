"""The backtest counts lost sales in a storm and what a nearby store with spare stock could have covered."""
from datetime import date

import pandas as pd
from stormsense_core.backtest import replay

PRODUCTS = pd.DataFrame([{"product_id": "P01", "unit_price": 10.0}])
STORES = pd.DataFrame([
    {"store_id": "A", "latitude": 28.0, "longitude": -81.0},   # hit by the storm, runs out
    {"store_id": "B", "latitude": 28.5, "longitude": -81.0},   # close, not hit, has spare stock
    {"store_id": "C", "latitude": 35.0, "longitude": -81.0},   # about 460 miles away, has spare stock
])
EVENT = {"event_name": "Test Storm", "start": pd.Timestamp("2026-10-01"), "end": pd.Timestamp("2026-10-02"), "stores": ["A"]}


def frames(a_stock, a_sold, b_stock, b_sold, c_stock=0, c_sold=0):
    inventory = pd.DataFrame([
        {"store_id": "A", "product_id": "P01", "snapshot_date": date(2026, 9, 30), "on_hand": a_stock},
        {"store_id": "B", "product_id": "P01", "snapshot_date": date(2026, 9, 30), "on_hand": b_stock},
        {"store_id": "C", "product_id": "P01", "snapshot_date": date(2026, 9, 30), "on_hand": c_stock},
    ])
    sales = pd.DataFrame([
        {"store_id": "A", "product_id": "P01", "sale_date": date(2026, 10, 1), "units": a_sold},
        {"store_id": "B", "product_id": "P01", "sale_date": date(2026, 10, 1), "units": b_sold},
        {"store_id": "C", "product_id": "P01", "sale_date": date(2026, 10, 1), "units": c_sold},
    ])
    return sales, inventory


def test_nearby_spare_stock_protects_the_lost_sales():
    sales, inventory = frames(a_stock=10, a_sold=25, b_stock=40, b_sold=5)
    out = replay(EVENT, sales, inventory, PRODUCTS, STORES)
    assert out["lost_units"] == 15 and out["lost_usd"] == 150.0
    assert out["protected_units"] == 15 and out["protected_usd"] == 150.0 and out["share_protected"] == 1.0


def test_a_store_too_far_away_protects_nothing():
    sales, inventory = frames(a_stock=10, a_sold=25, b_stock=0, b_sold=0, c_stock=40, c_sold=5)
    out = replay(EVENT, sales, inventory, PRODUCTS, STORES)
    assert out["lost_units"] == 15 and out["protected_units"] == 0 and out["share_protected"] == 0.0
