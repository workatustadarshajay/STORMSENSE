"""The browser picks sample data or the live workspace per request. Live is refused when it is not connected."""
from fastapi.testclient import TestClient

H = {"X-Requested-With": "stormsense"}


def test_the_copy_defaults_to_sample_data(client: TestClient):
    assert client.get("/api/me").json()["data_label"] == "sample"


def test_asking_for_live_data_on_a_copy_without_it_says_so(client: TestClient):
    r = client.get("/api/overview", headers={"X-Data-Source": "live"})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "not_connected"


def test_an_unknown_source_is_refused(client: TestClient):
    r = client.get("/api/overview", headers={"X-Data-Source": "moon"})
    assert r.status_code == 400


def test_each_source_returns_its_own_data(client: TestClient):
    # Connect a second source in this test: a sample copy under the name live, with its own approvals.
    client.app.state.services["live"] = client.app.state.services["sample"]
    sample = client.get("/api/transfers", headers={"X-Data-Source": "sample"}).json()
    live = client.get("/api/transfers", headers={"X-Data-Source": "live"}).json()
    assert [t["id"] for t in sample] == [t["id"] for t in live]
    r = client.post("/api/what-if", json={"strength": 50, "start_day": 0, "days": 2, "region": None},
                    headers={**H, "X-Data-Source": "sample"}).json()
    assert r["answered"] is False and "live workspace" in r["message"]
