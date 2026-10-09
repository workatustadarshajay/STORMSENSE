"""Proof that SQL is parameterized, and that the live source follows the same rules as the mock."""
import ast
import re
from datetime import date
from pathlib import Path

import pytest
from app.sources.databricks import DatabricksSource

HOSTILE = "x'; DROP TABLE transfer_recommendations; --"


class FakeSql:
    """Records every statement and answers with canned rows."""

    def __init__(self, answers: dict[str, list[dict]] | None = None):
        self.calls: list[tuple[str, dict]] = []
        self.answers = answers or {}

    def run(self, statement: str, params: dict | None = None) -> list[dict]:
        self.calls.append((statement, params or {}))
        for needle, rows in self.answers.items():
            if needle in statement:
                return rows
        return []


def every_read(src: DatabricksSource):
    src.user(HOSTILE)
    src.setting(HOSTILE)
    src.transfers(HOSTILE, HOSTILE, 5)
    src.transfer(HOSTILE)
    src.history(5)
    src.predictions(HOSTILE)
    src.gaps(HOSTILE, HOSTILE)
    src.weather(HOSTILE)


def test_user_input_never_reaches_statement_text():
    sql = FakeSql()
    src = DatabricksSource(sql)
    every_read(src)
    src.decide("APPROVED", [HOSTILE, "TR-0000000001"], HOSTILE, HOSTILE, HOSTILE)
    assert len(sql.calls) > 8
    for statement, params in sql.calls:
        assert "DROP" not in statement and "'x" not in statement
        markers = set(re.findall(r"(?<![:\w]):(\w+)", statement))
        assert markers <= params.keys(), f"unbound marker in: {statement}"
        assert set(params) <= markers | {"limit"}, f"unused parameter in: {statement}"


def test_only_placeholder_lists_are_assembled_at_run_time():
    """Static check: the only f-strings in SQL calls interpolate constants or placeholder lists, never request data."""
    tree = ast.parse((Path(__file__).resolve().parents[1] / "app" / "sources" / "databricks.py").read_text())
    # i is the loop counter that names placeholders (:id0, :id1 ...); it is an int, never request data
    # i names placeholders (:id0 ...); listed and marks hold only placeholders; "version" is Delta's version number
    # (int-coerced in _version_clause), never request data.
    allowed = {"_LATEST_GAPS", "_LATEST_PREDICTIONS", "_LATEST_WEATHER", "marks", "listed", "i", "version", "at", "int"}
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            names = {n.id for v in node.values if isinstance(v, ast.FormattedValue) for n in ast.walk(v) if isinstance(n, ast.Name)}
            if names - allowed:
                offenders.append((node.lineno, names - allowed))
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") in ("format",) and "sql" in ast.unparse(node.func):
            offenders.append((node.lineno, "format"))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Constant) \
                and isinstance(node.left.value, str) and "SELECT" in node.left.value.upper():
            offenders.append((node.lineno, "%"))
    assert not offenders, offenders


def test_decide_only_touches_pending_rows_and_reports_skips():
    sql = FakeSql({"SELECT rec_id FROM": [{"rec_id": "TR-0000000001"}]})
    d = DatabricksSource(sql).decide("APPROVED", ["TR-0000000001", "TR-0000000002"], "ava@example.com", None, "req1")
    assert d.changed == ["TR-0000000001"] and d.skipped == ["TR-0000000002"]
    update = sql.calls[0][0]
    assert update.startswith("UPDATE transfer_recommendations") and "status = 'PENDING'" in update
    assert sql.calls[0][1]["req"] == "req1" and sql.calls[0][1]["id0"] == "TR-0000000001"
    audits = [c for c in sql.calls if c[0].startswith("INSERT INTO transfer_audit")]
    assert len(audits) == 2 and "'SKIPPED'" in audits[1][0]  # one for the change, one for the skip
    # Databricks rejects non-deterministic functions such as uuid() inside a VALUES list; they belong in the SELECT.
    assert "SELECT uuid()" in audits[1][0] and "VALUES (uuid()" not in audits[1][0]


def test_nothing_changed_means_every_id_is_skipped():
    sql = FakeSql()
    d = DatabricksSource(sql).decide("REJECTED", ["TR-0000000001"], "ava@example.com", "no truck", "req2")
    assert d.changed == [] and d.skipped == ["TR-0000000001"]
    inserts = [c[0] for c in sql.calls if c[0].startswith("INSERT INTO transfer_audit")]
    assert len(inserts) == 1 and "VALUES" in inserts[0]  # only the skipped attempt is logged


@pytest.mark.parametrize("method", ["stores", "products"])
def test_dimension_reads_are_constant_statements(method: str):
    sql = FakeSql()
    getattr(DatabricksSource(sql), method)()
    assert sql.calls[0][1] == {}


def test_ask_cannot_run_without_a_space():
    r = DatabricksSource(FakeSql()).ask("anything")
    assert r.answered is False


def test_ask_turns_a_conversation_into_a_sentence_and_table():
    from types import SimpleNamespace as NS

    column = lambda n: NS(name=n)  # noqa: E731
    reply = NS(status="COMPLETED", conversation_id="c", message_id="m", id="m", attachments=[
        NS(attachment_id="a1", text=None, query=NS(description="Two stores will run low on generators. More text.")),
    ])
    result = NS(statement_response=NS(manifest=NS(schema=NS(columns=[column("store"), column("units_short")])),
                                      result=NS(data_array=[["Orlando", "53"], ["Tampa", "44"]])))
    genie = NS(start_conversation_and_wait=lambda space, q, timeout: reply,
               get_message_attachment_query_result=lambda *a: result)
    r = DatabricksSource(FakeSql(), genie, "space1").ask("who runs low?")
    assert r.answered and r.columns == ["store", "units_short"] and r.rows[1] == ["Tampa", "44"]


def test_dates_survive():  # sanity for the type conversion used by every query
    from app.dbx import convert

    assert convert("2026-10-08", "DATE") == date(2026, 10, 8) and convert("12", "LONG") == 12 and convert(None, "INT") is None
