from src.portfolio import Portfolio
from src.formatters import format_portfolio_output


def test_empty_portfolio_shows_no_holdings_and_cash():
    p = Portfolio(cash=1000.0)
    out = format_portfolio_output(p, price_map={})

    assert "Cash: 1000.00" in out
    assert "No holdings" in out
    assert "Total value: 1000.00" in out


def test_total_value_calculated_from_price_map():
    p = Portfolio(cash=1000.0, holdings={"ERIC-B": 2, "HM-B": 1})
    out = format_portfolio_output(p, price_map={"ERIC-B": 100.0, "HM-B": 200.0})

    assert "Total value: 1400.00" in out
