from app.config import Settings
from app.dbx import QueryError, WarmingUp
from app.main import create_app
from app.sources.mock import MockSource
from fastapi.testclient import TestClient

from tests.conftest import XHR


def test_security_headers_everywhere(client: TestClient):
    h = client.get("/api/overview").headers
    assert "default-src 'self'" in h["content-security-policy"] and h["x-content-type-options"] == "nosniff"
    assert h["x-frame-options"] == "DENY" and h["cache-control"] == "no-store" and "strict-transport-security" not in h


def test_production_requires_platform_sign_in_and_sends_hsts():
    app = create_app(Settings(STORMSENSE_MODE="mock", STORMSENSE_ENVIRONMENT="production"), MockSource())
    c = TestClient(app)
    r = c.get("/api/overview")
    assert r.status_code == 401 and r.json()["detail"]["code"] == "signed_out" and "strict-transport-security" in r.headers
    assert c.get("/api/overview", headers={"X-Forwarded-Email": "ava.planner@stormsense.test"}).status_code == 200
    assert c.get("/api/overview", headers={"X-Forwarded-Email": "not an email"}).status_code == 401


def test_oversized_requests_are_refused(client: TestClient):
    r = client.post("/api/ask", content=b"x" * 70_000, headers={**XHR, "Content-Type": "application/json"})
    assert r.status_code == 413


def test_ask_is_rate_limited_per_person(client: TestClient):
    body = {"question": "Which stores will run out of generators?"}
    codes = [client.post("/api/ask", json=body, headers=XHR).status_code for _ in range(12)]
    assert codes[:10] == [200] * 10 and codes[10:] == [429, 429]
    other = client.post("/api/ask", json=body, headers={**XHR, "X-Forwarded-Email": "sam.viewer@stormsense.test"})
    assert other.status_code == 200  # someone else is unaffected


def test_ask_validates_input(client: TestClient):
    assert client.post("/api/ask", json={"question": "hi"}, headers=XHR).status_code == 422
    assert client.post("/api/ask", json={"question": "x" * 501}, headers=XHR).status_code == 422


class Broken(MockSource):
    def __init__(self, error: Exception):
        super().__init__()
        self.error = error

    def transfers(self, *a, **k):
        raise self.error

    def ping(self):
        raise self.error


def test_a_waking_warehouse_is_a_friendly_state_not_an_error():
    c = TestClient(create_app(Settings(STORMSENSE_MODE="mock"), Broken(WarmingUp())))
    r = c.get("/api/transfers")
    assert r.status_code == 503 and r.headers["retry-after"] == "5"
    assert r.json()["detail"] == {"code": "warming_up", "message": "Getting things ready. This usually takes a few seconds."}
    assert c.get("/api/health", params={"deep": True}).json()["status"] == "starting"


def test_failed_queries_show_nothing_technical():
    c = TestClient(create_app(Settings(STORMSENSE_MODE="mock"), Broken(QueryError())))
    r = c.get("/api/transfers")
    assert r.status_code == 502 and r.json()["detail"]["message"] == "We couldn't load that right now. Please try again."
    assert c.get("/api/health", params={"deep": True}).json()["status"] == "unavailable"


def test_the_web_app_is_served_when_built(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>app</html>")
    (tmp_path / "assets" / "a.js").write_text("console.log(1)")
    c = TestClient(create_app(Settings(STORMSENSE_MODE="mock", static_dir=tmp_path), MockSource()))
    assert c.get("/transfers").text == "<html>app</html>"  # client-side route falls back to the app
    assert c.get("/assets/a.js").text == "console.log(1)"
    assert c.get("/../../etc/passwd").text == "<html>app</html>"  # no path traversal
