import json
import pytest

from src.transaction_manager import TransactionManager
from src.portfolio import Portfolio


@pytest.fixture
def portfolio():
    return Portfolio(cash=10000.0)


@pytest.fixture
def price_map():
    # Mutable map so each test can set deterministic prices.
    return {
        "AAPL": 150.0,
        "TSLA": 200.0,
        "HM-B.ST": 120.0,
    }


@pytest.fixture
def tm(portfolio, price_map):
    def price_provider(ticker: str) -> float:
        return float(price_map[ticker])

    return TransactionManager(portfolio=portfolio, price_provider=price_provider)


@pytest.fixture
def temp_transactions_file(tmp_path, monkeypatch):
    """Use a temporary file instead of the real one."""
    fake_file = tmp_path / "transactions.json"
    monkeypatch.setattr("src.transaction_logger.TRANSACTIONS_FILE", fake_file)
    return fake_file


def test_buy_appends_to_transaction_history(
    portfolio, tm, price_map, temp_transactions_file
):
    price_map["AAPL"] = 150.0
    tm.buy("AAPL", 10.0)

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


def test_sell_appends_to_transaction_history(
    portfolio, tm, price_map, temp_transactions_file
):
    portfolio.holdings["AAPL"] = 15.0

    price_map["AAPL"] = 160.0
    tm.sell("AAPL", 6.0)

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


def test_sell_completely_removes_ticker(
    portfolio, tm, price_map, temp_transactions_file
):
    portfolio.holdings["TSLA"] = 5.0

    price_map["TSLA"] = 200.0
    tm.sell("TSLA", 5.0)

    assert "TSLA" not in portfolio.holdings
    assert portfolio.cash == pytest.approx(11000.0)

    with temp_transactions_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]["side"] == "SELL"
    assert data[0]["quantity"] == 5.0
