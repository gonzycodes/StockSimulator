# tests/test_cli_smoke.py

from __future__ import annotations

import importlib
from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest


DATA_DIR_ENV = "STOCKSIM_DATA_DIR"


@dataclass
class FakeQuote:
    ticker: str
    price: float
    timestamp: datetime
    currency: str = "USD"
    company_name: str | None = None
    price_sek: float | None = None
    fx_pair: str | None = None
    fx_rate_to_sek: float | None = None


@pytest.fixture()
def cli(tmp_path, monkeypatch):
    """
    Load src.cli with an isolated data dir per test by reloading src.config + src.cli.
    This avoids touching repo-root data/ and makes tests deterministic.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv(DATA_DIR_ENV, str(data_dir))

    import src.config as config
    import src.cli as cli_mod

    importlib.reload(config)
    importlib.reload(cli_mod)
    return cli_mod


def test_cli_help_exits_0(cli):
    # argparse prints help and exits with SystemExit(0)
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0


def test_cli_quote_offline_returns_0_and_prints(cli, monkeypatch, capsys):
    def fake_fetch(ticker: str):
        return FakeQuote(
            ticker=ticker,
            price=123.45,
            timestamp=datetime(2026, 2, 11, 12, 0, tzinfo=timezone.utc),
            currency="USD",
            company_name="Test Corp",
        )

    monkeypatch.setattr(cli, "fetch_latest_quote", fake_fetch)

    rc = cli.main(["--log-level", "CRITICAL", "quote", "AAPL"])
    out = capsys.readouterr().out

    assert rc == 0
    assert "AAPL" in out
    assert "123.45" in out


def test_cli_buy_offline_returns_0(cli, monkeypatch, capsys):
    # Fake TransactionManager to avoid network / market-time logic
    class FakeTM:
        def __init__(self, portfolio, snapshot_store=None, logger=None):
            self.portfolio = portfolio

        def buy(self, ticker: str, quantity: float):
            self.portfolio.holdings[ticker] = (
                self.portfolio.holdings.get(ticker, 0.0) + quantity
            )
            self.portfolio.cash -= 100.0 * quantity
            return SimpleNamespace(
                ticker=ticker,
                quantity=quantity,
                price=100.0,
                gross_amount=100.0 * quantity,
            )

    monkeypatch.setattr(cli, "TransactionManager", FakeTM)

    rc = cli.main(["--log-level", "CRITICAL", "buy", "AAPL", "1"])
    out = capsys.readouterr().out

    assert rc == 0
    assert "SUCCESS: Bought" in out
    assert "AAPL" in out


def test_cli_save_then_load_offline_returns_0(cli, capsys):
    # save
    rc1 = cli.main(["--log-level", "CRITICAL", "save"])
    out1 = capsys.readouterr().out
    assert rc1 == 0
    assert "Saved portfolio" in out1

    # load
    rc2 = cli.main(["--log-level", "CRITICAL", "load"])
    out2 = capsys.readouterr().out
    assert rc2 == 0
    assert "Loaded portfolio" in out2
