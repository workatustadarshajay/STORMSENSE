"""Demo weather puts a storm on the Florida screens; live weather is left exactly as it was."""
from fastapi.testclient import TestClient


def test_live_is_the_default_and_says_so(client: TestClient):
    assert client.get("/api/overview").json()["weather_source"] == "live"
    assert client.get("/api/overview", params={"weather": "live"}).json()["weather_source"] == "live"


def test_demo_adds_a_storm_to_the_florida_alerts(client: TestClient):
    demo = client.get("/api/overview", params={"weather": "demo"}).json()
    assert demo["weather_source"] == "demo"
    storm_alerts = [a for a in demo["alerts"] if a["kind"] == "storm"]
    assert storm_alerts and "Orlando" in storm_alerts[0]["stores"]


def test_demo_lowers_florida_readiness_and_leaves_other_regions_alone(client: TestClient):
    live = {s["name"]: s for s in client.get("/api/stores").json()}
    demo = {s["name"]: s for s in client.get("/api/stores", params={"weather": "demo"}).json()}
    assert demo["Orlando"]["storm_days"] >= 2 and demo["Orlando"]["storm_days"] > live["Orlando"]["storm_days"]
    assert demo["Orlando"]["readiness"] <= live["Orlando"]["readiness"]
    assert demo["Dallas"]["storm_days"] == live["Dallas"]["storm_days"]  # Texas is not touched


def test_demo_store_forecast_is_labelled(client: TestClient):
    live = client.get("/api/stores/S01/forecast").json()
    demo = client.get("/api/stores/S01/forecast", params={"weather": "demo"}).json()
    assert live["weather_source"] == "live" and demo["weather_source"] == "demo"
    assert any(d["condition"] == "storm" for d in demo["weather"])
