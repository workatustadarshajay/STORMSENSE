"""On a local copy the operator's own identity can approve; other people who are not in the account list cannot."""
from app.config import Settings
from app.main import create_app
from app.sources.mock import MockSource
from fastapi.testclient import TestClient

H = {"X-Requested-With": "stormsense"}


def test_the_local_operator_can_approve_even_when_not_in_the_account_list():
    settings = Settings(STORMSENSE_MODE="mock", STORMSENSE_ENVIRONMENT="local", STORMSENSE_DEV_USER_EMAIL="operator@example.com")
    client = TestClient(create_app(settings, MockSource()))
    me = client.get("/api/me").json()
    assert me["role"] == "planner" and me["can_approve"] is True
    pending = client.get("/api/transfers", params={"status": "PENDING"}).json()
    assert client.post("/api/transfers/approve", json={"ids": [pending[0]["id"]]}, headers=H).status_code == 200


def test_a_stranger_who_is_not_in_the_account_list_still_cannot_approve():
    client = TestClient(create_app(Settings(STORMSENSE_MODE="mock", STORMSENSE_ENVIRONMENT="local",
                                            STORMSENSE_DEV_USER_EMAIL="operator@example.com"), MockSource()))
    stranger = {"X-Forwarded-Email": "someone.else@example.com"}
    assert client.get("/api/me", headers=stranger).json()["can_approve"] is False
