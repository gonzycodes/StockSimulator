# tests/test_main_dispatch.py

"""
Tests for the safe simulation dispatch in src.main.

Focus:
- dispatch_line: command parsing + routing
- safe_dispatch: expected errors don't crash and produce friendly output
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.errors import FileError
from src.main import SimDeps, SimState, dispatch_line, safe_dispatch
from src.portfolio import Portfolio
from src.data_fetcher import Quote, QuoteFetchError, FetchErrorCode


def _quote(ticker: str = "AAPL", price: float = 100.0) -> Quote:
    """Create a deterministic quote for tests."""
    return Quote(
        ticker=ticker,
        price=price,
        currency="USD",
        timestamp=datetime(2026, 1, 27, 12, 0, 0, tzinfo=timezone.utc),
        company_name="Test Corp",
        price_sek=1000.0,
        fx_pair="USDSEK=X",
        fx_rate_to_sek=10.0,
    )


def test_dispatch_exit_returns_false() -> None:
    state = SimState(portfolio=Portfolio())
    deps = SimDeps(fetch_quote=lambda t: _quote(t), save_pf=lambda p: None)
    assert dispatch_line("exit", state, deps) is False
    assert dispatch_line("quit", state, deps) is False


def test_dispatch_empty_line_returns_true() -> None:
    state = SimState(portfolio=Portfolio())
    deps = SimDeps(fetch_quote=lambda t: _quote(t), save_pf=lambda p: None)
    assert dispatch_line("", state, deps) is True


def test_dispatch_unknown_command_prints_hint(capsys) -> None:
    state = SimState(portfolio=Portfolio())
    deps = SimDeps(fetch_quote=lambda t: _quote(t), save_pf=lambda p: None)

    assert dispatch_line("whatever", state, deps) is True
    out = capsys.readouterr().out
    assert "Unknown command" in out
    assert "help" in out


def test_safe_dispatch_quote_usage_error_does_not_crash(capsys) -> None:
    state = SimState(portfolio=Portfolio())
    deps = SimDeps(fetch_quote=lambda t: _quote(t), save_pf=lambda p: None)

    assert safe_dispatch("quote", state, deps) is True
    out = capsys.readouterr().out
    assert "Input error:" in out
    assert "Usage: quote <TICKER>" in out


def test_safe_dispatch_quote_success_prints_quote(capsys) -> None:
    state = SimState(portfolio=Portfolio())
    deps = SimDeps(fetch_quote=lambda t: _quote(t), save_pf=lambda p: None)

    assert safe_dispatch("quote aapl", state, deps) is True
    out = capsys.readouterr().out
    assert "AAPL" in out
    assert "100.00 USD" in out
    assert "1000.00 SEK" in out
    assert "Fetched at:" in out


def test_safe_dispatch_quote_not_found_maps_to_friendly_message(capsys) -> None:
    def fake_fetch(_: str) -> Quote:
        raise QuoteFetchError("not found", code=FetchErrorCode.NOT_FOUND)

    state = SimState(portfolio=Portfolio())
    deps = SimDeps(fetch_quote=fake_fetch, save_pf=lambda p: None)

    assert safe_dispatch("quote FAKE123", state, deps) is True
    out = capsys.readouterr().out
    assert "Market error:" in out
    assert "Ticker not found" in out


def test_safe_dispatch_sell_quantity_not_number(capsys) -> None:
    state = SimState(portfolio=Portfolio())
    deps = SimDeps(fetch_quote=lambda t: _quote(t), save_pf=lambda p: None)

    assert safe_dispatch("sell AAPL nope", state, deps) is True
    out = capsys.readouterr().out
    assert "Input error:" in out
    assert "Quantity must be a number" in out


def test_safe_dispatch_sell_quantity_negative(capsys) -> None:
    state = SimState(portfolio=Portfolio())
    deps = SimDeps(fetch_quote=lambda t: _quote(t), save_pf=lambda p: None)

    assert safe_dispatch("sell AAPL -1", state, deps) is True
    out = capsys.readouterr().out
    assert "Input error:" in out
    assert "greater than 0" in out


def test_safe_dispatch_sell_success_updates_portfolio_and_saves(capsys) -> None:
    pf = Portfolio(cash=1000.0)
    pf.holdings["AAPL"] = 10.0

    saved = {"called": False}

    def fake_save(_: Portfolio) -> None:
        saved["called"] = True

    state = SimState(portfolio=pf)
    deps = SimDeps(fetch_quote=lambda t: _quote(t, price=50.0), save_pf=fake_save)

    assert safe_dispatch("sell AAPL 2", state, deps) is True

    # Portfolio changed
    assert pf.holdings["AAPL"] == 8.0
    assert pf.cash == 1100.0  # 1000 + (2 * 50)

    # Save called
    assert saved["called"] is True

    out = capsys.readouterr().out
    assert "SUCCESS: Sold 2.0 shares of AAPL" in out


def test_safe_dispatch_sell_save_failure_is_caught(capsys) -> None:
    pf = Portfolio(cash=1000.0)
    pf.holdings["AAPL"] = 10.0

    def fake_save(_: Portfolio) -> None:
        raise FileError("disk full")

    state = SimState(portfolio=pf)
    deps = SimDeps(fetch_quote=lambda t: _quote(t, price=10.0), save_pf=fake_save)

    assert safe_dispatch("sell AAPL 1", state, deps) is True
    out = capsys.readouterr().out
    assert "File error:" in out
    assert "disk full" in out
