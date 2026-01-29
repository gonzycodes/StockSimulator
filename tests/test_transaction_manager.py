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


# -------------------------
# BUY
# -------------------------

def test_buy_updates_cash_and_holdings():
    p = Portfolio(cash=1000.0)
    tm = TransactionManager()

    tx = tm.buy(p, ticker="AAPL", quantity=2, price=100.0)

    assert p.cash == 800.0
    assert p.holdings["AAPL"] == 2

    # Transaction summary
    assert tx.kind == "buy"
    assert tx.ticker == "AAPL"
    assert tx.quantity == 2
    assert tx.price == 100.0
    assert tx.gross_amount == 200.0
    assert tx.cash_after == 800.0


def test_buy_raises_if_insufficient_funds_and_does_not_mutate_portfolio():
    p = Portfolio(cash=50.0)
    p.holdings["AAPL"] = 1  # make sure holdings stay unchanged
    tm = TransactionManager()

    cash_before = p.cash
    holdings_before = dict(p.holdings)

    with pytest.raises(InsufficientFundsError):
        tm.buy(p, ticker="AAPL", quantity=1, price=100.0)

    # Atomicity: portfolio must be unchanged
    assert p.cash == cash_before
    assert p.holdings == holdings_before


# -------------------------
# SELL
# -------------------------

def test_sell_updates_cash_and_holdings():
    p = Portfolio(cash=1000.0)
    p.holdings["AAPL"] = 2
    tm = TransactionManager()

    tx = tm.sell(p, ticker="AAPL", quantity=1, price=100.0)

    assert p.cash == 1100.0
    assert p.holdings["AAPL"] == 1

    # Transaction summary
    assert tx.kind == "sell"
    assert tx.ticker == "AAPL"
    assert tx.quantity == 1
    assert tx.price == 100.0
    assert tx.gross_amount == 100.0
    assert tx.cash_after == 1100.0


def test_sell_removes_ticker_if_fully_sold():
    p = Portfolio(cash=1000.0)
    p.holdings["AAPL"] = 2
    tm = TransactionManager()

    tm.sell(p, ticker="AAPL", quantity=2, price=100.0)

    assert p.cash == 1200.0
    assert "AAPL" not in p.holdings


def test_sell_raises_if_insufficient_holdings_and_does_not_mutate_portfolio():
    p = Portfolio(cash=1000.0)
    p.holdings["AAPL"] = 1
    tm = TransactionManager()

    cash_before = p.cash
    holdings_before = dict(p.holdings)

    with pytest.raises(InsufficientHoldingsError):
        tm.sell(p, ticker="AAPL", quantity=2, price=100.0)

    # Atomicity: portfolio must be unchanged
    assert p.cash == cash_before
    assert p.holdings == holdings_before


# -------------------------
# INPUT VALIDATION
# -------------------------

def test_validate_inputs_raises_on_invalid_ticker():
    p = Portfolio(cash=1000.0)
    tm = TransactionManager()

    with pytest.raises(InvalidTickerError):
        tm.buy(p, ticker="", quantity=1, price=100.0)

    with pytest.raises(InvalidTickerError):
        tm.buy(p, ticker="   ", quantity=1, price=100.0)

    with pytest.raises(InvalidTickerError):
        tm.buy(p, ticker=123, quantity=1, price=100.0)  # type: ignore[arg-type]


def test_validate_inputs_raises_on_invalid_quantity():
    p = Portfolio(cash=1000.0)
    tm = TransactionManager()

    with pytest.raises(InvalidQuantityError):
        tm.buy(p, ticker="AAPL", quantity=0, price=100.0)

    with pytest.raises(InvalidQuantityError):
        tm.buy(p, ticker="AAPL", quantity=-1, price=100.0)

    with pytest.raises(InvalidQuantityError):
        tm.buy(p, ticker="AAPL", quantity="10", price=100.0)  # type: ignore[arg-type]


def test_validate_inputs_raises_on_invalid_price():
    p = Portfolio(cash=1000.0)
    tm = TransactionManager()

    with pytest.raises(InvalidPriceError):
        tm.buy(p, ticker="AAPL", quantity=1, price=0)

    with pytest.raises(InvalidPriceError):
        tm.buy(p, ticker="AAPL", quantity=1, price=-100)

    with pytest.raises(InvalidPriceError):
        tm.buy(p, ticker="AAPL", quantity=1, price="100")  # type: ignore[arg-type]
