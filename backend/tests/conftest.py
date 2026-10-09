import pytest
from app.config import Settings
from app.main import create_app
from app.sources.mock import MockSource
from fastapi.testclient import TestClient

XHR = {"X-Requested-With": "stormsense"}
VIEWER = {"X-Forwarded-Email": "sam.viewer@stormsense.test"}


@pytest.fixture
def source() -> MockSource:
    return MockSource()  # fresh copy per test: approvals change it


@pytest.fixture
def client(source: MockSource) -> TestClient:
    settings = Settings(STORMSENSE_MODE="mock", STORMSENSE_ENVIRONMENT="local", STORMSENSE_DEV_USER_EMAIL="ava.planner@stormsense.test")
    return TestClient(create_app(settings, source))


@pytest.fixture
def pending_ids(client: TestClient) -> list[str]:
    return [t["id"] for t in client.get("/api/transfers", params={"status": "PENDING"}).json()]
