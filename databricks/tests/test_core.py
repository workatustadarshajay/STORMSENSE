import pandas as pd
import pytest
from conftest import END
from stormsense_core import planning, reference, synth, weather
from stormsense_core.features import FEATURES


def test_sample_data_is_reproducible():
    a, b = synth.generate(END).tables, synth.generate(END).tables
    pd.testing.assert_frame_equal(a["sales_history"], b["sales_history"])


def test_history_has_named_events_and_a_year_of_days(pipeline):
    t = pipeline["tables"]
    assert t["sales_history"]["sale_date"].nunique() == synth.HISTORY_DAYS
    past = t["weather_observed"]["event_name"].dropna().unique()
    assert len(past) >= 4
    fc = t["weather_forecast"]
    assert {"storm", "heat"} <= set(fc["condition"])  # something to react to in the upcoming week


def test_demand_follows_weather(pipeline):
    """Generators sell more in the day or two before a storm; coolers sell more in heat."""
    t = pipeline["tables"]
    wx = t["weather_observed"].rename(columns={"obs_date": "sale_date"})
    s = t["sales_history"].merge(wx, on=["store_id", "sale_date"])
    gen = s[s.product_id == "P01"]
    assert gen[gen.condition == "storm"].units.mean() > 3 * gen[gen.condition == "clear"].units.mean()
    cool = s[s.product_id == "P05"]
    assert cool[cool.condition == "heat"].units.mean() > 1.3 * cool[cool.condition == "clear"].units.mean()


def test_model_beats_both_baselines_on_held_out_month(pipeline):
    m = pipeline["trained"].metrics
    assert m["wape_model"] < m["wape_same_as_last_week"]
    assert m["wape_model"] < m["wape_trailing_28d_avg"]


def test_split_is_by_time_and_features_exclude_the_target(pipeline):
    tr = pipeline["trained"]
    assert tr.validation_start == pd.Timestamp(END) - pd.Timedelta(days=27)
    assert "units" not in FEATURES
    f = pipeline["feats"]
    row = f[~f.is_future].iloc[100]  # lag features equal sales exactly 7 days earlier
    earlier = f[(f.store_id == row.store_id) & (f.product_id == row.product_id) & (f.date == row.date - pd.Timedelta(days=7))]
    assert row.sales_lag7 == earlier.units.iloc[0]


def test_intervals_come_from_validation_residuals(pipeline):
    iv = pipeline["trained"].intervals
    assert len(iv) == 5 and (iv.ratio_p10 < 1).all() and (iv.ratio_p90 > 1).all()


def test_latest_stock_has_shortage_and_surplus(pipeline):
    assert {"SHORTAGE", "SURPLUS"} <= set(pipeline["gaps"].status)


def test_recommendations_respect_the_rules(pipeline):
    recs, gaps, s = pipeline["recs"], pipeline["gaps"], pipeline["settings"]
    prod = reference.products_df().set_index("product_id")
    assert len(recs) >= 5 and (recs.status == "PENDING").all()
    assert (recs.qty >= s["min_transfer_qty"]).all() and (recs.distance_miles <= s["max_transfer_distance_miles"]).all()
    assert (recs.qty % recs.product_id.map(prod.pack_size) == 0).all()
    given = recs.groupby(["source_store_id", "product_id"]).qty.sum()
    spare = gaps.set_index(["store_id", "product_id"]).spare_units
    for key, qty in given.items():
        assert qty <= spare[key] + 1e-6, f"{key} gives away more than it can spare"
    assert not recs.duplicated(["source_store_id", "dest_store_id", "product_id"]).any()
    assert recs.rec_id.is_unique and recs.reason.str.contains("this week and has").all()
    sources = set(zip(recs.source_store_id, recs.product_id))
    assert sources.isdisjoint(zip(recs.dest_store_id, recs.product_id))  # no store both gives and receives a product


def test_approved_transfers_count_as_incoming_stock(pipeline):
    recs, t = pipeline["recs"].copy(), pipeline
    approved = recs.assign(status="APPROVED")
    again = planning.compute_gaps(t["preds"], t["inv"], planning.committed_from_recs(approved, END),
                                  t["trained"].intervals, t["settings"], END)
    before, after = t["gaps"].set_index(["store_id", "product_id"]), again.set_index(["store_id", "product_id"])
    assert after.shortfall_units.sum() < before.shortfall_units.sum()
    rerun = planning.recommend_transfers(again, reference.stores_df(), reference.products_df(),
                                         t["tables"]["weather_forecast"], t["settings"], END, pd.Timestamp("2026-10-08 06:00"))
    assert len(rerun) < len(recs)  # already-approved moves are not recommended again


