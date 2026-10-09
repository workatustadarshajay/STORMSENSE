"""Storm readiness: how many of a store's products have enough cover to get through the storm window.

For each product, cover is ready when its days of cover reach the storm window plus the safety days.
The score is the share of ready products, 0 to 100. A product with no sales (cover 999) counts as ready.
ponytail: counts products equally; weight by sales protected when the planners ask for it.
"""

from __future__ import annotations

from collections.abc import Iterable

STORM_CONDITIONS = ("storm", "heavy_rain")
NO_SALES_COVER = 999


def storm_window_days(conditions: Iterable[tuple[str, str]]) -> int:
    """Days in the forecast that carry a storm or heavy rain. `conditions` is (date, condition) pairs."""
    return len({d for d, c in conditions if c in STORM_CONDITIONS})


def score(days_of_cover: Iterable[float], window: int, safety_days: float) -> int:
    covers = list(days_of_cover)
    if not covers:
        return 0
    need = window + safety_days
    ready = sum(1 for d in covers if d >= NO_SALES_COVER or d >= need)
    return round(100 * ready / len(covers))


def label(value: int) -> str:
    return "Ready" if value >= 80 else "Watch" if value >= 50 else "At risk"
