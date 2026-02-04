import pytest

from src.portfolio import Portfolio
from src.transaction_manager import (
    TransactionManager,
    InvalidTickerError,
    InvalidQuantityError,
    InsufficientFundsError,
    InsufficientHoldingsError,
    PriceFetchError,
)


@pytest.fixture
def portfolio():
    """Simple portfolio with 1000 SEK cash and no holdings."""
    return Portfolio(cash=1000.0)


@pytest.fixture
def price_map():
    # Can be mutated per test to control the price deterministically.
    return {
        "AAPL": 120.0,
        "TSLA": 150.0,
        "ERIC-B.ST": 85.0,
        "GOOGL": 200.0,
        "NOKIA": 50.0,
    }


@pytest.fixture
def price_provider(price_map):
    def _get_price(ticker: str) -> float:
        return float(price_map[ticker])
    return _get_price


@pytest.fixture
def tm(portfolio, price_provider):
    return TransactionManager(portfolio=portfolio, price_provider=price_provider)


# ────────────────────────────────────────────────
# BUY-tests
# ────────────────────────────────────────────────

def test_buy_successful_updates_portfolio_and_returns_transaction(portfolio, tm):
    tx = tm.buy("AAPL", 2.5)

    assert portfolio.cash == pytest.approx(700.0)
    assert portfolio.holdings["AAPL"] == pytest.approx(2.5)

    assert tx.kind == "buy"
    assert tx.ticker == "AAPL"
    assert tx.quantity == pytest.approx(2.5)
    assert tx.price == pytest.approx(120.0)
    assert tx.gross_amount == pytest.approx(300.0)
    assert tx.cash_after == pytest.approx(700.0)
    assert isinstance(tx.timestamp, str) and tx.timestamp


def test_buy_insufficient_funds_raises_and_portfolio_unchanged(portfolio, tm):
    cash_before = portfolio.cash
    holdings_before = dict(portfolio.holdings)

    with pytest.raises(InsufficientFundsError):
        tm.buy("TSLA", 10)  # 10 * 150 = 1500 > 1000

    assert portfolio.cash == cash_before
    assert portfolio.holdings == holdings_before


def test_buy_zero_or_negative_quantity_raises(portfolio, tm):
    with pytest.raises(InvalidQuantityError):
        tm.buy("AAPL", 0)

    with pytest.raises(InvalidQuantityError):
        tm.buy("AAPL", -3)


def test_buy_invalid_ticker_raises(portfolio, tm):
    for bad_ticker in ["", "   ", 123, None]:  # type: ignore[list-item]
        with pytest.raises(InvalidTickerError):
            tm.buy(bad_ticker, 1)  # type: ignore[arg-type]


def test_buy_handles_price_provider_error_atomic(portfolio):
    def boom(_ticker: str) -> float:
        raise RuntimeError("provider down")

    tm = TransactionManager(portfolio=portfolio, price_provider=boom)

    cash_before = portfolio.cash
    holdings_before = dict(portfolio.holdings)

    with pytest.raises(PriceFetchError):
        tm.buy("AAPL", 1)

    assert portfolio.cash == cash_before
    assert portfolio.holdings == holdings_before


def test_buy_handles_price_provider_none_atomic(portfolio):
    def none_price(_ticker: str):
        return None  # type: ignore[return-value]

    tm = TransactionManager(portfolio=portfolio, price_provider=none_price)  # type: ignore[arg-type]

    cash_before = portfolio.cash
    holdings_before = dict(portfolio.holdings)

    with pytest.raises(PriceFetchError):
        tm.buy("AAPL", 1)

    assert portfolio.cash == cash_before
    assert portfolio.holdings == holdings_before


# ────────────────────────────────────────────────
# SELL-tests
# ────────────────────────────────────────────────

def test_sell_successful_updates_portfolio_and_returns_transaction(portfolio, tm, price_map):
    portfolio.holdings["AAPL"] = 5.0
    price_map["AAPL"] = 130.0

    tx = tm.sell("AAPL", 2)

    assert portfolio.cash == pytest.approx(1260.0)
    assert portfolio.holdings["AAPL"] == pytest.approx(3.0)

    assert tx.kind == "sell"
    assert tx.ticker == "AAPL"
    assert tx.quantity == pytest.approx(2.0)
    assert tx.price == pytest.approx(130.0)
    assert tx.gross_amount == pytest.approx(260.0)
    assert tx.cash_after == pytest.approx(1260.0)
    assert isinstance(tx.timestamp, str) and tx.timestamp


def test_sell_completely_removes_ticker_from_holdings(portfolio, tm):
    portfolio.holdings["ERIC-B.ST"] = 4.0
    tm.sell("ERIC-B.ST", 4.0)

    assert portfolio.cash == pytest.approx(1340.0)  # 1000 + (4*85)
    assert "ERIC-B.ST" not in portfolio.holdings


def test_sell_insufficient_holdings_raises_and_portfolio_unchanged(portfolio, tm):
    portfolio.holdings["AAPL"] = 3.0
    cash_before = portfolio.cash
    holdings_before = dict(portfolio.holdings)

    with pytest.raises(InsufficientHoldingsError):
        tm.sell("AAPL", 5.0)

    assert portfolio.cash == cash_before
    assert portfolio.holdings == holdings_before


def test_sell_non_existent_ticker_raises(portfolio, tm):
    with pytest.raises(InsufficientHoldingsError):
        tm.sell("NOKIA", 1)


def test_sell_cannot_sell_more_then_owned_ac_case(portfolio, tm):
    """Selling more than owned should raise and keep the portfolio unchanged."""
    portfolio.holdings["AAPL"] = 1.0
    cash_before = portfolio.cash
    holdings_before = dict(portfolio.holdings)

    with pytest.raises(InsufficientHoldingsError):
        tm.sell("AAPL", 2.0)

    assert portfolio.cash == cash_before
    assert portfolio.holdings == holdings_before
    assert portfolio.holdings["AAPL"] == 1.0


def test_sell_fractional_shares_supported(portfolio, tm):
    portfolio.holdings["GOOGL"] = 1.75
    tm.sell("GOOGL", 0.75)

    assert portfolio.holdings["GOOGL"] == pytest.approx(1.0)
    assert portfolio.cash == pytest.approx(1150.0)  # 1000 + (0.75*200)
