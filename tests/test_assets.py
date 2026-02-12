# tests/test_assets.py

import pytest
from datetime import datetime, timezone
from src.assets import Asset


def test_asset_initialization_normalizes_ticker():
    """Test that tickers are uppercased and stripped."""
    asset = Asset(ticker="  aapl ", price=150.0)
    assert asset.ticker == "AAPL"
    assert asset.name == "AAPL"  # Should default to ticker


def test_asset_initialization_validation():
    """Test that negative price raises error."""
    with pytest.raises(ValueError):
        Asset(ticker="AAPL", price=-10.0)


def test_update_price():
    """Test updating the price."""
    asset = Asset(ticker="AAPL", price=100.0)

    new_ts = datetime.now(timezone.utc)
    asset.update_price(105.5, timestamp=new_ts)

    assert asset.price == 105.5
    assert asset.timestamp == new_ts


def test_asset_serialization_roundtrip():
    """Test to_dict and from_dict (Roundtrip)."""
    original = Asset(ticker="MSFT", price=300.0, name="Microsoft")

    # Serialize
    data = original.to_dict()
    assert data["ticker"] == "MSFT"
    assert data["price"] == 300.0

    # Deserialize
    restored = Asset.from_dict(data)

    assert restored.ticker == original.ticker
    assert restored.price == original.price
    assert restored.name == original.name
    assert restored.timestamp == original.timestamp
