"""The demo email button starts the demo job. Planners only; nothing runs unless the workspace is there."""
from types import SimpleNamespace

import pytest
from app import alerts
from fastapi.testclient import TestClient

from tests.conftest import VIEWER

HEADERS = {"X-Requested-With": "stormsense"}


class FakeWorkspace:
    def __init__(self, job_names=("StormSense - Demo storm alert",), refuse=False):
        self.job_names, self.refuse, self.runs = job_names, refuse, []
        self.jobs = SimpleNamespace(list=self._list, run_now=self._run_now)

    def _list(self, name):
        return [SimpleNamespace(job_id=7)] if name in self.job_names else []

    def _run_now(self, job_id):
        if self.refuse:
            raise PermissionError("no permission for job 7 at /secret/path")
        self.runs.append(job_id)
        return SimpleNamespace(run_id=99)


def test_no_workspace_says_it_needs_the_live_workspace(client: TestClient):
    r = client.post("/api/demo/alert", headers=HEADERS)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "not_configured"


def test_viewers_cannot_start_it(client: TestClient):
    client.app.state.workspace = FakeWorkspace()
    assert client.post("/api/demo/alert", headers={**VIEWER, **HEADERS}).status_code == 403


def test_a_planner_starts_the_job_once(client: TestClient):
    fake = FakeWorkspace()
    client.app.state.workspace = fake
    r = client.post("/api/demo/alert", headers=HEADERS)
    assert r.status_code == 200 and r.json()["started"] is True
    assert fake.runs == [7]


def test_a_missing_job_says_to_deploy_first(client: TestClient):
    client.app.state.workspace = FakeWorkspace(job_names=())
    r = client.post("/api/demo/alert", headers=HEADERS)
    assert r.status_code == 409 and "Deploy the bundle" in r.json()["detail"]["message"]


def test_a_refused_start_gives_a_plain_message_and_no_internal_detail(client: TestClient):
    client.app.state.workspace = FakeWorkspace(refuse=True)
    r = client.post("/api/demo/alert", headers=HEADERS)
    assert r.status_code == 502
    assert "secret" not in r.text and "PermissionError" not in r.text


def test_start_demo_email_returns_the_run_id():
    assert alerts.start_demo_email(FakeWorkspace(), "StormSense - Demo storm alert") == 99
    with pytest.raises(alerts.JobMissing):
        alerts.start_demo_email(FakeWorkspace(job_names=()), "StormSense - Demo storm alert")
