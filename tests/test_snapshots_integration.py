import csv
from datetime import datetime, timezone

from src.portfolio import Portfolio
from src.snapshot_store import SnapshotStore
from src.transaction_manager import TransactionManager


def test_two_trades_write_two_snapshots(tmp_path):
    # deterministic clock
    t0 = datetime(2026, 2, 4, 12, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 2, 4, 12, 1, 0, tzinfo=timezone.utc)
    times = [t0, t1]

    def clock():
        return times.pop(0)

    path = tmp_path / "snapshots.csv"
    store = SnapshotStore(path=path, clock=clock)

    p = Portfolio(cash=1000.0)

    prices = {"AAPL": 100.0}

    def price_provider(ticker: str) -> float:
        return float(prices[ticker])

    tm = TransactionManager(
        portfolio=p,
        price_provider=price_provider,
        snapshot_store=store,
    )

    tm.buy("AAPL", 2)  # cash -> 800, holdings_value -> 2*100=200, total -> 1000

    prices["AAPL"] = 110.0
    tm.sell(
        "AAPL", 1
    )  # cash -> 910, remaining=1, holdings_value -> 1*110=110, total -> 1020

    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    assert rows[0]["event"] == "BUY"
    assert rows[0]["timestamp"] == t0.isoformat()
    assert float(rows[0]["total_value"]) == 1000.0

    assert rows[1]["event"] == "SELL"
    assert rows[1]["timestamp"] == t1.isoformat()
    assert float(rows[1]["total_value"]) == 1020.0
