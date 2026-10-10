"""The morning briefing says what matters today, in plain words, with figures from the data."""
from fastapi.testclient import TestClient

from tests.conftest import VIEWER


def test_the_briefing_gives_a_headline_and_plain_lines(client: TestClient):
    b = client.get("/api/briefing").json()
    assert b["headline"] and 3 <= len(b["lines"]) <= 7
    text = " ".join([b["headline"], *b["lines"]]).lower()
    assert "urgent" in text and "stock was counted" in text
    for banned in ("sql", "delta", "databricks", "genie", "mlflow", "warehouse", "sku", "mape", "wape", "model", "api"):
        assert f" {banned} " not in f" {text} ", banned


def test_the_briefing_names_the_least_ready_store(client: TestClient):
    b = client.get("/api/briefing").json()
    stores = client.get("/api/stores").json()
    least = min(stores, key=lambda s: s["readiness"])
    assert any(least["name"] in line and f"{least['readiness']}%" in line for line in b["lines"])


def test_the_briefing_is_for_any_signed_in_person(client: TestClient):
    assert client.get("/api/briefing", headers=VIEWER).status_code == 200
