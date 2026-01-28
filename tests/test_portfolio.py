import pytest
import json

from src.portfolio import Portfolio
from pathlib import Path

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
    
    