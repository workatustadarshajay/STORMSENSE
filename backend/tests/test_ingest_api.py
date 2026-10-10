"""Your own data over HTTP: off by default, same-origin changes only, and every refusal says why."""
import pytest
from app.config import Settings
from app.main import create_app
from app.sources.mock import MockSource
from fastapi.testclient import TestClient

H = {"X-Requested-With": "stormsense"}
STORES_CSV = "store_id,name,city,region,latitude,longitude\nS01,Orlando,Orlando,Florida,28.5,-81.4\nS02,Tampa,Tampa,Florida,27.9,-82.4\n"
PRODUCTS_CSV = "product_id,name,name_plural,weather_driver,unit_price,pack_size\nP01,Tarp,Tarps,wind,20,1\n"


@pytest.fixture
def ingest(tmp_path):
    settings = Settings(STORMSENSE_MODE="mock", STORMSENSE_ENVIRONMENT="local",
                        STORMSENSE_DEV_USER_EMAIL="ava.planner@stormsense.test", STORMSENSE_INGEST_ENABLED="1",
                        STORMSENSE_INGEST_DIR=str(tmp_path))
    app = create_app(settings, MockSource())
    return TestClient(app)


def test_off_by_default(client: TestClient):
    assert client.get("/api/ingest/feeds").status_code == 404


def test_the_four_feeds_are_listed_with_their_template(ingest: TestClient):
    feeds = ingest.get("/api/ingest/feeds").json()
    assert [f["feed"] for f in feeds] == ["stores", "products", "sales", "stock"]
    stores = feeds[0]
    assert stores["template"].startswith("store_id,name,city,region,latitude,longitude")


def test_upload_keeps_good_rows_and_refuses_bad_ones_with_reasons(ingest: TestClient):
    bad = STORES_CSV + "S03,Miami,Miami,Florida,200,-80.2\n"
    r = ingest.post("/api/ingest/feeds/stores/upload", json={"csv": bad}, headers=H).json()
    assert r["kept"] == 2 and r["refused"] == 1 and r["refusals"][0] == {"line": 4, "reason": "latitude must be at most 90"}
    ok = ingest.post("/api/ingest/feeds/stores/upload", json={"csv": STORES_CSV}, headers=H).json()
    assert ok["kept"] == 2 and ok["refused"] == 0 and "Kept 2 rows" in ok["message"]


def test_sales_need_stores_and_products_first(ingest: TestClient):
    sales = "store_id,product_id,sale_date,units\nS01,P01,2026-10-01,3\n"
    r = ingest.post("/api/ingest/feeds/sales/upload", json={"csv": sales}, headers=H).json()
    assert "Upload the stores file first" in r["refusals"][0]["reason"]
    ingest.post("/api/ingest/feeds/stores/upload", json={"csv": STORES_CSV}, headers=H)
    ingest.post("/api/ingest/feeds/products/upload", json={"csv": PRODUCTS_CSV}, headers=H)
    r = ingest.post("/api/ingest/feeds/sales/upload", json={"csv": sales}, headers=H).json()
    assert r["kept"] == 1


def test_your_own_column_names_work_through_the_mapping(ingest: TestClient):
    own = "Code,Store name,Town,State,Lat,Lon\nS01,Orlando,Orlando,Florida,28.5,-81.4\n"
    mapping = {"store_id": "Code", "name": "Store name", "city": "Town", "region": "State", "latitude": "Lat", "longitude": "Lon"}
    r = ingest.post("/api/ingest/feeds/stores/upload", json={"csv": own, "mapping": mapping}, headers=H).json()
    assert r["kept"] == 1 and r["missing_columns"] == []


def test_rows_can_be_sent_as_json_from_another_system(ingest: TestClient):
    rows = [{"store_id": "S01", "name": "Orlando", "city": "Orlando", "region": "Florida", "latitude": 28.5, "longitude": -81.4}]
    r = ingest.post("/api/ingest/feeds/stores/rows", json={"rows": rows}, headers=H).json()
    assert r["kept"] == 1
    preview = ingest.get("/api/ingest/feeds/stores/preview").json()
    assert preview[0]["name"] == "Orlando"


