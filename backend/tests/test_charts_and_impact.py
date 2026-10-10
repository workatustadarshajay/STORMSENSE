"""Chart data and the business impact figures: planner side for each source, upload side for the files, and the timeline."""
import pytest
from app.config import Settings
from app.main import create_app
from app.sources.mock import MockSource
from fastapi.testclient import TestClient

H = {"X-Requested-With": "stormsense"}


@pytest.fixture
def copy_(tmp_path):
    settings = Settings(STORMSENSE_MODE="mock", STORMSENSE_ENVIRONMENT="local", STORMSENSE_DEV_USER_EMAIL="ava.planner@stormsense.test",
                        STORMSENSE_INGEST_ENABLED="1", STORMSENSE_INGEST_DIR=str(tmp_path))
    return TestClient(create_app(settings, MockSource()))


def test_analysis_charts_have_demand_shortages_urgency_and_products(copy_: TestClient):
    c = copy_.get("/api/analysis/charts").json()
    assert len(c["demand_by_day"]) == 7 and all(d["units"] >= 0 for d in c["demand_by_day"])
    assert c["stock_available"] > 0
    assert {u["urgency"] for u in c["transfers_by_urgency"]} <= {"URGENT", "NORMAL"}
    assert c["protected_by_product"] == sorted(c["protected_by_product"], key=lambda p: -p["protected_usd"])


def test_impact_figures_match_the_moves_and_say_what_they_assume(copy_: TestClient):
    i = copy_.get("/api/impact").json()
    h = i["headline"]
    assert h["moves"] == h["pending"] + h["approved"] and h["protected_usd"] > 0
    assert round(h["net_usd"], 2) == round(h["margin_usd"] - h["trucking_usd"], 2)
    assert any("Carbon" in a for a in i["assumptions"]) and any("not profit" in a for a in i["assumptions"])


def test_the_timeline_records_uploads_plans_costs_and_decisions(copy_: TestClient):
    copy_.post("/api/ingest/demo/load", headers=H)
    copy_.put("/api/ingest/economics", json={"truck_cost_per_mile": 3, "margin_pct": 25}, headers=H)
    pending = copy_.get("/api/transfers", params={"status": "PENDING"}).json()
    copy_.post("/api/transfers/approve", json={"ids": [pending[0]["id"]]}, headers=H)
    timeline = copy_.get("/api/impact").json()["timeline"]
    kinds = [e["kind"] for e in timeline]
    assert kinds[0] == "transfers_approved"
    assert {"demo_loaded", "plan_built", "economics_saved"} <= set(kinds)
    assert any(e["detail"].startswith("Built the plan:") for e in timeline)


def test_the_plan_change_says_when_the_last_plan_was_built(copy_: TestClient):
    copy_.post("/api/ingest/demo/load", headers=H)
    changes = copy_.get("/api/impact").json()["changes"]
    assert changes["last_plan_at"] and changes["moves_then"] is not None and changes["moves_now"] > 0


def test_upload_charts_show_daily_sales_stock_cover_and_status(copy_: TestClient):
    assert copy_.get("/api/ingest/charts").json()["sales_by_day"] == []
    copy_.post("/api/ingest/demo/load", headers=H)
    c = copy_.get("/api/ingest/charts").json()
    assert len(c["sales_by_day"]) == 28 and len(c["stock_by_day"]) == 28
    assert sum(c["status_counts"].values()) == 50 and len(c["cover_by_store"]) == 10
    assert [x["feed"] for x in c["completeness"]] == ["Stores", "Products", "Daily sales", "Daily stock"]
