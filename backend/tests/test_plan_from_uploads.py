"""Your uploads become a plan the planner can show: the one-click demo, the plain checks, the dropdown template, and the cost inputs."""

import io

import openpyxl
import pytest
from app.config import Settings
from app.main import create_app
from app.sources.mock import MockSource
from fastapi.testclient import TestClient

H = {"X-Requested-With": "stormsense"}


@pytest.fixture
def uploads(tmp_path):
    settings = Settings(
        STORMSENSE_MODE="mock",
        STORMSENSE_ENVIRONMENT="local",
        STORMSENSE_DEV_USER_EMAIL="ava.planner@stormsense.test",
        STORMSENSE_INGEST_ENABLED="1",
        STORMSENSE_INGEST_DIR=str(tmp_path),
    )
    return TestClient(create_app(settings, MockSource()))


def test_the_planner_has_no_uploaded_plan_until_one_is_built(uploads: TestClient):
    assert uploads.get("/api/ingest/plan/status").json()["ready"] is False
    r = uploads.get("/api/overview", headers={"X-Data-Source": "upload"})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "no_plan"


def test_one_click_demo_loads_the_workbooks_and_builds_a_plan_the_planner_can_read(uploads: TestClient):
    r = uploads.post("/api/ingest/demo/load", headers=H).json()
    assert r["loaded"] == {"stores": 10, "products": 5, "sales": 1400, "stock": 1400}
    assert r["plan"]["ready"] and r["plan"]["summary"]["transfers"] > 0
    me = uploads.get("/api/me", headers={"X-Data-Source": "upload"}).json()
    assert me["data_label"] == "uploaded"
    overview = uploads.get("/api/overview", headers={"X-Data-Source": "upload"})
    assert overview.status_code == 200 and overview.json()["pending_transfers"] > 0


def test_checks_say_what_is_missing_in_plain_words(uploads: TestClient):
    first = uploads.get("/api/ingest/checks").json()["sentences"]
    assert first[0].startswith("Still to upload: stores, products, sales, stock.")
    uploads.post("/api/ingest/demo/load", headers=H)
    sentences = uploads.get("/api/ingest/checks").json()["sentences"]
    assert any(s.startswith("Your sales cover 28 days") for s in sentences)
    assert any(s.startswith("Latest stock count:") for s in sentences)


def test_checks_name_stores_without_stock_and_products_without_sales(uploads: TestClient):
    uploads.post(
        "/api/ingest/feeds/stores/upload",
        json={"csv": "store_id,name,city,region,latitude,longitude\nS01,Orlando,O,F,28,-81\nS02,Tampa,T,F,27,-82\n"},
        headers=H,
    )
    uploads.post(
        "/api/ingest/feeds/products/upload",
        json={
            "csv": "product_id,name,name_plural,weather_driver,unit_price,pack_size\nP01,Tarp,Tarps,wind,20,1\nP02,Pump,Pumps,rain,90,1\n"
        },
        headers=H,
    )
    uploads.post("/api/ingest/feeds/sales/upload", json={"csv": "store_id,product_id,sale_date,units\nS01,P01,2026-10-01,3\n"}, headers=H)
    uploads.post(
        "/api/ingest/feeds/stock/upload", json={"csv": "store_id,product_id,snapshot_date,on_hand\nS01,P01,2026-10-01,9\n"}, headers=H
    )
    sentences = uploads.get("/api/ingest/checks").json()["sentences"]
    assert "1 store has no stock count: Tampa." in sentences
    assert "1 product has no sales: Pump." in sentences


def test_the_template_has_code_dropdowns_filled_from_your_files(uploads: TestClient):
    uploads.post("/api/ingest/demo/load", headers=H)
    r = uploads.get("/api/ingest/feeds/sales/template.xlsx")
    assert r.status_code == 200 and "spreadsheetml" in r.headers["content-type"]
    book = openpyxl.load_workbook(io.BytesIO(r.content))
    validations = book["sales"].data_validations.dataValidation
    formulas = {v.formula1 for v in validations}
    assert "=lists!$A$2:$A$11" in formulas and "=lists!$B$2:$B$6" in formulas  # 10 stores, 5 products
    assert book["lists"].sheet_state == "hidden" and book["lists"]["A2"].value


def test_cost_and_margin_inputs_change_the_estimated_profit(uploads: TestClient):
    uploads.post("/api/ingest/demo/load", headers=H)
    before = uploads.get("/api/ingest/plan/status").json()["net_benefit"]
    assert uploads.put("/api/ingest/economics", json={"truck_cost_per_mile": 10, "margin_pct": 30}, headers=H).status_code == 200
    after = uploads.get("/api/ingest/plan/status").json()["net_benefit"]
    assert after["trucking_usd"] > before["trucking_usd"] and after["net_usd"] < before["net_usd"]
    assert uploads.put("/api/ingest/economics", json={"truck_cost_per_mile": 2, "margin_pct": 150}, headers=H).status_code == 422


def test_a_planner_approves_or_rejects_a_markdown_and_it_shows_on_the_list(client: TestClient):
    items = client.get("/api/markdowns").json()
    if not items:  # the live rule finds none on sample data; the demo response finds some
        items = client.get("/api/markdowns", params={"weather": "demo"}).json()
    assert items, "the sample data should give at least one markdown in demo weather"
    first = items[0]
    r = client.post(
        "/api/markdowns/decision",
        json={"store_id": first["store"]["id"], "product_id": first["product"]["id"], "decision": "APPROVED"},
        headers=H,
    )
    assert r.status_code == 200 and r.json()["decision"] == "approved"
    shown = [
        m
        for m in client.get("/api/markdowns", params={"weather": "demo"}).json()
        if m["store"]["id"] == first["store"]["id"] and m["product"]["id"] == first["product"]["id"]
    ]
    assert shown and shown[0]["decision"] == "approved" and shown[0]["decided_by"]
    assert (
        client.post(
            "/api/markdowns/decision", json={"store_id": first["store"]["id"], "product_id": first["product"]["id"], "decision": "APPROVED"}
        ).status_code
        == 403
    )


def test_files_dropped_in_the_folder_are_loaded_and_moved_aside(uploads: TestClient, tmp_path):
    from app.ingest import DROP_DIR

    drop = tmp_path / DROP_DIR
    drop.mkdir()
    (drop / "stores.csv").write_text("store_id,name,city,region,latitude,longitude\nS01,Orlando,O,F,28,-81\n", encoding="utf-8-sig")
    (drop / "notes.txt").write_text("not a feed")
    r = uploads.post("/api/ingest/drop/scan", headers=H).json()
    assert r["loaded"] == ["stores"] and not (drop / "stores.csv").exists()
    assert list((drop / "processed").iterdir()) and (drop / "notes.txt").exists()
    assert uploads.get("/api/ingest/feeds").json()[0]["kept"] == 1
