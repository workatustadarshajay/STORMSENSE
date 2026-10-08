"""Contract tests: every endpoint returns the documented shape, in plain language."""
import json
import re

from app.service import BANNED
from fastapi.testclient import TestClient

from tests.conftest import VIEWER


def test_health_is_cheap_by_default(client: TestClient):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json() == {"status": "ok", "mode": "mock", "warehouse": "not_checked"}
    assert client.get("/api/health", params={"deep": True}).json()["warehouse"] == "ready"


def test_me_reflects_role(client: TestClient):
    planner = client.get("/api/me").json()
    assert planner["role"] == "planner" and planner["can_approve"] is True and planner["data_label"] == "sample"
    viewer = client.get("/api/me", headers=VIEWER).json()
    assert viewer["role"] == "viewer" and viewer["can_approve"] is False


def test_unknown_user_gets_the_default_read_only_role(client: TestClient):
    me = client.get("/api/me", headers={"X-Forwarded-Email": "new.person@example.com"}).json()
    assert me["role"] == "viewer" and me["name"] == "New Person"


def test_overview(client: TestClient):
    o = client.get("/api/overview").json()
    assert o["urgent_transfers"] > 0 and o["pending_transfers"] >= o["urgent_transfers"] and o["stores_at_risk"] > 0
    assert o["next_alert"]["title"].endswith("expected " + o["next_alert"]["weekday"])
    assert o["next_action"]["button"] == "Review transfers" and o["next_action"]["title"].startswith("Review")


def test_transfers_read_like_sentences(client: TestClient):
    rows = client.get("/api/transfers", params={"status": "PENDING"}).json()
    assert len(rows) >= 5
    t = rows[0]
    assert re.fullmatch(r"Move \d+ .+ from .+ to .+", t["headline"]) and t["confidence"] in ("High", "Medium", "Low")
    assert t["urgency"] == "URGENT"  # urgent first
    urgent = client.get("/api/transfers", params={"urgency": "URGENT"}).json()
    assert urgent and all(x["urgency"] == "URGENT" for x in urgent)


def test_transfer_detail_and_not_found(client: TestClient, pending_ids: list[str]):
    assert client.get(f"/api/transfers/{pending_ids[0]}").json()["id"] == pending_ids[0]
    r = client.get("/api/transfers/TR-0000000000")
    assert r.status_code == 404 and r.json()["detail"]["code"] == "not_found"
    assert client.get("/api/transfers/nope").status_code == 422


def test_stores_and_forecast(client: TestClient):
    stores = client.get("/api/stores").json()
    assert len(stores) == 10 and {"id", "name", "city", "region", "running_low"} <= stores[0].keys()
    orlando = next(s for s in stores if s["name"] == "Orlando")
    f = client.get(f"/api/stores/{orlando['id']}/forecast").json()
    assert len(f["weather"]) == 7 and len(f["products"]) == 5
    assert all(len(p["days"]) == 7 for p in f["products"])
    low = [p for p in f["products"] if p["status"] == "RUNNING_LOW"]
    assert low and low[0]["runs_low_day"] and f["products"][0]["status"] == "RUNNING_LOW"  # trouble first
    assert "demand" in low[0]["why"]
    assert client.get("/api/stores/S99/forecast").status_code == 404


def test_inventory_filters(client: TestClient):
    low = client.get("/api/inventory", params={"status": "RUNNING_LOW"}).json()
    extra = client.get("/api/inventory", params={"status": "EXTRA"}).json()
    assert low and extra and {i["status"] for i in low} == {"RUNNING_LOW"} and {i["status"] for i in extra} == {"EXTRA"}
    assert len(client.get("/api/inventory").json()) == len(low) + len(extra)


def test_history_lists_past_decisions(client: TestClient):
    rows = client.get("/api/history").json()
    assert rows and all(r["status"] != "PENDING" and r["decided_by"] and r["decided_at"] for r in rows)


def test_ask_answers_a_sentence_and_a_table(client: TestClient):
    r = client.post("/api/ask", json={"question": "Which stores will run out of generators this week?"},
                    headers={"X-Requested-With": "stormsense"}).json()
    assert r["answered"] and "generators" in r["answer"] and r["table"]["columns"][0] == "Store" and r["table"]["rows"]


def test_ask_falls_back_kindly(client: TestClient):
    r = client.post("/api/ask", json={"question": "What is the meaning of life?"}, headers={"X-Requested-With": "stormsense"}).json()
    assert r["answered"] is False and r["table"] is None and "Try asking" in r["answer"]


def test_nothing_technical_reaches_planners(client: TestClient, pending_ids: list[str]):
    """The words on the banned list never appear in any value an endpoint returns."""
    urls = ["/api/me", "/api/overview", "/api/transfers", "/api/history", "/api/stores", "/api/stores/S01/forecast", "/api/inventory"]
    for url in urls:
        values = re.findall(r'"([^"]*)"', json.dumps(client.get(url).json()))
        keys = set(re.findall(r'"([^"]*)":', json.dumps(client.get(url).json())))
        hits = [v for v in values if v not in keys and BANNED.search(v)]
        assert not hits, f"{url}: {hits[:3]}"


def test_openapi_describes_the_contract(client: TestClient):
    spec = client.get("/api/openapi.json").json()
    assert {"/api/transfers/approve", "/api/transfers/reject", "/api/ask", "/api/overview"} <= spec["paths"].keys()


def test_ask_answers_become_one_plain_sentence():
    """Real answers from the live Ask space: markdown, lists and run-on text."""
    from app.service import plain_sentence

    assert plain_sentence("**2 stores** are forecast to run out of generators this week: **Orlando** runs low on **Thursday**.", True) \
        == "2 stores are forecast to run out of generators this week: Orlando runs low on Thursday."
    listy = ("Here are the forecast weekly sales for **Orlando** by product from the latest prediction snapshot: "
             "- **4x8 plywood sheet:** **121** units - **20x30 tarp:** **111** units")
    assert plain_sentence(listy, True) == "Here are the forecast weekly sales for Orlando by product from the latest prediction snapshot."
    long = "word " * 80
    out = plain_sentence(long, False)
    assert out.endswith("...") and len(out) <= 245 and "wor..." not in out
    assert plain_sentence("The total is **$54,282.41**. More detail follows.", True) == "The total is $54,282.41."
