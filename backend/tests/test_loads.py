"""Truck consolidation: moves on one route share trucks, and the trips saved are counted with the same cost model as the impact page."""
from types import SimpleNamespace as NS

from app.loads import plan_loads
from fastapi.testclient import TestClient


def move(id_, qty, miles=100, src="S01", dst="S02", product="Tarp"):
    return NS(id=id_, qty=qty, distance_miles=miles, from_store=NS(id=src, name="Jacksonville"),
              to_store=NS(id=dst, name="Orlando"), product=NS(name=product))


def test_two_small_moves_on_one_route_share_one_truck():
    out = plan_loads([move("TR1", 60), move("TR2", 60, product="Pump")], cost_per_mile=2.0)
    route = out["routes"][0]
    assert route["trips_now"] == 2 and route["trips_together"] == 1 and route["units"] == 120
    assert route["saved_usd"] == 200.0  # one trip saved: 100 miles at $2
    assert route["saved_kg"] == 90.0    # one trip saved: 100 miles at 0.9 kg


def test_moves_that_fill_their_own_trucks_save_nothing():
    out = plan_loads([move("TR1", 200), move("TR2", 200)], cost_per_mile=2.0)
    assert out["routes"][0]["trips_together"] == 2 and out["saved_usd"] == 0.0


def test_routes_are_kept_apart():
    out = plan_loads([move("TR1", 60, dst="S02"), move("TR2", 60, dst="S03")], cost_per_mile=2.0)
    assert len(out["routes"]) == 2 and out["saved_usd"] == 0.0


def test_the_loads_page_data_matches_the_pending_moves(client: TestClient):
    loads = client.get("/api/loads").json()
    pending = client.get("/api/transfers", params={"status": "PENDING"}).json()
    listed = {m["id"] for r in loads["routes"] for m in r["moves"]}
    assert listed == {t["id"] for t in pending}
    assert loads["trips_together"] <= loads["trips_now"] and loads["saved_usd"] >= 0
