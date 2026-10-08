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
