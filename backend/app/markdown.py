"""Price markdown suggestions: surplus stock that would not sell in time at full price.

A markdown is suggested only when all of these hold:
- At the current pace the spare stock would take longer than the clearance window to sell.
- A discount of 10% to 40% clears more of it in the window, and brings in more cash than holding it.
Assumptions, shown to planners as a footnote:
- Each 10% off lifts sales by 15% (ELASTICITY = 1.5). Measure this on a pilot before relying on it.
- The window is 14 days. Discounts stop at 40%, so no product is sold below its cost by design.
# ponytail: no cost or margin data, so the cap stands in for "never below cost". Add cost when the pilot provides it.
"""

from __future__ import annotations

CLEAR_DAYS = 14
ELASTICITY = 1.5
DEMO_ELASTICITY = 4.0  # demo mode only: a stronger response, so the rule has examples to show
DISCOUNTS = (0.10, 0.20, 0.30, 0.40)


def suggest(spare_units: float, avg_daily: float, price: float, elasticity: float = ELASTICITY) -> dict | None:
    """The smallest discount that clears the spare stock, or None when a markdown is not worth it."""
    if spare_units <= 0 or avg_daily <= 0 or price <= 0:
        return None
    if spare_units / avg_daily <= CLEAR_DAYS:
        return None  # it sells at full price inside the window
    hold_usd = min(spare_units, avg_daily * CLEAR_DAYS) * price
    for discount in DISCOUNTS:
        pace = avg_daily * (1 + elasticity * discount)
        sold = min(spare_units, pace * CLEAR_DAYS)
        if sold >= spare_units or discount == DISCOUNTS[-1]:
            break
    cash_usd = sold * price * (1 - discount)
    extra = cash_usd - hold_usd
    if extra <= 0:
        return None
    return {
        "discount_pct": round(discount * 100),
        "new_price": round(price * (1 - discount), 2),
        "units_cleared": round(sold),
        "clears_all": sold >= spare_units,
        "extra_cash_usd": round(extra, 2),
    }