@pytest.mark.parametrize("wind,rain,temp,expected", [(60, 1, 80, "storm"), (20, 2, 80, "heavy_rain"),
                                                     (10, 0, 100, "heat"), (10, 0.5, 80, "rain"), (10, 0, 80, "clear")])
def test_classify(wind, rain, temp, expected):
    assert weather.classify(wind, rain, temp) == expected


def test_parse_nws_grid():
    grid = {"properties": {
        "temperature": {"values": [{"validTime": "2026-10-08T12:00:00+00:00/PT6H", "value": 30.0},
                                   {"validTime": "2026-10-08T18:00:00+00:00/PT6H", "value": 20.0}]},
        "windGust": {"values": [{"validTime": "2026-10-08T12:00:00+00:00/PT3H", "value": 100.0}]},
        "quantitativePrecipitation": {"values": [{"validTime": "2026-10-08T12:00:00+00:00/PT6H", "value": 25.4}]},
    }}
    d = weather.parse_nws_grid(grid).iloc[0]
    assert d.temp_max_f == pytest.approx(86.0) and d.temp_min_f == pytest.approx(68.0)
    assert d.wind_max_mph == pytest.approx(62.1, abs=0.1) and d.rain_in == pytest.approx(1.0)


def test_table_definitions_are_valid_sql_strings():
    """Comments with apostrophes once broke setup on the workspace; every literal must close properly."""
    import re

    from stormsense_core.tables import TABLES, create_sql

    for name, table in TABLES.items():
        sql = create_sql(f"`c`.`s`.`{name}`", table)
        literals = re.findall(r"'((?:[^'\\]|\\.)*)'", sql)
        assert len(literals) == len(table.columns) + 1, name  # one per column comment plus the table comment
        assert sql.count("'") - sql.count("\\'") == 2 * len(literals), name  # no stray quote outside a literal
    assert "planner\\'s" in create_sql("t", TABLES["transfer_recommendations"])


def test_nws_days_are_store_local_not_utc():
    """A Sunday 8 PM Eastern storm is 00:00 UTC Monday; it must still be labelled Sunday."""
    from stormsense_core import weather

    grid = {"properties": {
        "temperature": {"values": [{"validTime": "2026-10-12T00:00:00+00:00/PT1H", "value": 25.0}]},
        "windGust": {"values": [{"validTime": "2026-10-12T00:00:00+00:00/PT1H", "value": 80.0}]},
        "quantitativePrecipitation": {"values": [{"validTime": "2026-10-12T00:00:00+00:00/PT1H", "value": 0.0}]},
    }}
    utc = weather.parse_nws_grid(grid, tz="UTC")
    eastern = weather.parse_nws_grid(grid, tz="America/New_York")
    assert str(utc.iloc[0].forecast_date) == "2026-10-12"
    assert str(eastern.iloc[0].forecast_date) == "2026-10-11"  # Sunday evening Eastern


