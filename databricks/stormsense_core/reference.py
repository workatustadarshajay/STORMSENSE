"""Reference data: stores, products and planning settings."""
from __future__ import annotations

import pandas as pd

# (store_id, name, city, region, latitude, longitude, time_zone, size_factor)
_STORES = [
    ("S01", "Orlando", "Orlando", "Florida", 28.5383, -81.3792, "America/New_York", 1.15),
    ("S02", "Tampa", "Tampa", "Florida", 27.9506, -82.4572, "America/New_York", 1.25),
    ("S03", "Miami", "Miami", "Florida", 25.7617, -80.1918, "America/New_York", 1.30),
    ("S04", "Jacksonville", "Jacksonville", "Florida", 30.3322, -81.6557, "America/New_York", 1.00),
    ("S05", "Houston", "Houston", "Texas", 29.7604, -95.3698, "America/Chicago", 1.40),
    ("S06", "Dallas", "Dallas", "Texas", 32.7767, -96.7970, "America/Chicago", 1.30),
    ("S07", "Austin", "Austin", "Texas", 30.2672, -97.7431, "America/Chicago", 1.00),
    ("S08", "Los Angeles", "Los Angeles", "California", 34.0522, -118.2437, "America/Los_Angeles", 1.45),
    ("S09", "San Diego", "San Diego", "California", 32.7157, -117.1611, "America/Los_Angeles", 1.00),
    ("S10", "Sacramento", "Sacramento", "California", 38.5816, -121.4944, "America/Los_Angeles", 0.90),
]

# (product_id, name, name_plural, category, unit_cost, unit_price, pack_size, base_daily_rate, weather_driver)
_PRODUCTS = [
    ("P01", "1000W generator", "1000W generators", "Storm power", 310.0, 499.0, 1, 1.6, "wind"),
    ("P02", "4x8 plywood sheet", "4x8 plywood sheets", "Building materials", 24.0, 41.0, 10, 6.0, "wind"),
    ("P03", "20x30 tarp", "20x30 tarps", "Storm cover", 8.0, 19.0, 5, 5.0, "rain"),
    ("P04", "Submersible pump", "submersible pumps", "Water control", 105.0, 179.0, 1, 1.2, "rain"),
    ("P05", "120-quart cooler", "120-quart coolers", "Outdoor", 52.0, 99.0, 2, 2.2, "heat"),
]

SETTINGS = {
    "safety_stock_days": 2.0,
    "surplus_threshold_days": 21.0,
    "urgent_threshold_days": 2.0,
    "urgent_lost_sales_usd": 5000.0,
    "max_transfer_distance_miles": 300.0,
    "min_transfer_qty": 10.0,
    "forecast_horizon_days": 7.0,
}

# Where the demo data comes from, shown to planners as a small label.
DATA_LABEL = "sample"


def stores_df() -> pd.DataFrame:
    return pd.DataFrame(
        _STORES,
        columns=["store_id", "name", "city", "region", "latitude", "longitude", "time_zone", "size_factor"],
    )


def products_df() -> pd.DataFrame:
    return pd.DataFrame(
        _PRODUCTS,
        columns=[
            "product_id", "name", "name_plural", "category", "unit_cost", "unit_price",
            "pack_size", "base_daily_rate", "weather_driver",
        ],
    )


def settings_df() -> pd.DataFrame:
    rows = [(k, v) for k, v in SETTINGS.items()] + [("data_label", DATA_LABEL)]
    return pd.DataFrame(rows, columns=["key", "value"]).astype({"value": "string"})
