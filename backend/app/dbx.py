"""Databricks access: SQL through the warehouse, with bound parameters, retries and a friendly 'warming up' state."""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Protocol, TypeVar

log = logging.getLogger("stormsense.dbx")
T = TypeVar("T")


class WarmingUp(Exception):
    """The warehouse is still starting or busy; the caller should try again shortly."""


class QueryError(Exception):
    """A query failed. The cause is logged, never shown to planners."""


class SqlRunner(Protocol):
    def run(self, statement: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]: ...


_INT = {"BYTE", "SHORT", "INT", "LONG"}
_FLOAT = {"FLOAT", "DOUBLE", "DECIMAL"}


def convert(value: str | None, type_name: str) -> Any:
    """The statement API returns every value as text; restore the real type."""
    if value is None:
        return None
    if type_name in _INT:
        return int(value)
    if type_name in _FLOAT:
        return float(Decimal(value))
    if type_name == "BOOLEAN":
        return value.lower() == "true"
    if type_name == "DATE":
        return date.fromisoformat(value)
    if type_name in ("TIMESTAMP", "TIMESTAMP_NTZ"):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value


def param_type(value: Any) -> str:
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, int):
        return "INT" if -(2**31) <= value < 2**31 else "BIGINT"  # LIMIT and similar clauses reject BIGINT
    if isinstance(value, float):
        return "DOUBLE"
    return "STRING"


def with_retries(fn: Callable[[], T], attempts: int = 3, base_delay: float = 0.5,
                 sleep: Callable[[float], None] = time.sleep) -> T:
    """Retry transient failures (throttling, brief outages) with exponential backoff."""
    from databricks.sdk.errors import DeadlineExceeded, ResourceExhausted, TemporarilyUnavailable

    transient = (TemporarilyUnavailable, ResourceExhausted, DeadlineExceeded, ConnectionError, TimeoutError)
    for attempt in range(attempts):
        try:
            return fn()
        except transient as exc:
            if attempt == attempts - 1:
                raise
            log.warning("transient failure, retrying: %s", type(exc).__name__)
            sleep(base_delay * 2**attempt)
    raise AssertionError("unreachable")


class Warehouse:
    """Runs SQL on a serverless SQL warehouse as the app's own service principal."""

    def __init__(self, client: Any, warehouse_id: str, catalog: str, schema: str, budget_seconds: int = 45,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.client, self.warehouse_id = client, warehouse_id
        self.catalog, self.schema = catalog or None, schema
        self.budget, self._sleep = budget_seconds, sleep

    def run(self, statement: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        from databricks.sdk.service.sql import (
            Disposition,
            ExecuteStatementRequestOnWaitTimeout,
            Format,
            StatementParameterListItem,
            StatementState,
        )

        parameters = [StatementParameterListItem(name=k, value=None if v is None else str(v), type=param_type(v))
                      for k, v in (params or {}).items()]

        def submit() -> Any:
            return self.client.statement_execution.execute_statement(
                statement=statement, warehouse_id=self.warehouse_id, catalog=self.catalog, schema=self.schema,
                parameters=parameters, wait_timeout="20s", on_wait_timeout=ExecuteStatementRequestOnWaitTimeout.CONTINUE,
                disposition=Disposition.INLINE, format=Format.JSON_ARRAY, row_limit=5000,
            )

        deadline = time.monotonic() + self.budget
        resp, delay = with_retries(submit), 0.5
        statement_id = resp.statement_id
        while resp.status.state in (StatementState.PENDING, StatementState.RUNNING):
            if time.monotonic() > deadline:
                raise WarmingUp()
            self._sleep(delay)
            delay = min(delay * 1.6, 3.0)
            resp = with_retries(lambda: self.client.statement_execution.get_statement(statement_id))
        if resp.status.state != StatementState.SUCCEEDED:
            err = resp.status.error
            log.error("statement %s ended %s: %s", resp.statement_id, resp.status.state, err.message if err else "")
            raise QueryError()
        return _rows(resp)


def _rows(resp: Any) -> list[dict[str, Any]]:
    if not resp.manifest or not resp.result or not resp.result.data_array:
        return []
    cols = [(c.name, getattr(c.type_name, "value", str(c.type_name))) for c in resp.manifest.schema.columns]
    # ponytail: first chunk only (5,000 rows); every screen query is far smaller. Add chunk paging if that changes.
    return [{name: convert(v, typ) for (name, typ), v in zip(cols, row)} for row in resp.result.data_array]
