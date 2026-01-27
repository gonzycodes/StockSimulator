

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
        "regularMarketTime": 1737892000,   # → 2025-01-26 11:46:40 UTC
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