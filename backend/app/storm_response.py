"""Storm response: when a storm is forecast, draft the whole response. Nothing is sent or moved until a planner decides.

The draft holds the moves waiting for a decision, the open markdown suggestions, the impact, and a draft note for
each affected store. A planner approves some moves and rejects the rest, in one step. Drafts are kept in memory,
so they reset when the server restarts.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from .carbon import estimate_kg_co2e


class ResponseBook:
    def __init__(self) -> None:
        self.drafts: dict[str, dict[str, Any]] = {}

    def open_for(self, source: str) -> dict[str, Any] | None:
        return next((d for d in self.drafts.values() if d["status"] == "draft" and d["source"] == source), None)


def draft_id(alert: Any) -> str:
    key = f"{alert.kind}|{alert.date}|{','.join(sorted(alert.stores))}"
    return "SR-" + hashlib.sha1(key.encode()).hexdigest()[:8].upper()


def build_draft(alert: Any, pending: list[Any], markdowns_open: int, source: str) -> dict[str, Any]:
    """A draft from the storm alert and the moves waiting. Pure: no sending, no decisions."""
    moves = [{
        "id": t.id, "headline": t.headline, "urgency": t.urgency, "qty": t.qty,
        "sales_protected_usd": round(float(t.sales_protected_usd), 2), "distance_miles": t.distance_miles,
        "co2_kg": estimate_kg_co2e(int(t.qty), int(t.distance_miles)), "reason": t.reason,
    } for t in pending]
    notes = [{
        "store": store,
        "text": (f"Storm expected {alert.weekday}: {alert.title}. "
                 f"Moves to and from {store} are being planned. Please confirm your delivery window and keep the aisles clear."),
    } for store in alert.stores]
    return {
        "id": draft_id(alert), "status": "draft", "source": source,
        "storm": alert.title, "weekday": alert.weekday, "onset": alert.date.isoformat(), "stores": list(alert.stores),
        "moves": moves,
        "protected_usd": round(sum(m["sales_protected_usd"] for m in moves), 2),
        "co2_kg": round(sum(m["co2_kg"] for m in moves), 1),
        "markdowns_open": markdowns_open, "store_notes": notes,
        "created_at": datetime.now().isoformat(timespec="seconds"), "decided_by": None, "decided_at": None,
        "approved": 0, "rejected": 0,
    }


def decide(draft: dict[str, Any], svc: Any, actor: str, approve_ids: list[str], reason: str) -> dict[str, Any]:
    """Approves the chosen moves and rejects the rest, through the same approval path as every other transfer."""
    ids = [m["id"] for m in draft["moves"]]
    approve = [i for i in dict.fromkeys(approve_ids) if i in ids]
    reject = [i for i in ids if i not in approve]
    if approve:
        svc.decide("APPROVED", approve, actor, None)
    if reject:
        svc.decide("REJECTED", reject, actor, reason, "OTHER")
    draft.update(status="decided", approved=len(approve), rejected=len(reject),
                 decided_by=actor, decided_at=datetime.now().isoformat(timespec="seconds"))
    return draft
