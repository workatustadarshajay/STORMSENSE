"""Storm cover (simulation) and storm recovery: thresholds, caps, and the per-storm report."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_cover_triggers_only_where_enough_stores_reach_the_threshold(client: TestClient):
    body = client.get("/api/cover/simulation").json()
    assert {r["region"] for r in body["regions"]} == {"California", "Florida", "Texas"}
    for region in body["regions"]:
        assert region["triggered"] == (len(region["stores_hit"]) >= 2)
        if region["triggered"]:
            assert region["simulated_payout_usd"] == min(region["projected_lost_sales_usd"], body["cap_usd"])
            assert region["first_day"] is not None
        else:
            assert region["simulated_payout_usd"] == 0


def test_cover_says_it_is_a_simulation_and_states_the_trigger(client: TestClient):
    body = client.get("/api/cover/simulation").json()
    assert "Not a quote and not a contract" in body["note"]
    assert "39 mph" in body["trigger"] and "3 inches" in body["trigger"]


def test_cover_payout_never_exceeds_the_cap(client: TestClient):
    body = client.get("/api/cover/simulation").json()
    assert all(r["simulated_payout_usd"] <= body["cap_usd"] for r in body["regions"])


def test_recovery_reports_each_past_storm(client: TestClient):
    body = client.get("/api/recovery").json()
    assert len(body["events"]) == 5
    for ev in body["events"]:
        assert ev["unprotected_usd"] == round(ev["event"]["lost_usd"] - ev["event"]["protected_usd"], 2)
        firsts = [s["first_decision"] for s in ev["stores_restocked"]]
        assert firsts == sorted(firsts)
        assert all(s["days_after_start"] >= 0 for s in ev["stores_restocked"])


def test_recovery_explains_an_empty_timeline(client: TestClient):
    body = client.get("/api/recovery").json()
    assert body["note"]


def test_new_endpoints_are_in_the_contract(client: TestClient):
    paths = client.get("/api/openapi.json").json()["paths"]
    assert "/api/cover/simulation" in paths and "/api/recovery" in paths
