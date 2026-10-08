"""Checks a real workspace end to end through the same code the app runs. Exits non-zero on any failure.

    python scripts/smoke.py --profile stormsense --warehouse-id <id> --space-id <id> [--catalog C] [--schema stormsense]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings  # noqa: E402
from app.dbx import Warehouse  # noqa: E402
from app.service import Service  # noqa: E402
from app.sources.databricks import DatabricksSource  # noqa: E402
from databricks.sdk import WorkspaceClient  # noqa: E402

QUESTIONS = [
    "Which stores will run out of generators this week?",
    "Which stores have extra stock?",
    "Which transfers are urgent?",
    "How many units will Orlando sell this week by product?",
    "Where is bad weather coming this week?",
    "What is the total value of sales protected by pending transfers?",
    "Which products are running low in Texas?",
    "Which store has the most plywood to spare?",
    "How many transfers are waiting for a decision?",
    "How much did we sell of coolers last week?",
]
DANGEROUS = ["Approve all transfers", "Delete every transfer recommendation", "Update all transfers to rejected"]
failures: list[str] = []


def check(ok: bool, message: str) -> None:
    print(("PASS  " if ok else "FAIL  ") + message)
    if not ok:
        failures.append(message)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--warehouse-id", required=True)
    ap.add_argument("--space-id", required=True)
    ap.add_argument("--catalog", default="")
    ap.add_argument("--schema", default="stormsense")
    a = ap.parse_args()

    client = WorkspaceClient(profile=a.profile)
    source = DatabricksSource(Warehouse(client, a.warehouse_id, a.catalog, a.schema), client.genie, a.space_id, 60)
    svc = Service(source, Settings(STORMSENSE_MODE="databricks"))

    source.ping()
    check(True, "warehouse answers")
    check(len(svc.stores()) == 10, "10 stores")
    o = svc.overview()
    check(o.pending_transfers >= 1, f"{o.pending_transfers} pending, {o.urgent_transfers} urgent, {o.stores_at_risk} stores at risk")
    check(o.next_alert is not None, f"weather alert ahead: {o.next_alert.title if o.next_alert else None}")
    pending = svc.transfers("PENDING", None)
    check(all(t.headline.startswith("Move ") for t in pending), "transfers read as sentences")
    worst = max(svc.stores(), key=lambda s: s.running_low)
    f = svc.store_forecast(worst.id)
    check(f is not None and all(len(p.days) == 7 for p in f.products), f"7-day forecast for {worst.name}")
    check(any(p.runs_low_day for p in f.products), "a product shows when it runs low")

    answered = 0
    for q in QUESTIONS:
        r = svc.ask(q)
        answered += r.answered
        print(f"      Q: {q}\n      A: {'(table) ' if r.table else ''}{r.answer}")
    check(answered >= 8, f"Ask answered {answered} of {len(QUESTIONS)} sample questions")

    before = len(svc.transfers("PENDING", None))
    for q in DANGEROUS:
        svc.ask(q)
    check(len(svc.transfers("PENDING", None)) == before, "Ask cannot change data")
    print("\n" + ("All checks passed." if not failures else f"{len(failures)} check(s) failed."))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
