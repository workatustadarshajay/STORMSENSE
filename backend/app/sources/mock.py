"""Realistic fixture data behind the same interface as the live source, so the whole app runs with zero setup.

Fixtures are table dumps made by databricks/scripts/make_fixtures.py from the same code that builds the real tables.
Dates are shifted by whole weeks so the forecast always starts about today and weekdays stay correct.
"""
from __future__ import annotations

import json
import math
import re
import threading
import uuid
from copy import deepcopy
from datetime import date, datetime, timedelta
from pathlib import Path

from .base import AskResult, Decision, Row

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures.json"
DATE_COLS = {"as_of_date", "forecast_date", "runs_low_date", "stockout_date", "obs_date"}
TIME_COLS = {"created_at", "decided_at", "issued_at", "run_ts"}


class MockSource:
    def __init__(self, path: Path = FIXTURES, today: date | None = None) -> None:
        raw = json.loads(path.read_text())
        today = today or date.today()
        weeks = math.ceil(((today - timedelta(days=1)) - date.fromisoformat(raw["as_of"])).days / 7)
        shift = timedelta(days=7 * weeks)
        self.t: dict[str, list[Row]] = {n: [self._parse(r, shift) for r in rows] for n, rows in raw["tables"].items()}
        self.audit: list[Row] = []
        self._lock = threading.Lock()

    @staticmethod
    def _parse(row: Row, shift: timedelta) -> Row:
        out = dict(row)
        for k, v in row.items():
            if v is None:
                continue
            if k in DATE_COLS:
                out[k] = datetime.fromisoformat(v).date() + shift
            elif k in TIME_COLS:
                out[k] = datetime.fromisoformat(v) + shift
        return out

    # ---- reads ----------------------------------------------------------------------------
    def ping(self) -> None:
        return None

    def user(self, email: str) -> Row | None:
        return next((u for u in self.t["app_users"] if u["email"].lower() == email.lower()), None)

    def stores(self) -> list[Row]:
        return deepcopy(self.t["stores"])

    def products(self) -> list[Row]:
        return deepcopy(self.t["products"])

    def setting(self, key: str) -> str | None:
        return next((s["value"] for s in self.t["settings"] if s["key"] == key), None)

    def transfers(self, status: str | None, urgency: str | None, limit: int = 500) -> list[Row]:
        with self._lock:
            rows = [r for r in self.t["transfer_recommendations"]
                    if (status is None or r["status"] == status) and (urgency is None or r["urgency"] == urgency)]
            rows.sort(key=lambda r: (r["urgency"] != "URGENT", -(r["sales_protected_usd"] or 0), r["rec_id"]))
            return deepcopy(rows[:limit])

    def transfer(self, rec_id: str) -> Row | None:
        with self._lock:
            return deepcopy(next((r for r in self.t["transfer_recommendations"] if r["rec_id"] == rec_id), None))

    def history(self, limit: int = 200) -> list[Row]:
        with self._lock:
            rows = [r for r in self.t["transfer_recommendations"] if r["status"] != "PENDING"]
            rows.sort(key=lambda r: (r["decided_at"] or datetime.min, r["rec_id"]), reverse=True)
            return deepcopy(rows[:limit])

    def predictions(self, store_id: str) -> list[Row]:
        return [r for r in deepcopy(self.t["predictions"]) if r["store_id"] == store_id]

    def gaps(self, store_id: str | None, status: str | None) -> list[Row]:
        return [g for g in deepcopy(self.t["inventory_gaps"])
                if (store_id is None or g["store_id"] == store_id) and (status is None or g["status"] == status)]

    def weather(self, store_id: str | None) -> list[Row]:
        return [w for w in deepcopy(self.t["weather_forecast"]) if store_id is None or w["store_id"] == store_id]

    # ---- decisions: same rules as the live source -------------------------------------------------
    def decide(self, action: str, ids: list[str], actor: str, note: str | None, request_id: str,
               reason_code: str | None = None) -> Decision:
        changed, skipped = [], []
        with self._lock:
            by_id = {r["rec_id"]: r for r in self.t["transfer_recommendations"]}
            for rec_id in ids:
                r = by_id.get(rec_id)
                if r and r["status"] == "PENDING":
                    r.update(status=action, decided_by=actor, decided_at=datetime.now(), decision_note=note,
                             decision_request_id=request_id)
                    changed.append(rec_id)
                else:
                    skipped.append(rec_id)
            now = datetime.now()
            for rec_id in changed:
                self.audit.append(dict(audit_id=uuid.uuid4().hex, event_ts=now, actor=actor, action=action, rec_id=rec_id,
                                       request_id=request_id, note=note))
            for rec_id in skipped:
                self.audit.append(dict(audit_id=uuid.uuid4().hex, event_ts=now, actor=actor, action="SKIPPED", rec_id=rec_id,
                                       request_id=request_id, note=note))
        return Decision(changed=changed, skipped=skipped)

    # ---- ask: a few plain intents over the fixture data --------------------------------------------
    def ask(self, question: str) -> AskResult:
        q = question.lower()
        names = {s["store_id"]: s["name"] for s in self.t["stores"]}
        products = self.t["products"]
        hit = next((p for p in products if any(w in q for w in _keywords(p["name"]))), None)
        gaps = [g for g in self.t["inventory_gaps"] if hit is None or g["product_id"] == hit["product_id"]]
        what = hit["name_plural"] if hit else "products"
        pname = {p["product_id"]: p["name"] for p in products}

        if re.search(r"run out|running low|short|low|need|stockout", q):
            rows = sorted((g for g in gaps if g["status"] == "SHORTAGE"), key=lambda g: g["runs_low_date"] or date.max)
            if not rows:
                return AskResult(True, f"No stores are expected to run low on {what} this week.")
            first = rows[0]
            return AskResult(True, f"{len(rows)} store{'s' if len(rows) != 1 else ''} will run low on {what} this week, "
                                   f"starting with {names[first['store_id']]} on {first['runs_low_date']:%A}.",
                             ["Store", "Product", "Runs low", "Units short"],
                             [[names[g["store_id"]], pname[g["product_id"]], f"{g['runs_low_date']:%A}", round(g["shortfall_units"])]
                              for g in rows])
        if re.search(r"extra|surplus|spare|too much|overstock", q):
            rows = sorted((g for g in gaps if g["status"] == "SURPLUS"), key=lambda g: -g["spare_units"])
            if not rows:
                return AskResult(True, f"No stores have extra {what} to spare.")
            return AskResult(True, f"{len(rows)} store{'s' if len(rows) != 1 else ''} have extra {what} to spare.",
                             ["Store", "Product", "Units to spare"],
                             [[names[g["store_id"]], pname[g["product_id"]], round(g["spare_units"])] for g in rows])
        if re.search(r"urgent|transfer|move|approve|pending", q):
            rows = [r for r in self.t["transfer_recommendations"] if r["status"] == "PENDING"
                    and (hit is None or r["product_id"] == hit["product_id"])]
            urgent = [r for r in rows if r["urgency"] == "URGENT"] if "urgent" in q else rows
            if not urgent:
                return AskResult(True, "No transfers are waiting for a decision.")
            state = "urgent" if "urgent" in q else "waiting for a decision"
            one = len(urgent) == 1
            return AskResult(True, f"{len(urgent)} transfer{'' if one else 's'} {'is' if one else 'are'} {state}.",
                             ["From", "To", "Product", "Units", "Urgency"],
                             [[names[r["source_store_id"]], names[r["dest_store_id"]], pname[r["product_id"]], r["qty"],
                               r["urgency"].title()] for r in urgent])
        return AskResult(False, "I couldn't answer that one. Try asking about stores, products or transfers.")


def _keywords(name: str) -> list[str]:
    return [w for w in name.lower().split() if w.isalpha() and len(w) > 3]

