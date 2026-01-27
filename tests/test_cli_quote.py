# tests/test_cli_quote.py

"""
Tests for CLI quote command.
"""

from __future__ import annotations

from datetime import datetime, timezone

from src.cli import cmd_quote, validate_ticker
from src.data_fetcher import Quote


def test_validate_ticker_trims_and_uppercases() -> None:
    assert validate_ticker("  aapl ") == "AAPL"
    
    
def test_cmd_quote_does_not_crash(monkeypatch, capsys) -> None:
    def fake_fetch_latest_quote(ticker: str) -> Quote:
        return Quote(ticker=ticker, price=123.45, timestamp=datetime(2026, 1, 27, tzinfo=timezone.utc))
    
    monkeypatch.setattr("src.cli.fetch_latest_quote", fake_fetch_latest_quote)
    
    code = cmd_quote(" aapl ")
    assert code == 0
    
    out = capsys.readouterr()
    assert "AAPL" in out.out
    assert "123.45" in out.out
    
    