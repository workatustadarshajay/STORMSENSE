"""The analysis turns uploaded sales and stock into days of cover, and says Short, Watch or Plenty."""

from app.ingest import IngestStore, Outcome
from app.ingest_analysis import analyse


def _feed(store, key, rows):
    store.save(key, Outcome(accepted=rows), {})


def test_days_of_cover_from_the_last_28_days_of_sales(tmp_path):
    store = IngestStore(tmp_path)
    assert analyse(store) is None  # nothing uploaded yet
    _feed(store, "stores", [{"store_id": "S01", "name": "Orlando"}])
    _feed(store, "products", [{"product_id": "P01", "name": "Tarp", "unit_price": 20.0}])
    # 28 days at 2 units a day, so 2 a day on average; 10 units on hand is 5 days of cover: Short.
    sales = [{"store_id": "S01", "product_id": "P01", "sale_date": f"2026-10-{d:02d}", "units": 2} for d in range(1, 29)]
    _feed(store, "sales", sales)
    _feed(store, "stock", [{"store_id": "S01", "product_id": "P01", "snapshot_date": "2026-10-28", "on_hand": 10}])
    out = analyse(store)
    item = out["items"][0]
    assert item["sold_per_day"] == 2.0 and item["days_of_cover"] == 5.0 and item["status"] == "Short"
    assert out["short"] == 1 and out["sold_units"] == 56 and out["sales_value_usd"] == 1120.0
    assert out["by_store"][0]["store"] == "Orlando" and out["by_store"][0]["short_items"] == 1


def test_plenty_of_stock_is_not_flagged(tmp_path):
    store = IngestStore(tmp_path)
    _feed(store, "stores", [{"store_id": "S01", "name": "Orlando"}])
    _feed(store, "products", [{"product_id": "P01", "name": "Tarp", "unit_price": 20.0}])
    _feed(store, "sales", [{"store_id": "S01", "product_id": "P01", "sale_date": "2026-10-28", "units": 28}])
    _feed(store, "stock", [{"store_id": "S01", "product_id": "P01", "snapshot_date": "2026-10-28", "on_hand": 500}])
    out = analyse(store)
    assert out["items"] == [] and out["short"] == 0 and out["stock_value_usd"] == 10000.0