def test_rejected_routes_rank_lower_and_say_why():
    """A source whose route was rejected recently is tried after a farther source, and the reason says why."""
    from datetime import date, datetime

    from stormsense_core import planning
    from stormsense_core.feedback import compute_route_preferences

    rej = pd.DataFrame([
        {"source_store_id": "S04", "dest_store_id": "S01", "product_id": "P01", "reason_code": "TRUCK_UNAVAILABLE",
         "decided_at": "2026-10-06 15:00:00"},
        {"source_store_id": "S04", "dest_store_id": "S01", "product_id": "P01", "reason_code": "TRUCK_UNAVAILABLE",
         "decided_at": "2026-10-07 15:00:00"},
    ])
    prefs = compute_route_preferences(rej, date(2026, 10, 8))
    assert prefs.iloc[0].penalty > 2.5 and prefs.iloc[0].rejections == 2 and prefs.iloc[0].last_reason == "truck unavailable"
    old = compute_route_preferences(rej.assign(decided_at="2026-07-01 12:00:00"), date(2026, 10, 8))
    assert old.empty  # outside the 60-day window: forgotten
    today = compute_route_preferences(rej.iloc[[1]].assign(decided_at="2026-10-09 09:30:00"), date(2026, 10, 8),
                                      now=datetime(2026, 10, 9, 10, 0))
    assert len(today) == 1 and today.iloc[0].rejections == 1  # a decision made today, after the stock date, still counts

    st = pd.DataFrame([
        {"store_id": "S01", "name": "Orlando", "latitude": 28.54, "longitude": -81.38, "city": "", "region": "",
         "time_zone": "", "size_factor": 1.0},
        {"store_id": "S04", "name": "Jacksonville", "latitude": 30.33, "longitude": -81.66, "city": "", "region": "",
         "time_zone": "", "size_factor": 1.0},
        {"store_id": "S03", "name": "Miami", "latitude": 25.76, "longitude": -80.19, "city": "", "region": "",
         "time_zone": "", "size_factor": 1.0},
    ])
    pr = reference.products_df().iloc[[0]].copy()
    gaps = pd.DataFrame([
        {"as_of_date": date(2026, 10, 8), "store_id": "S01", "product_id": "P01", "status": "SHORTAGE", "available": 5.0,
         "forecast_units": 50.0, "forecast_p10": 40.0, "forecast_p90": 60.0, "avg_daily": 7.0, "safety_stock": 14.0,
         "days_of_cover": 0.7, "runs_low_date": date(2026, 10, 9), "stockout_date": date(2026, 10, 10),
         "shortfall_units": 60.0, "shortfall_p10": 50.0, "shortfall_p90": 70.0, "lost_units": 45.0, "spare_units": 0.0},
        {"as_of_date": date(2026, 10, 8), "store_id": "S04", "product_id": "P01", "status": "SURPLUS", "available": 200.0,
         "forecast_units": 20.0, "forecast_p10": 16.0, "forecast_p90": 24.0, "avg_daily": 3.0, "safety_stock": 6.0,
         "days_of_cover": 30.0, "runs_low_date": None, "stockout_date": None, "shortfall_units": 0.0, "shortfall_p10": 0.0,
         "shortfall_p90": 0.0, "lost_units": 0.0, "spare_units": 120.0},
        {"as_of_date": date(2026, 10, 8), "store_id": "S03", "product_id": "P01", "status": "SURPLUS", "available": 200.0,
         "forecast_units": 20.0, "forecast_p10": 16.0, "forecast_p90": 24.0, "avg_daily": 3.0, "safety_stock": 6.0,
         "days_of_cover": 30.0, "runs_low_date": None, "stockout_date": None, "shortfall_units": 0.0, "shortfall_p10": 0.0,
         "shortfall_p90": 0.0, "lost_units": 0.0, "spare_units": 120.0},
    ])
    settings = {"safety_stock_days": 2.0, "surplus_threshold_days": 21.0, "urgent_threshold_days": 2.0,
                "urgent_lost_sales_usd": 5000.0, "max_transfer_distance_miles": 300.0, "min_transfer_qty": 10.0,
                "forecast_horizon_days": 7.0}
    wx = pd.DataFrame({"store_id": ["S01"], "forecast_date": [pd.Timestamp("2026-10-09")], "condition": ["clear"],
                       "temp_max_f": [85.0], "rain_in": [0.0], "wind_max_mph": [5.0], "event_name": [None]})
    base = planning.recommend_transfers(gaps, st, pr, wx, settings, date(2026, 10, 8), datetime(2026, 10, 9, 6))
    learned = planning.recommend_transfers(gaps, st, pr, wx, settings, date(2026, 10, 8), datetime(2026, 10, 9, 6),
                                           route_preferences=prefs)
    assert not base.empty and not learned.empty
    assert base.iloc[0].source_store_id == "S04"  # the nearer source wins with no feedback
    assert learned.iloc[0].source_store_id == "S03"  # rejected route ranked lower
    assert "Jacksonville is closer, but a planner rejected that route recently." in learned.iloc[0].reason
    assert "Ranked lower" not in learned.iloc[0].reason  # the chosen route was never rejected
    # Learning reorders, never removes: when the rejected route is the only option, it is still offered, with the reason.
    only_rejected = planning.recommend_transfers(gaps[gaps.store_id != "S03"], st, pr, wx, settings, date(2026, 10, 8),
                                                 datetime(2026, 10, 9, 6), route_preferences=prefs)
    assert only_rejected.iloc[0].source_store_id == "S04"
    assert "Ranked lower" in only_rejected.iloc[0].reason and "truck unavailable" in only_rejected.iloc[0].reason
    assert "Ranked lower" not in base.iloc[0].reason