def test_personal_or_card_columns_are_refused_with_a_clear_message(ingest: TestClient):
    r = ingest.post("/api/ingest/feeds/stores/upload", json={"csv": "store_id,card_number\nS01,1234\n"}, headers=H)
    assert r.status_code == 422 and "card_number" in r.json()["detail"]["message"]


def test_changes_need_the_same_origin_header(ingest: TestClient):
    assert ingest.post("/api/ingest/feeds/stores/upload", json={"csv": STORES_CSV}).status_code == 403


def test_clearing_a_feed_empties_it(ingest: TestClient):
    ingest.post("/api/ingest/feeds/stores/upload", json={"csv": STORES_CSV}, headers=H)
    ingest.delete("/api/ingest/feeds/stores", headers=H)
    assert ingest.get("/api/ingest/feeds/stores/preview").json() == []


def _workbook(sheets: dict[str, list[list]]) -> bytes:
    import io

    import openpyxl

    book = openpyxl.Workbook()
    book.remove(book.active)
    for name, rows in sheets.items():
        ws = book.create_sheet(name)
        for r in rows:
            ws.append(r)
    buf = io.BytesIO()
    book.save(buf)
    return buf.getvalue()


def test_an_excel_workbook_uploads_with_dates_and_numbers_read_properly(ingest: TestClient):
    import base64
    import datetime

    sales = _workbook({"sales": [["store_id", "product_id", "sale_date", "units"],
                                 ["S01", "P01", datetime.date(2026, 10, 1), 3]]})
    ingest.post("/api/ingest/feeds/stores/upload", json={"csv": STORES_CSV}, headers=H)
    ingest.post("/api/ingest/feeds/products/upload", json={"csv": PRODUCTS_CSV}, headers=H)
    r = ingest.post("/api/ingest/feeds/sales/upload", json={"xlsx_base64": base64.b64encode(sales).decode()}, headers=H).json()
    assert r["kept"] == 1 and r["refused"] == 0 and r["refusals"] == []
    assert ingest.get("/api/ingest/feeds/sales/preview").json()[0]["sale_date"] == "2026-10-01"  # dates read as dates


def test_one_file_at_a_time_and_a_clear_message_for_a_broken_excel_file(ingest: TestClient):
    import base64
    both = {"csv": STORES_CSV, "xlsx_base64": base64.b64encode(b"x").decode()}
    assert ingest.post("/api/ingest/feeds/stores/upload", json=both, headers=H).status_code == 422
    broken = ingest.post("/api/ingest/feeds/stores/upload", json={"xlsx_base64": base64.b64encode(b"not a workbook").decode()}, headers=H)
    assert broken.status_code == 422 and "could not be read" in broken.json()["detail"]["message"]


def test_the_analysis_waits_for_all_four_files(ingest: TestClient):
    assert ingest.get("/api/ingest/analysis").status_code == 404
    ingest.post("/api/ingest/feeds/stores/upload", json={"csv": STORES_CSV}, headers=H)
    ingest.post("/api/ingest/feeds/products/upload", json={"csv": PRODUCTS_CSV}, headers=H)
    sales = "store_id,product_id,sale_date,units\nS01,P01,2026-10-01,3\n"
    stock = "store_id,product_id,snapshot_date,on_hand\nS01,P01,2026-10-01,2\n"
    ingest.post("/api/ingest/feeds/sales/upload", json={"csv": sales}, headers=H)
    ingest.post("/api/ingest/feeds/stock/upload", json={"csv": stock}, headers=H)
    a = ingest.get("/api/ingest/analysis").json()
    assert a["stores"] == 2 and a["pairs"] == 1 and a["items"][0]["status"] == "Watch"  # 3 sold in 28 days is about 19 days of cover
