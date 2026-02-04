from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from src.config import SNAPSHOTS_FILE

log = logging.getLogger(__name__)
Clock = Callable[[], datetime]


@dataclass(frozen=True)
class Snapshot:
    """
    Immutable representation of a single portfolio snapshot
    
    Captures the portfolio state immediately after a successful trade
    Stored as one row in snapshots.csv
    """
    timestamp: str
    event: str
    ticker: str
    quantity: float
    price: float
    cash: float
    holdings_value: float
    total_value: float


class SnapshotStore:
    """
    Append-only CSV writer for portfolio snapshots.

    Responsibilities:
    - Create snapshot file if missing
    - Append one row per successful trade
    - Never overwrite history
    - Fail safely (log error, return False)

    Designed for:
    - Portfolio history tracking
    - Graphs / analytics later
    - Easy pandas/matplotlib import
    """    
    """Append-only snapshot writer for portfolio state after trades (CSV)."""

    def __init__(self, path: Path = SNAPSHOTS_FILE, clock: Optional[Clock] = None) -> None:
        self.path = path
        self.clock: Clock = clock or (lambda: datetime.now(timezone.utc))

    def append_snapshot(
        self,
        *,
        event: str,
        ticker: str,
        quantity: float,
        price: float,
        cash: float,
        holdings_value: float,
    ) -> bool:
        """
        Append a new snapshot row to the CSV file.

        Called after each successful BUY/SELL.

        Args:
            event: Trade type ("BUY" or "SELL")
            ticker: Stock symbol
            quantity: Shares traded
            price: Price per share
            cash: Current portfolio cash balance
            holdings_value: Total value of all holdings

        Returns:
            True if write succeeded, False otherwise.
        """        
        ts = self.clock().isoformat()
        total_value = cash + holdings_value

        snap = Snapshot(
            timestamp=ts,
            event=event,
            ticker=ticker,
            quantity=quantity,
            price=price,
            cash=cash,
            holdings_value=holdings_value,
            total_value=total_value,
        )

        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            file_exists = self.path.exists()

            with self.path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "timestamp",
                        "event",
                        "ticker",
                        "quantity",
                        "price",
                        "cash",
                        "holdings_value",
                        "total_value",
                    ],
                )
                if not file_exists:
                    writer.writeheader()
                writer.writerow(snap.__dict__)

            return True

        except OSError:
            log.error("Failed to write snapshot file: %s", self.path, exc_info=True)
            return False