def test_a_farther_source_says_why_the_closer_store_was_not_used():
    """The reason names the nearest closer store and why it was passed over: short too, or no spare stock."""
    from datetime import date, datetime

    from stormsense_core import planning

    st = pd.DataFrame([
        {"store_id": "S01", "name": "Orlando", "latitude": 28.54, "longitude": -81.38, "city": "", "region": "",
         "time_zone": "", "size_factor": 1.0},
        {"store_id": "S04", "name": "Jacksonville", "latitude": 30.33, "longitude": -81.66, "city": "", "region": "",
         "time_zone": "", "size_factor": 1.0},
        {"store_id": "S03", "name": "Miami", "latitude": 25.76, "longitude": -80.19, "city": "", "region": "",
         "time_zone": "", "size_factor": 1.0},
    ])
    pr = reference.products_df().iloc[[0]].copy()

    def gap(store, status, spare):
        return {"as_of_date": date(2026, 10, 8), "store_id": store, "product_id": "P01", "status": status,
                "available": 200.0 if spare else 5.0,
                "forecast_units": 20.0, "forecast_p10": 16.0, "forecast_p90": 24.0, "avg_daily": 3.0, "safety_stock": 6.0,
                "days_of_cover": 30.0 if spare else 0.7, "runs_low_date": None if spare else date(2026, 10, 9),
                "stockout_date": None if spare else date(2026, 10, 10), "shortfall_units": 0.0 if spare else 60.0,
                "shortfall_p10": 0.0 if spare else 50.0, "shortfall_p90": 0.0 if spare else 70.0,
                "lost_units": 0.0 if spare else 45.0, "spare_units": 120.0 if spare else 0.0}

    settings = {"safety_stock_days": 2.0, "surplus_threshold_days": 21.0, "urgent_threshold_days": 2.0,
                "urgent_lost_sales_usd": 5000.0, "max_transfer_distance_miles": 300.0, "min_transfer_qty": 10.0,
                "forecast_horizon_days": 7.0}
    wx = pd.DataFrame({"store_id": ["S01"], "forecast_date": [pd.Timestamp("2026-10-09")], "condition": ["clear"],
                       "temp_max_f": [85.0], "rain_in": [0.0], "wind_max_mph": [5.0], "event_name": [None]})

    # Jacksonville is also short: Miami supplies, and the reason says Jacksonville is short too.
    gaps = pd.DataFrame([gap("S01", "SHORTAGE", False), gap("S04", "SHORTAGE", False), gap("S03", "SURPLUS", True)])
    rec = planning.recommend_transfers(gaps, st, pr, wx, settings, date(2026, 10, 8), datetime(2026, 10, 9, 6))
    assert rec.iloc[0].source_store_id == "S03"
    assert "Jacksonville is closer but also short of" in rec.iloc[0].reason

    # Jacksonville is balanced (no spare stock): the reason says it has nothing to send.
    balanced = gap("S04", "BALANCED", False).copy()
    gaps = pd.DataFrame([gap("S01", "SHORTAGE", False), balanced, gap("S03", "SURPLUS", True)])
    rec = planning.recommend_transfers(gaps, st, pr, wx, settings, date(2026, 10, 8), datetime(2026, 10, 9, 6))
    assert "Jacksonville is closer but has no spare" in rec.iloc[0].reason

    # The nearest source itself gets no explanation: nothing is closer than it.
    gaps = pd.DataFrame([gap("S01", "SHORTAGE", False), gap("S04", "SURPLUS", True), gap("S03", "SURPLUS", True)])
    rec = planning.recommend_transfers(gaps, st, pr, wx, settings, date(2026, 10, 8), datetime(2026, 10, 9, 6))
    assert rec.iloc[0].source_store_id == "S04" and " closer" not in rec.iloc[0].reason
