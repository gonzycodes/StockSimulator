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
    
    
def test_cmd_quote_outputs_currency_and_sek(monkeypatch, capsys) -> None:
    def fake_fetch_latest_quote(ticker: str) -> Quote:
        return Quote(
            ticker=ticker,
            price=123.4,
            currency="USD",
            timestamp=datetime(2026, 1, 27, 12, 0, 0, tzinfo=timezone.utc),
            company_name="Apple Inc.",
            price_sek=1300.5,
            fx_pair="USDSEK=X",
            fx_rate_to_sek=10.54,
        )

    monkeypatch.setattr("src.cli.fetch_latest_quote", fake_fetch_latest_quote)

    code = cmd_quote(" aapl ")
    assert code == 0

    out = capsys.readouterr().out
    assert "AAPL" in out
    assert "Apple Inc." in out
    assert "123.40 USD" in out
    assert "1300.50 SEK" in out
    assert "Fetched at:" in out
    
    