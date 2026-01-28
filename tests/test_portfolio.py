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
    
def test_sell_stock_success():
    """Test that selling increases cash and decreases holdings."""
    p = Portfolio(cash=1000.0)
    p.holdings["AAPL"] = 10.0 # User owns 10 shares
    
    # Action: Sell 5 shares at $100 each
    p.sell("AAPL", quantity=5, price=100.0)
    
    assert p.cash == 1500.0 # 1000 + (5 * 100)
    assert p.holdings["AAPL"] == 5.0 # 10 - 5
    
def test_sell_all_shares_removes_ticker():
    """Test that selling all shares removes the ticker from holdings."""
    p = Portfolio()
    p.holdings["TSLA"] = 5.0
    
    p.sell("TSLA", 5.0, 200.0)
    
    assert "TSLA" not in p.holdings
    assert p.cash > 10000.0 
    
def test_sell_not_enough_shares():
    """Test that selling more shares than owned raises an error."""
    p = Portfolio()
    p.holdings["NVDA"] = 2.0
    
    # Action & Assert: Try to sell 5 shares when we only have 2
    with pytest.raises(ValueError, match="Not enough shares"):
        p.sell("NVDA", 5.0, 100.0)
        
def test_sell_unowned_stock():
    """Test that selling a stock not owned raises an error."""
    p = Portfolio()
    
    # Action & Assert: Try to sell a stock not in holdings
    with pytest.raises(ValueError, match="do not own"):
        p.sell("GOOGL", 1.0, 100.0)
