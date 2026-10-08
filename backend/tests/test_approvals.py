"""Approvals are guarded: only pending rows change, repeats are harmless, every action is audited."""
from app.sources.mock import MockSource
from fastapi.testclient import TestClient

from tests.conftest import VIEWER, XHR


def approve(client: TestClient, ids: list[str], **kw):
    return client.post("/api/transfers/approve", json={"ids": ids}, headers={**XHR, **kw.get("headers", {})})


def test_approve_two(client: TestClient, pending_ids: list[str]):
    r = approve(client, pending_ids[:2]).json()
    assert r["changed"] == sorted(pending_ids[:2]) and r["skipped"] == [] and r["message"] == "2 transfers approved."
    assert len(client.get("/api/transfers", params={"status": "PENDING"}).json()) == len(pending_ids) - 2


def test_double_click_is_harmless(client: TestClient, pending_ids: list[str]):
    first = approve(client, pending_ids[:2]).json()
    second = approve(client, pending_ids[:2]).json()
    assert len(first["changed"]) == 2 and second["changed"] == [] and len(second["skipped"]) == 2
    assert second["message"] == "2 were already handled by someone else."
    approved = [t for t in client.get("/api/transfers", params={"status": "APPROVED"}).json() if t["id"] in pending_ids[:2]]
    assert len(approved) == 2  # still approved once, by the first request


def test_mixed_result_message(client: TestClient, pending_ids: list[str]):
    approve(client, pending_ids[:1])
    r = approve(client, pending_ids[:2]).json()
    assert r["message"] == "1 transfer approved. 1 was already handled by someone else."
    assert r["skipped"] == pending_ids[:1]


def test_repeated_ids_in_one_request_count_once(client: TestClient, pending_ids: list[str]):
    r = approve(client, [pending_ids[0], pending_ids[0]]).json()
    assert r["changed"] == [pending_ids[0]] and r["skipped"] == []


def test_reject_needs_a_reason_and_records_it(client: TestClient, pending_ids: list[str]):
    bad = client.post("/api/transfers/reject", json={"ids": pending_ids[:1], "reason": ""}, headers=XHR)
    assert bad.status_code == 422
    ok = client.post("/api/transfers/reject", json={"ids": pending_ids[:1], "reason": "Truck unavailable"}, headers=XHR).json()
    assert ok["message"] == "1 transfer rejected."
    row = next(t for t in client.get("/api/history").json() if t["id"] == pending_ids[0])
    assert row["status"] == "REJECTED" and row["note"] == "Truck unavailable"


def test_every_action_is_audited(client: TestClient, source: MockSource, pending_ids: list[str]):
    approve(client, pending_ids[:2])
    approve(client, pending_ids[:1])  # a repeat is logged too
    actions = [(a["action"], a["rec_id"]) for a in source.audit]
    assert actions.count(("APPROVED", pending_ids[0])) == 1 and ("SKIPPED", pending_ids[0]) in actions
    assert all(a["actor"] == "ava.planner@stormsense.test" and a["request_id"] for a in source.audit)


def test_viewers_cannot_decide(client: TestClient, pending_ids: list[str]):
    r = approve(client, pending_ids[:1], headers=VIEWER)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "read_only"
    assert client.get("/api/transfers/" + pending_ids[0]).json()["status"] == "PENDING"


def test_cross_site_posts_are_blocked(client: TestClient, pending_ids: list[str]):
    r = client.post("/api/transfers/approve", json={"ids": pending_ids[:1]})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "blocked"


def test_ids_are_validated(client: TestClient):
    for ids in (["x"], ["TR-1'; DROP TABLE x;--"], [], ["TR-0000000000"] * 51):
        assert approve(client, ids).status_code == 422


def test_overview_updates_after_a_decision(client: TestClient):
    before = client.get("/api/overview").json()
    urgent = [t["id"] for t in client.get("/api/transfers", params={"urgency": "URGENT"}).json()]
    approve(client, urgent[:1])
    after = client.get("/api/overview").json()
    assert after["urgent_transfers"] == before["urgent_transfers"] - 1
