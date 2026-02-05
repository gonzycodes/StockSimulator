# tests/test_report.py

"""
File helper: Tests for daily trade report.

Verifies:
- report renders key summary lines
- report writes to a temp directory (no touching real data/)
- no-trades scenario still produces a valid report
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.portfolio import Portfolio
from src.reporting import build_report_data, render_report, write_report_text


def _fixed_clock() -> datetime:
    """Return a fixed UTC time to make filenames deterministic."""
    return datetime(2026, 2, 5, 12, 0, 0, tzinfo=timezone.utc)


def test_report_no_trades_renders_and_writes(tmp_path: Path) -> None:
    """No transactions should still produce a report with 0 trades and 0 P/L."""
    portfolio = Portfolio(cash=1000.0, holdings={})
    tx_path = tmp_path / "transactions.json"  # does not exist on purpose

    def price_provider(_: str) -> float:
        raise AssertionError("price_provider should not be called when holdings are empty")

    data = build_report_data(
        portfolio=portfolio,
        transactions_path=tx_path,
        price_provider=price_provider,
        clock=_fixed_clock,
        recent_n=5,
    )
    text = render_report(data)

    assert "Trade Report" in text
    assert "Trades: 0" in text
    assert "Realized P/L: 0.00" in text
    assert "Unrealized P/L: 0.00" in text
    assert "Total P/L: 0.00" in text
    assert "Range: (no transactions found)" in text

    out_path = write_report_text(text=text, out_dir=tmp_path, clock=_fixed_clock)
    assert out_path.exists()
    assert out_path.name == "report_2026-02-05.txt"

    saved = out_path.read_text(encoding="utf-8")
    assert "Trades: 0" in saved


def test_report_includes_recent_trades_and_pl(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Report should include last N trades and P/L lines (deterministic via stubs)."""
    tx_path = tmp_path / "transactions.json"
    tx_path.write_text(
        json.dumps(
            [
                {
                    "timestamp": "2026-02-05T10:00:00Z",
                    "side": "BUY",
                    "ticker": "AAPL",
                    "quantity": 1.0,
                    "price": 100.0,
                    "total": 100.0,
                    "cash_after": 900.0,
                },
                {
                    "timestamp": "2026-02-05T10:05:00Z",
                    "side": "BUY",
                    "ticker": "MSFT",
                    "quantity": 2.0,
                    "price": 50.0,
                    "total": 100.0,
                    "cash_after": 800.0,
                },
            ],
            indent=2,
        ),
        encoding="utf-8",
    )

    portfolio = Portfolio(cash=800.0, holdings={"AAPL": 1.0, "MSFT": 2.0})

    def price_provider(ticker: str) -> float:
        prices = {"AAPL": 120.0, "MSFT": 60.0}
        return prices[ticker.upper()]

    # Stub analytics for deterministic P/L (avoid coupling test to analytics internals).
    import src.reporting as reporting_mod

    def fake_load_transactions_df(_: Path) -> object:
        return object()

    def fake_compute_pl(*, df, latest_prices, **kwargs):
        assert df is not None
        assert latest_prices["AAPL"] == 120.0
        assert latest_prices["MSFT"] == 60.0
        return {
            "realized_pl": 10.0,
            "unrealized_pl": 20.0,
            "total_pl": 30.0,
        }

    monkeypatch.setattr(reporting_mod, "load_transactions_df", fake_load_transactions_df, raising=False)
    monkeypatch.setattr(reporting_mod, "compute_pl", fake_compute_pl, raising=False)

    data = build_report_data(
        portfolio=portfolio,
        transactions_path=tx_path,
        price_provider=price_provider,
        clock=_fixed_clock,
        recent_n=2,
    )
    text = render_report(data)

    assert "Trades: 2" in text
    assert "Realized P/L: 10.00" in text
    assert "Unrealized P/L: 20.00" in text
    assert "Total P/L: 30.00" in text

    # Holdings should list tickers with prices
    assert "AAPL" in text
    assert "@ 120.00" in text
    assert "MSFT" in text
    assert "@ 60.00" in text

    # Recent trades section should include both trades (N=2)
    assert "Recent trades (last 2)" in text
    assert "BUY" in text
