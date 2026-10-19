"""Order suggestions (what is still short after pending moves) and best sellers by weather."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_order_suggestions_cover_pending_moves_and_only_list_real_gaps(client: TestClient):
    rows = client.get("/api/orders/suggested").json()
    assert rows, "the sample plan leaves some high-demand shortfall"
    for row in rows:
        assert row["order_units"] > 0
        assert row["order_units"] == row["shortfall_high"]
        assert row["shortfall_units"] <= row["order_units"]
        assert row["shortfall_low"] <= row["shortfall_units"] or row["shortfall_low"] == 0
        assert row["store"]["name"] and row["product"]["name"]


def test_pending_moves_are_counted_against_the_shortfall(client: TestClient):
    rows = client.get("/api/orders/suggested").json()
    pending = client.get("/api/transfers", params={"status": "PENDING"}).json()
    inbound: dict[tuple[str, str], int] = {}
    for t in pending:
        key = (t["to_store"]["name"], t["product"]["name"])
        inbound[key] = inbound.get(key, 0) + t["qty"]
    for row in rows:
        assert row["pending_inbound"] == inbound.get((row["store"]["name"], row["product"]["name"]), 0)


def test_best_sellers_rank_by_units_for_the_weather(client: TestClient):
    for weather in ("heat", "wind", "rain"):
        body = client.get("/api/best-sellers", params={"weather": weather}).json()
        assert body["weather"] == weather
        units = [item["units"] for item in body["ranking"]]
        assert units == sorted(units, reverse=True)
        assert body["what_next"]
    heat = client.get("/api/best-sellers", params={"weather": "heat"}).json()
    assert heat["ranking"] and "cooler" in heat["ranking"][0]["product"]["name"].lower()


def test_best_sellers_reject_unknown_weather(client: TestClient):
    assert client.get("/api/best-sellers", params={"weather": "snow"}).status_code == 422

