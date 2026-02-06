import pandas as pd
from src.analytics import compute_pl


def test_compute_pl_returns_zeros_when_no_data():
    """
    Verify that analytics does not crash and returns zeros
    when no transaction data is provided.
    """
    out = compute_pl(pd.DataFrame())

    assert out["no_data"] is True
    assert out["realized_pl"] == 0.0
    assert out["unrealized_pl"] == 0.0
    assert out["total_pl"] == 0.0
    assert out["per_ticker"] == {}


def test_compute_pl_average_cost_realized_and_unrealized():
    """
    Verify average cost P/L calculation:
    - realized P/L from SELL
    - unrealized P/L from remaining holdings
    """
    # avg_cost = (10*100 + 10*110) / 20 = 105
    # realized (sell 5 @120) = (120 - 105) * 5 = 75
    # unrealized (15 left, latest 115) = (115 - 105) * 15 = 150
    df = pd.DataFrame(
        [
            {"ticker": "AAPL", "side": "BUY", "quantity": 10, "price": 100},
            {"ticker": "AAPL", "side": "BUY", "quantity": 10, "price": 110},
            {"ticker": "AAPL", "side": "SELL", "quantity": 5, "price": 120},
        ]
    )


    out = compute_pl(df, latest_prices={"AAPL": 115.0})

    # Core P/L results
    assert out["no_data"] is False
    assert out["realized_pl"] == 75.0
    assert out["unrealized_pl"] == 150.0
    assert out["total_pl"] == 225.0


    # Check per-ticker details
    aapl = out["per_ticker"]["AAPL"]
    assert aapl["qty"] == 15.0
    assert aapl["avg_cost"] == 105.0
    assert aapl["latest_price"] == 115.0
    assert aapl["unrealized_pl"] == 150.0