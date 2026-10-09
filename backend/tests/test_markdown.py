"""A markdown is suggested only when the stock would not sell in time and the discount adds cash."""
from app.markdown import suggest


def test_stock_that_sells_at_full_price_gets_no_markdown():
    assert suggest(spare_units=30, avg_daily=5, price=10) is None  # 6 days of cover, inside the 14-day window


def test_the_smallest_discount_that_clears_the_stock_is_chosen():
    plan = suggest(spare_units=80, avg_daily=5, price=10)  # 16 days of cover
    assert plan is not None and plan["discount_pct"] == 10 and plan["clears_all"] is True
    assert plan["new_price"] == 9.0 and plan["extra_cash_usd"] > 0


def test_a_markdown_that_does_not_add_cash_is_not_suggested():
    assert suggest(spare_units=200, avg_daily=5, price=10) is None  # too much stock to clear, so the discount loses money


def test_no_surplus_or_no_sales_gives_nothing():
    assert suggest(0, 5, 10) is None and suggest(80, 0, 10) is None


def test_a_stronger_response_shows_a_markdown_where_the_live_assumption_does_not():
    from app.markdown import DEMO_ELASTICITY, ELASTICITY
    assert suggest(spare_units=39, avg_daily=1.7, price=100) is None
    plan = suggest(spare_units=39, avg_daily=1.7, price=100, elasticity=DEMO_ELASTICITY)
    assert plan is not None and plan["discount_pct"] == 20 and ELASTICITY < DEMO_ELASTICITY
