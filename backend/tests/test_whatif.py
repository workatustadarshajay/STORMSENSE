"""What-if simulator, tested with a known linear scorer so the expected numbers are exact."""
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from app.whatif import FEATURES, Scenario, apply_scenario, run

AS_OF = date(2026, 10, 8)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "databricks"))


def week(store="S01", product="P01", wind=10.0, rain=0.0) -> pd.DataFrame:
    days = pd.date_range("2026-10-09", periods=7)
    return pd.DataFrame({
        "store_id": store, "product_id": product, "date": days, "store_code": 1, "product_code": 1, "dow": days.dayofweek,
        "month": 10, "is_weekend": 0, "is_holiday": 0, "temp_max_f": 85.0, "rain_in": rain, "wind_max_mph": wind,
        "wind_lead_max": wind, "rain_lead_sum": rain, "temp_lead_delta": 0.0, "sales_lag7": 5.0, "avg7_lag7": 5.0, "avg28_lag7": 5.0,
    })


def linear_scorer(frame: pd.DataFrame) -> np.ndarray:
    """Demand rises with wind and rain: a stand-in for the forecaster that makes the numbers checkable."""
    return (2.0 + 0.1 * frame["wind_max_mph"] + 1.0 * frame["rain_in"]).to_numpy()


def test_features_match_the_library():
    from stormsense_core.features import FEATURES as LIB
    assert FEATURES == LIB


def test_storm_changes_only_its_days():
    base = week()
    storm = apply_scenario(base, Scenario(strength=100, start_day=2, days=2), AS_OF)
    changed = storm.assign(d=pd.to_datetime(storm["date"])).query("wind_max_mph > 10")
    assert list(changed["d"].dt.strftime("%m-%d")) == ["10-11", "10-12"]
    assert changed["wind_max_mph"].iloc[0] == 60.0 and changed["rain_in"].iloc[0] == 5.0


def test_lead_features_follow_the_storm():
    storm = apply_scenario(week(), Scenario(strength=100, start_day=2, days=1), AS_OF)
    day_before = storm.assign(d=pd.to_datetime(storm["date"])).query("d == '2026-10-10'").iloc[0]
    assert day_before["wind_lead_max"] == 60.0  # the storm is one day ahead, so the day before sees it


def test_no_storm_no_loss():
    stock = {("S01", "P01"): 1000.0}
    result = run(week(), Scenario(strength=0, start_day=0, days=1), AS_OF, linear_scorer, stock, {"P01": 100.0}, {})
    assert result["extra_lost_usd"] == 0 and result["extra_demand_units"] == 0


def test_storm_costs_sales_only_beyond_stock():
    prices = {"P01": 100.0}
    names = {"S01": "Orlando", "P01": "1000W generator"}
    tight = run(week(), Scenario(strength=100, start_day=0, days=3), AS_OF, linear_scorer, {("S01", "P01"): 0.0}, prices, names)
    assert tight["extra_demand_units"] > 0 and tight["extra_lost_usd"] > 0
    assert tight["extra_lost_usd"] == round(tight["stock_to_move_units"] * 100.0, 2)  # every missing unit is a lost sale
    row = tight["rows"][0]
    assert row["store"] == "Orlando" and row["product"] == "1000W generator"
    plenty = run(week(), Scenario(strength=100, start_day=0, days=3), AS_OF, linear_scorer, {("S01", "P01"): 1e6}, prices, names)
    assert plenty["extra_lost_usd"] == 0 and plenty["stock_to_move_units"] == 0  # enough stock: the storm costs nothing


def test_stronger_storms_cost_more():
    prices = {"P01": 100.0}
    weak = run(week(), Scenario(strength=30, start_day=0, days=3), AS_OF, linear_scorer, {("S01", "P01"): 0.0}, prices, {})
    strong = run(week(), Scenario(strength=90, start_day=0, days=3), AS_OF, linear_scorer, {("S01", "P01"): 0.0}, prices, {})
    assert strong["extra_lost_usd"] > weak["extra_lost_usd"] > 0


def test_the_window_is_described_in_plain_words():
    result = run(week(), Scenario(strength=50, start_day=2, days=2), AS_OF, linear_scorer, {}, {"P01": 1.0}, {})
    assert result["window"] == "Sunday to Monday"  # 2026-10-11 is a Sunday
