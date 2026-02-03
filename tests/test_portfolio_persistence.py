import pytest

from src.cli import save_portfolio, load_portfolio
from src.portfolio import Portfolio


def test_portfolio_save_load_roundtrip(tmp_path):
    # Arrange
    p = Portfolio(cash=1234.56, holdings={"AAPL": 2, "TSLA": 1})
    path = tmp_path / "portfolio.json"

    # Act
    save_portfolio(p, path=path)
    loaded = load_portfolio(path=path)

    # Assert
    assert loaded.cash == pytest.approx(1234.56)
    assert loaded.holdings == {"AAPL": 2, "TSLA": 1}
