import json
from pathlib import Path

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
    
def test_buy_insufficient_funds():
    p = Portfolio(cash=100.0)
    
    # Try to buy 10 shares at $20 each = $200 total
    # Should raise ValueError due to insufficient funds
    with pytest.raises(ValueError, match="Insufficient funds"):
        p.buy("TSLA", quantity=10, price=20.0)
        
    # Double check that no changes were made
    assert p.cash == 100.0
    assert "TSLA" not in p.holdings
    
    
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


def test_portfolio_save_creates_file_and_valid_json(tmp_path: Path):
    p = Portfolio(cash=1234.5)
    p.holdings["AAPL"] = 2

    out_file = tmp_path / "portfolio.json"
    ok = p.save(out_file)

    assert ok is True
    assert out_file.exists()

    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert "saved_at" in data
    assert data["cash"] == 1234.5
    assert data["holdings"] == {"AAPL": 2.0}


def test_portfolio_save_handles_write_error(monkeypatch, tmp_path: Path, capsys):
    p = Portfolio(cash=10.0)
    p.holdings["MSFT"] = 1

    out_file = tmp_path / "portfolio.json"

    def _boom(*args, **kwargs):
        raise PermissionError("nope")

    monkeypatch.setattr(Path, "write_text", _boom)

    ok = p.save(out_file)
    assert ok is False

    captured = capsys.readouterr()
    assert "ERROR: Could not save portfolio" in captured.out
    
    
