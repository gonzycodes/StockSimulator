import pytest
from src.portfolio import Portfolio

def test_portfolio_default_cash():
    p = Portfolio()
    assert p.cash == 10000.0

def test_portfolio_total_value():
    p = Portfolio()
    p.holdings["HM-B"] = 2
    
    prices = {"HM-B": 100}
    assert p.total_value(prices) == 10200.0
def test_buy_changes_balance():
    p = Portfolio(cash=1000.0)
    p.buy("ERIC-B", quantity=2, price=100.0)
    
    assert p.cash == 800.0
    assert p.holdings["ERIC-B"] == 2