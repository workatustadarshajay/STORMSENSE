"""The carbon estimate scales with distance and load, and every transfer carries one."""
from app.carbon import estimate_kg_co2e
from fastapi.testclient import TestClient


def test_estimate_scales_with_distance_and_load():
    assert estimate_kg_co2e(qty=200, distance_miles=100) == 90.0  # a full truck over 100 miles
    assert estimate_kg_co2e(qty=50, distance_miles=100) == 22.5   # a quarter of that
    assert estimate_kg_co2e(qty=0, distance_miles=100) == 0.0


def test_every_transfer_reports_its_estimate(client: TestClient):
    transfers = client.get("/api/transfers").json()
    assert transfers and all(t["co2_kg"] >= 0 for t in transfers)
    for t in transfers:
        assert t["co2_kg"] == estimate_kg_co2e(t["qty"], t["distance_miles"])
