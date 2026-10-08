"""The warehouse client: types, retries and the friendly 'getting things ready' state."""
from datetime import datetime
from types import SimpleNamespace as NS

import pytest
from app.dbx import QueryError, Warehouse, WarmingUp, convert, param_type, with_retries
from databricks.sdk.errors import TemporarilyUnavailable
from databricks.sdk.service.sql import StatementState


def response(state, rows=None, cols=(), statement_id="s1", error=None):
    manifest = NS(schema=NS(columns=[NS(name=n, type_name=NS(value=t)) for n, t in cols])) if cols else None
    return NS(statement_id=statement_id, status=NS(state=state, error=error), manifest=manifest,
              result=NS(data_array=rows) if rows is not None else None)


class FakeClient:
    def __init__(self, *responses):
        self.responses, self.submitted = list(responses), []
        self.statement_execution = NS(execute_statement=self._submit, get_statement=self._poll)

    def _submit(self, **kw):
        self.submitted.append(kw)
        return self.responses.pop(0)

    def _poll(self, statement_id):
        return self.responses.pop(0)


def test_values_come_back_typed():
    ok = response(StatementState.SUCCEEDED, [["S01", "5", "1.5", "2026-10-08", "true"]],
                  [("id", "STRING"), ("n", "INT"), ("x", "DOUBLE"), ("d", "DATE"), ("b", "BOOLEAN")])
    rows = Warehouse(FakeClient(ok), "w", "main", "stormsense").run("SELECT 1")
    assert rows == [{"id": "S01", "n": 5, "x": 1.5, "d": datetime(2026, 10, 8).date(), "b": True}]


def test_parameters_are_bound_with_types_and_the_schema_is_set():
    client = FakeClient(response(StatementState.SUCCEEDED, []))
    Warehouse(client, "w1", "main", "stormsense").run("SELECT :a, :b, :c, :d", {"a": "x", "b": 3, "c": 1.5, "d": None})
    sent = client.submitted[0]
    assert sent["warehouse_id"] == "w1" and sent["catalog"] == "main" and sent["schema"] == "stormsense"
    assert [(p.name, p.type, p.value) for p in sent["parameters"]] == [
        ("a", "STRING", "x"), ("b", "INT", "3"), ("c", "DOUBLE", "1.5"), ("d", "STRING", None)]
    assert param_type(2**40) == "BIGINT" and param_type(True) == "BOOLEAN" and convert("2026-10-08T06:00:00Z", "TIMESTAMP").hour == 6


def test_a_waking_warehouse_is_waited_for():
    client = FakeClient(response(StatementState.PENDING), response(StatementState.RUNNING),
                        response(StatementState.SUCCEEDED, [["1"]], [("ok", "INT")]))
    slept = []
    rows = Warehouse(client, "w", "", "s", sleep=slept.append).run("SELECT 1")
    assert rows == [{"ok": 1}] and len(slept) == 2 and slept[1] > slept[0]


def test_taking_too_long_becomes_getting_things_ready():
    client = FakeClient(response(StatementState.PENDING))
    with pytest.raises(WarmingUp):
        Warehouse(client, "w", "", "s", budget_seconds=0, sleep=lambda _: None).run("SELECT 1")


def test_failures_are_hidden_from_planners():
    failed = response(StatementState.FAILED, error=NS(message="secret internal detail"))
    with pytest.raises(QueryError) as err:
        Warehouse(FakeClient(failed), "w", "", "s").run("SELECT 1")
    assert "secret" not in str(err.value)


def test_transient_errors_are_retried_with_backoff():
    calls, waits = [], []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise TemporarilyUnavailable("busy")
        return "ok"

    assert with_retries(flaky, sleep=waits.append) == "ok" and waits == [0.5, 1.0]
    with pytest.raises(TemporarilyUnavailable):
        with_retries(lambda: (_ for _ in ()).throw(TemporarilyUnavailable("down")), attempts=2, sleep=lambda _: None)
