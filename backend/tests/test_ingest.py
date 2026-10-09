"""Your own data is checked row by row: good rows are kept, bad rows come back with the reason and the line."""
import pytest
from app.ingest import FEEDS, auto_mapping, check, sensitive_columns

STORES = [{"store_id": "S01", "name": "Orlando", "city": "Orlando", "region": "Florida", "latitude": "28.5", "longitude": "-81.4"}]
KNOWN = {"stores": {"S01"}, "products": {"P01"}}


def products(price="20", pack="1"):
    return [{"product_id": "P01", "name": "Tarp", "name_plural": "Tarps", "weather_driver": "wind", "unit_price": price, "pack_size": pack}]


def test_good_rows_are_kept_and_numbers_are_converted():
    out = check(FEEDS["stores"], STORES, None)
    assert len(out.accepted) == 1 and out.accepted[0]["latitude"] == 28.5 and out.refused == []


def test_bad_rows_are_refused_with_the_line_and_reason():
    rows = [{**STORES[0], "latitude": "120"}, {**STORES[0], "store_id": "S02", "latitude": "abc"}]
    out = check(FEEDS["stores"], rows, None)
    assert [r["line"] for r in out.refused] == [2, 3]
    assert "at most 90" in out.refused[0]["reason"] and "must be a number" in out.refused[1]["reason"]


def test_a_missing_required_column_is_reported_before_any_row_is_read():
    out = check(FEEDS["stores"], [{"store_id": "S01", "name": "Orlando"}], None)
    assert "city" in out.missing and out.accepted == []


def test_mapping_lets_your_own_column_names_work():
    rows = [{"Store code": "S01", "Store name": "Orlando", "Town": "Orlando", "State": "Florida", "Lat": "28", "Lon": "-81"}]
    mapping = {"store_id": "Store code", "name": "Store name", "city": "Town", "region": "State", "latitude": "Lat", "longitude": "Lon"}
    out = check(FEEDS["stores"], rows, mapping)
    assert out.accepted and out.missing == []


def test_sales_must_point_at_known_stores_and_products():
    sales = [{"store_id": "S09", "product_id": "P01", "sale_date": "2026-10-01", "units": "3"}]
    out = check(FEEDS["sales"], sales, None, KNOWN)
    assert "S09 is not in your stores file" in out.refused[0]["reason"]
    assert check(FEEDS["sales"], [{**sales[0], "store_id": "S01"}], None, KNOWN).accepted


def test_sales_need_the_stores_file_first():
    out = check(FEEDS["sales"], [{"store_id": "S01", "product_id": "P01", "sale_date": "2026-10-01", "units": "3"}], None, {})
    assert "Upload the stores file first" in out.refused[0]["reason"]


def test_duplicate_keys_are_refused():
    row = {"store_id": "S01", "product_id": "P01", "sale_date": "2026-10-01", "units": "3"}
    out = check(FEEDS["sales"], [row, dict(row)], None, KNOWN)
    assert len(out.accepted) == 1 and "repeats" in out.refused[0]["reason"]


def test_personal_or_card_columns_are_refused_outright():
    assert sensitive_columns(["store_id", "card_number", "Patient name", "company"]) == ["card_number", "Patient name"]
    with pytest.raises(ValueError):
        check(FEEDS["stores"], [{**STORES[0], "card_number": "1234"}], None)


def test_auto_mapping_matches_names_loosely():
    assert auto_mapping(FEEDS["products"], ["Product_ID", "NAME", "name plural"])["product_id"] == "Product_ID"
