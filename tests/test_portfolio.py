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