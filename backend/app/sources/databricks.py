"""Live data: SQL on the warehouse and questions to the Ask space.

Every statement is a constant string. Anything that varies is bound as a parameter. The only text assembled
at run time is a list of `:id0, :id1, ...` placeholders whose count (never content) comes from the request.
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from ..dbx import SqlRunner
from .base import AskResult, Decision, Row

log = logging.getLogger("stormsense.source")

# Latest forecast day-set and stock snapshot. Constant subqueries, no inputs.
_LATEST_GAPS = "(SELECT max(as_of_date) FROM inventory_gaps)"
_LATEST_PREDICTIONS = "(SELECT max(as_of_date) FROM predictions)"
_LATEST_WEATHER = "(SELECT max(issued_at) FROM weather_forecast)"

_FALLBACK = "I couldn't answer that one. Try asking about stores, products or transfers."


class DatabricksSource:
    def __init__(self, sql: SqlRunner, genie: Any | None = None, space_id: str = "", ask_timeout: int = 60) -> None:
        self.sql, self.genie, self.space_id, self.ask_timeout = sql, genie, space_id, ask_timeout

    # ---- reads ----------------------------------------------------------------------------
    def ping(self) -> None:
        self.sql.run("SELECT 1 AS ok")

    def user(self, email: str) -> Row | None:
        rows = self.sql.run("SELECT display_name, role FROM app_users WHERE lower(email) = lower(:email) LIMIT 1", {"email": email})
        return rows[0] if rows else None

    def stores(self) -> list[Row]:
        return self.sql.run("SELECT store_id, name, city, region FROM stores ORDER BY name")

    def products(self) -> list[Row]:
        return self.sql.run("SELECT product_id, name, name_plural, weather_driver, unit_price FROM products ORDER BY product_id")

    def setting(self, key: str) -> str | None:
        rows = self.sql.run("SELECT value FROM settings WHERE key = :key", {"key": key})
        return rows[0]["value"] if rows else None

    def transfers(self, status: str | None, urgency: str | None, limit: int = 500) -> list[Row]:
        return self.sql.run(
            "SELECT * FROM transfer_recommendations "
            "WHERE (:status IS NULL OR status = :status) AND (:urgency IS NULL OR urgency = :urgency) "
            "ORDER BY CASE urgency WHEN 'URGENT' THEN 0 ELSE 1 END, sales_protected_usd DESC, rec_id LIMIT :limit",
            {"status": status, "urgency": urgency, "limit": limit},
        )

    def transfer(self, rec_id: str) -> Row | None:
        rows = self.sql.run("SELECT * FROM transfer_recommendations WHERE rec_id = :rec_id", {"rec_id": rec_id})
        return rows[0] if rows else None

    def history(self, limit: int = 200) -> list[Row]:
        return self.sql.run(
            "SELECT * FROM transfer_recommendations WHERE status <> 'PENDING' ORDER BY decided_at DESC, rec_id LIMIT :limit",
            {"limit": limit},
        )

    def predictions(self, store_id: str) -> list[Row]:
        return self.sql.run(
            f"SELECT product_id, forecast_date, predicted_units, as_of_date FROM predictions "
            f"WHERE store_id = :store AND as_of_date = {_LATEST_PREDICTIONS} ORDER BY product_id, forecast_date",
            {"store": store_id},
        )

    def gaps(self, store_id: str | None, status: str | None) -> list[Row]:
        return self.sql.run(
            f"SELECT * FROM inventory_gaps WHERE as_of_date = {_LATEST_GAPS} "
            "AND (:store IS NULL OR store_id = :store) AND (:status IS NULL OR status = :status) ORDER BY store_id, product_id",
            {"store": store_id, "status": status},
        )

    def weather(self, store_id: str | None) -> list[Row]:
        return self.sql.run(
            "SELECT store_id, forecast_date, temp_max_f, rain_in, wind_max_mph, condition, event_name FROM weather_forecast "
            f"WHERE issued_at = {_LATEST_WEATHER} AND forecast_date > {_LATEST_GAPS} "
            f"AND forecast_date <= date_add({_LATEST_GAPS}, 7) AND (:store IS NULL OR store_id = :store) "
            "ORDER BY store_id, forecast_date",
            {"store": store_id},
        )

    # ---- decisions -------------------------------------------------------------------------
    def decide(self, action: str, ids: list[str], actor: str, note: str | None, request_id: str) -> Decision:
        """Approve or reject, touching only rows that are still PENDING.

        The update stamps this request's id on the rows it changes, so the rows reported back as changed are exactly
        those this request changed, even if someone else decides the same transfer at the same moment.
        """
        marks = ", ".join(f":id{i}" for i in range(len(ids)))  # placeholders only; values are bound below
        bound = {f"id{i}": v for i, v in enumerate(ids)}
        self.sql.run(
            "UPDATE transfer_recommendations SET status = :status, decided_by = :actor, decided_at = current_timestamp(), "
            f"decision_note = :note, decision_request_id = :req WHERE status = 'PENDING' AND rec_id IN ({marks})",
            {"status": action, "actor": actor, "note": note, "req": request_id, **bound},
        )
        changed = [r["rec_id"] for r in self.sql.run(
            "SELECT rec_id FROM transfer_recommendations WHERE decision_request_id = :req ORDER BY rec_id", {"req": request_id})]
        skipped = [i for i in ids if i not in set(changed)]
        if changed:
            self.sql.run(
                "INSERT INTO transfer_audit (audit_id, event_ts, actor, action, rec_id, request_id, note) "
                "SELECT uuid(), current_timestamp(), :actor, :status, rec_id, :req, :note "
                "FROM transfer_recommendations WHERE decision_request_id = :req",
                {"actor": actor, "status": action, "req": request_id, "note": note},
            )
        if skipped:
            listed = ", ".join(f"(:s{i})" for i in range(len(skipped)))  # placeholders only; values are bound below
            # uuid() is not allowed inside a VALUES list, so it is evaluated in the SELECT over that list.
            self.sql.run(
                "INSERT INTO transfer_audit (audit_id, event_ts, actor, action, rec_id, request_id, note) "
                f"SELECT uuid(), current_timestamp(), :actor, 'SKIPPED', t.rec_id, :req, :note FROM VALUES {listed} AS t(rec_id)",
                {"actor": actor, "req": request_id, "note": note, **{f"s{i}": v for i, v in enumerate(skipped)}},
            )
        return Decision(changed=changed, skipped=skipped)

    # ---- ask -------------------------------------------------------------------------------
    def ask(self, question: str) -> AskResult:
        """Send a question to the Ask space. It can only read; the result is shown, never executed by us."""
        if self.genie is None or not self.space_id:
            return AskResult(False, "Questions aren't available right now.")
        try:
            msg = self.genie.start_conversation_and_wait(self.space_id, question, timeout=timedelta(seconds=self.ask_timeout))
        except TimeoutError:
            return AskResult(False, "That's taking longer than expected. Try a simpler question, or try again in a moment.")
        if getattr(msg.status, "value", msg.status) != "COMPLETED":
            return AskResult(False, _FALLBACK)
        text, query_att = None, None
        for att in msg.attachments or []:
            text = text or (att.text.content if att.text else None)
            query_att = query_att or (att if att.query else None)
        answer = text or (query_att.query.description if query_att else None)
        columns = rows = None
        if query_att:
            res = self.genie.get_message_attachment_query_result(
                self.space_id, msg.conversation_id, msg.message_id or msg.id, query_att.attachment_id)
            stmt = res.statement_response
            if stmt and stmt.manifest and stmt.result and stmt.result.data_array:
                columns = [c.name for c in stmt.manifest.schema.columns]
                rows = [list(r) for r in stmt.result.data_array[:50]]
        if not answer and not rows:
            return AskResult(False, _FALLBACK)
        return AskResult(True, answer or "Here's what I found.", columns, rows)
