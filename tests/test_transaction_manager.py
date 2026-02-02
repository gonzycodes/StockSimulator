import pytest

from src.portfolio import Portfolio
from src.transaction_manager import (
    TransactionManager,
    InvalidTickerError,
    InvalidQuantityError,
    InvalidPriceError,
    InsufficientFundsError,
    InsufficientHoldingsError,
)


@pytest.fixture
def portfolio():
    """Enkel portfölj med 1000 SEK cash och inga innehav."""
    return Portfolio(cash=1000.0)


@pytest.fixture
def tm():
    """TransactionManager-instans."""
    return TransactionManager()


# ────────────────────────────────────────────────
# BUY-tests
# ────────────────────────────────────────────────

def test_buy_successful_updates_portfolio_and_returns_transaction(portfolio, tm):
    tx = tm.buy(portfolio, ticker="AAPL", quantity=2.5, price=120.0)

    assert portfolio.cash == pytest.approx(700.0)
    assert portfolio.holdings["AAPL"] == pytest.approx(2.5)

    assert tx.kind == "buy"
    assert tx.ticker == "AAPL"
    assert tx.quantity == pytest.approx(2.5)
    assert tx.price == pytest.approx(120.0)
    assert tx.gross_amount == pytest.approx(300.0)
    assert tx.cash_after == pytest.approx(700.0)


def test_buy_insufficient_funds_raises_and_portfolio_unchanged(portfolio, tm):
    cash_before = portfolio.cash
    holdings_before = dict(portfolio.holdings)

    with pytest.raises(InsufficientFundsError):
        tm.buy(portfolio, "TSLA", 10, 150.0)  # kostar 1500 > 1000

    assert portfolio.cash == cash_before
    assert portfolio.holdings == holdings_before


def test_buy_zero_or_negative_quantity_raises(portfolio, tm):
    with pytest.raises(InvalidQuantityError):
        tm.buy(portfolio, "AAPL", 0, 100.0)

    with pytest.raises(InvalidQuantityError):
        tm.buy(portfolio, "AAPL", -3, 100.0)


def test_buy_invalid_ticker_raises(portfolio, tm):
    for bad_ticker in ["", "   ", 123, None]:  # type: ignore[list-item]
        with pytest.raises(InvalidTickerError):
            tm.buy(portfolio, bad_ticker, 1, 100.0)


def test_buy_invalid_price_raises(portfolio, tm):
    for bad_price in [0, -50, "100", None]:  # type: ignore[list-item]
        with pytest.raises(InvalidPriceError):
            tm.buy(portfolio, "AAPL", 1, bad_price)


# ────────────────────────────────────────────────
# SELL-tests
# ────────────────────────────────────────────────

def test_sell_successful_updates_portfolio_and_returns_transaction(portfolio, tm):
    portfolio.holdings["AAPL"] = 5.0
    tx = tm.sell(portfolio, ticker="AAPL", quantity=2, price=130.0)

    assert portfolio.cash == pytest.approx(1260.0)
    assert portfolio.holdings["AAPL"] == pytest.approx(3.0)

    assert tx.kind == "sell"
    assert tx.ticker == "AAPL"
    assert tx.quantity == pytest.approx(2.0)
    assert tx.price == pytest.approx(130.0)
    assert tx.gross_amount == pytest.approx(260.0)
    assert tx.cash_after == pytest.approx(1260.0)


def test_sell_completely_removes_ticker_from_holdings(portfolio, tm):
    portfolio.holdings["ERIC-B.ST"] = 4.0
    tm.sell(portfolio, "ERIC-B.ST", 4.0, 85.0)

    assert portfolio.cash == pytest.approx(1340.0)
    assert "ERIC-B.ST" not in portfolio.holdings


def test_sell_insufficient_holdings_raises_and_portfolio_unchanged(portfolio, tm):
    portfolio.holdings["AAPL"] = 3.0
    cash_before = portfolio.cash
    holdings_before = dict(portfolio.holdings)

    with pytest.raises(InsufficientHoldingsError):
        tm.sell(portfolio, "AAPL", 5.0, 100.0)

    assert portfolio.cash == cash_before
    assert portfolio.holdings == holdings_before


def test_sell_non_existent_ticker_raises(portfolio, tm):
    with pytest.raises(InsufficientHoldingsError):  # eller annan exception beroende på implementation
        tm.sell(portfolio, "NOKIA", 1, 50.0)


# ────────────────────────────────────────────────
# Other / edge cases
# ────────────────────────────────────────────────

def test_buy_existing_holding_adds_to_quantity(portfolio, tm):
    portfolio.holdings["AAPL"] = 3.0
    tm.buy(portfolio, "AAPL", 2.0, 110.0)

    assert portfolio.holdings["AAPL"] == pytest.approx(5.0)
    assert portfolio.cash == pytest.approx(780.0)


def test_sell_fractional_shares_supported(portfolio, tm):
    portfolio.holdings["GOOGL"] = 1.75
    tm.sell(portfolio, "GOOGL", 0.75, 200.0)

    assert portfolio.holdings["GOOGL"] == pytest.approx(1.0)
    assert portfolio.cash == pytest.approx(1150.0)