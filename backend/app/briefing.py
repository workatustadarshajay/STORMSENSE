"""The morning briefing: a few plain sentences built from today's figures. No model writes it, so nothing is made up."""

from __future__ import annotations

from typing import Any


def build(overview: Any, stores: list[Any], pending: list[Any], markdowns: list[Any]) -> dict[str, Any]:
    lines: list[str] = []
    urgent, waiting = overview.urgent_transfers, overview.pending_transfers
    if urgent:
        headline = f"Review {urgent} urgent move{'s' if urgent != 1 else ''} first."
    elif waiting:
        headline = "Nothing is urgent this morning."
    else:
        headline = "All caught up: no moves are waiting for a decision."
    lines.append(f"{urgent} urgent, {waiting} waiting for a decision in total.")

    if overview.next_alert:
        a = overview.next_alert
        names = ", ".join(a.stores[:3]) + (" and others" if len(a.stores) > 3 else "")
        lines.append(f"Next weather alert: {a.title}, for {names}.")
    else:
        lines.append("No storm or heat alert is forecast this week.")

    at_risk = [s for s in stores if s.readiness < 50]
    if stores:
        least = min(stores, key=lambda s: s.readiness)
        lines.append(f"{len(at_risk)} store{'s are' if len(at_risk) != 1 else ' is'} at risk. "
                     f"{least.name} is least ready, at {least.readiness}%.")

    if pending:
        top = max(pending, key=lambda t: (t.urgency == "URGENT", t.sales_protected_usd))
        lines.append(f"Biggest move: {top.headline}. It protects about ${top.sales_protected_usd:,.0f} in sales.")

    open_md = sum(1 for m in markdowns if m.decision == "pending")
    if open_md:
        lines.append(f"{open_md} price markdown{'s' if open_md != 1 else ''} to decide.")

    if overview.as_of:
        lines.append(f"Stock was counted on {overview.as_of:%d %B}.")
    return {"headline": headline, "lines": lines}
