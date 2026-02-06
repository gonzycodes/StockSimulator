import json
from pathlib import Path
import pytest

from src.transaction_manager import TransactionManager
from src.portfolio import Portfolio
from src.transaction_logger import log_transaction, TRANSACTIONS_FILE
from src.models.transaction import Transaction


@pytest.fixture
def portfolio():
    return Portfolio(cash=10000.0)


@pytest.fixture
def tm():
    return TransactionManager()


@pytest.fixture
def temp_transactions_file(tmp_path, monkeypatch):
    """Använd en temporär fil istället för den riktiga"""
    fake_file = tmp_path / "transactions.json"
    monkeypatch.setattr("src.transaction_logger.TRANSACTIONS_FILE", fake_file)
    return fake_file


def test_buy_appends_to_transaction_history(portfolio, tm, temp_transactions_file):
    tx = tm.buy(portfolio, ticker="AAPL", quantity=10.0, price=150.0)

    assert portfolio.cash == pytest.approx(8500.0)
    assert portfolio.holdings["AAPL"] == pytest.approx(10.0)

    assert temp_transactions_file.exists()

    with temp_transactions_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]["side"] == "BUY"
    assert data[0]["ticker"] == "AAPL"
    assert data[0]["quantity"] == 10.0
    assert data[0]["price"] == 150.0
    assert data[0]["total"] == pytest.approx(1500.0)
    assert data[0]["cash_after"] == pytest.approx(8500.0)


def test_sell_appends_to_transaction_history(portfolio, tm, temp_transactions_file):
    portfolio.holdings["AAPL"] = 15.0

    tx = tm.sell(portfolio, ticker="AAPL", quantity=6.0, price=160.0)

    assert portfolio.cash == pytest.approx(10960.0)
    assert portfolio.holdings["AAPL"] == pytest.approx(9.0)

    assert temp_transactions_file.exists()

    with temp_transactions_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]["side"] == "SELL"
    assert data[0]["ticker"] == "AAPL"
    assert data[0]["quantity"] == 6.0
    assert data[0]["price"] == 160.0
    assert data[0]["total"] == pytest.approx(960.0)
    assert data[0]["cash_after"] == pytest.approx(10960.0)


def test_sell_completely_removes_ticker(portfolio, tm, temp_transactions_file):
    portfolio.holdings["TSLA"] = 5.0

    tm.sell(portfolio, "TSLA", 5.0, 200.0)

    assert "TSLA" not in portfolio.holdings
    assert portfolio.cash == pytest.approx(11000.0)

    with temp_transactions_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]["side"] == "SELL"
    assert data[0]["quantity"] == 5.0

