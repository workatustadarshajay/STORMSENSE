"""Storm response: a draft appears for a storm warning, sends nothing, and only a planner's decision moves stock."""
from fastapi.testclient import TestClient

from tests.conftest import VIEWER

H = {"X-Requested-With": "stormsense"}


def test_no_draft_without_a_storm_warning(client: TestClient):
    client.app.state.service.source.t["weather_forecast"] = []  # nothing forecast, so no alerts
    client.app.state.service._cache.clear()
    r = client.post("/api/response/draft", headers=H)
    assert r.status_code == 404 and r.json()["detail"]["code"] == "no_storm"


def test_a_draft_names_the_moves_and_the_stores_and_sends_nothing(client: TestClient):
    d = client.post("/api/response/draft", headers=H).json()
    assert d["status"] == "draft" and d["moves"] and d["store_notes"]
    assert {n["store"] for n in d["store_notes"]} == set(d["stores"])
    assert d["protected_usd"] == round(sum(m["sales_protected_usd"] for m in d["moves"]), 2)
    assert all("Not sent" not in n["text"] for n in d["store_notes"])


def test_drafting_again_gives_the_same_open_draft(client: TestClient):
    first = client.post("/api/response/draft", headers=H).json()
    second = client.post("/api/response/draft", headers=H).json()
    assert first["id"] == second["id"]


def test_a_planner_approves_only_the_chosen_moves_and_rejects_the_rest(client: TestClient):
    d = client.post("/api/response/draft", headers=H).json()
    keep = d["moves"][0]["id"]
    r = client.post(f"/api/response/{d['id']}/decide", json={"approve_ids": [keep], "reason": "Covered by another store"}, headers=H)
    assert r.status_code == 200
    decided = r.json()
    assert decided["status"] == "decided" and decided["approved"] == 1 and decided["rejected"] == len(d["moves"]) - 1
    pending = {t["id"] for t in client.get("/api/transfers", params={"status": "PENDING"}).json()}
    assert keep not in pending and not any(m["id"] in pending for m in d["moves"][1:])
    again = client.post(f"/api/response/{d['id']}/decide", json={"approve_ids": []}, headers=H)
    assert again.status_code == 409


def test_a_viewer_cannot_decide_a_storm_response(client: TestClient):
    d = client.post("/api/response/draft", headers=H).json()
    r = client.post(f"/api/response/{d['id']}/decide", json={"approve_ids": []}, headers={**VIEWER, **H})
    assert r.status_code == 403


def test_a_decided_response_is_not_reopened_by_drafting_again(client: TestClient):
    d = client.post("/api/response/draft", headers=H).json()
    client.post(f"/api/response/{d['id']}/decide", json={"approve_ids": []}, headers=H)
    again = client.post("/api/response/draft", headers=H).json()
    assert again["id"] == d["id"] and again["status"] == "decided"
