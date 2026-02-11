from unittest.mock import patch
import pytest

from data.yfinance_fetcher import get_latest_price, _extract_price_and_time


def test_extract_price_and_time_happy_path():
    fake_info = {
        "currentPrice": 150.25,
        "regularMarketTime": 1737891787,  # → 2025-01-26 11:43:07 UTC
    }
    price, ts_str = _extract_price_and_time(fake_info)
    assert price == 150.25
    assert ts_str == "2025-01-26 11:43:07"


def test_extract_price_and_time_missing_price():
    fake_info = {"regularMarketTime": 1737891787}
    with pytest.raises(ValueError, match="No price found"):
        _extract_price_and_time(fake_info)


@patch("data.yfinance_fetcher.yf.Ticker")
def test_get_latest_price_success(mock_ticker):
    fake_stock = mock_ticker.return_value
    fake_stock.info = {
        "currentPrice": 142.8,
        "regularMarketTime": 1737892000,  # → 2025-01-26 11:46:40 UTC
    }

    price, ts = get_latest_price("TSLA")
    assert price == 142.8
    assert isinstance(ts, str)
    assert ts == "2025-01-26 11:46:40"


@patch("data.yfinance_fetcher.yf.Ticker")
def test_get_latest_price_network_error(mock_ticker):
    mock_ticker.side_effect = Exception("Connection timeout")

    with pytest.raises(Exception, match="Connection timeout"):
        get_latest_price("MSFT")


def test_fetch_latest_quote_invalid_ticker():
    from src.data_fetcher import fetch_latest_quote, QuoteFetchError, FetchErrorCode

    with pytest.raises(QuoteFetchError) as exc:
        fetch_latest_quote("   ")

    assert exc.value.code == FetchErrorCode.VALIDATION


@patch("src.data_fetcher.yf.Ticker")
def test_fetch_latest_quote_not_found(mock_ticker):
    fake = mock_ticker.return_value
    fake.fast_info = {}
    fake.history.return_value = None

    from src.data_fetcher import fetch_latest_quote, QuoteFetchError, FetchErrorCode

    with pytest.raises(QuoteFetchError) as exc:
        fetch_latest_quote("FAKE123")

    assert exc.value.code == FetchErrorCode.NOT_FOUND


@patch("src.data_fetcher.yf.Ticker")
def test_fetch_latest_quote_network_error(mock_ticker):
    mock_ticker.side_effect = Exception("Connection timeout")

    from src.data_fetcher import fetch_latest_quote, QuoteFetchError, FetchErrorCode

    with pytest.raises(QuoteFetchError) as exc:
        fetch_latest_quote("MSFT")

    assert exc.value.code == FetchErrorCode.NETWORK
