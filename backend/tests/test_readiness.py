"""Readiness counts products whose cover reaches the storm window plus the safety days."""
from app.readiness import label, score, storm_window_days


def test_window_counts_storm_and_heavy_rain_days_once():
    days = [("2026-10-10", "storm"), ("2026-10-10", "storm"), ("2026-10-11", "heavy_rain"), ("2026-10-12", "clear")]
    assert storm_window_days(days) == 2


def test_score_is_the_share_of_products_with_enough_cover():
    # window 3 days + 2 safety days = 5 days needed
    assert score([6, 5, 4, 999], window=3, safety_days=2) == 75  # 6, 5 and "no sales" are ready; 4 is not
    assert score([], window=3, safety_days=2) == 0


def test_labels_match_the_thresholds():
    assert (label(80), label(79), label(50), label(49)) == ("Ready", "Watch", "Watch", "At risk")
