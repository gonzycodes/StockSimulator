# src/portfolio.py

"""
File helper: Portfolio domain model and persistence helpers.

This module defines the Portfolio class and provides a JSON save method
to persist portfolio state between runs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from src.config import DATA_DIR
from src.logger import get_logger

log = get_logger(__name__)

DEFAULT_FILENAME = "portfolio.json"
SCHEMA_VERSION = 1


def load_portfolio(path: Optional[Path] = None) -> Portfolio:
    """
    Loads the portfolio from a JSON file.

    - File missing          → returns default Portfolio + logs INFO
    - Invalid JSON / validation fails → returns default + logs ERROR + prints warning
    - Success               → returns loaded Portfolio + logs INFO

    Always returns a valid Portfolio object (never None).
    """
    target = (DATA_DIR / DEFAULT_FILENAME) if path is None else Path(path)

    if not target.exists():
        log.info(
            "Portfolio file not found at %s → starting with default portfolio", target
        )
        print(
            "No saved portfolio found. Starting with a new default portfolio (cash = 10000 SEK)."
        )
        return Portfolio()

    if not target.is_file():
        log.warning("Path exists but is not a file: %s → using default", target)
        print("Warning: Portfolio path is not a file. Starting with default.")
        return Portfolio()

    try:
        raw_content = target.read_text(encoding="utf-8")
        data = json.loads(raw_content)

        portfolio = parse_portfolio_dict(data)

        log.info(
            "Successfully loaded portfolio from %s | cash: %.2f | holdings: %d",
            target,
            portfolio.cash,
            len(portfolio.holdings),
        )

        return portfolio

    except json.JSONDecodeError as e:
        log.error("Corrupt/invalid JSON in portfolio file %s: %s", target, e)
        print("Warning: Save portfolio file is corrupt or invalid JSON.")
        print(f"Starting with default portfolio instead. (Error: {e})")
        return Portfolio()

    except ValueError as e:
        log.error("Validation failed when loading portfolio from %s: %s", target, e)
        print(
            "Warning: Saved portfolio contains invalid data (e.g negative cash or quantities)."
        )
        print(f"Starting with default portfolio instead. (Error: {e})")
        return Portfolio()

    except Exception:
        log.exception("Unexpected error loading portfolio from %s", target)
        print("Unexpected error while loading portfolio. Starting with default.")
        return Portfolio()


@dataclass
class Portfolio:
    cash: float = 10000.0
    holdings: Dict[str, float] = field(default_factory=dict)

    def total_value(self, price_map: Dict[str, float]) -> float:
        """Calculate total portfolio value including cash and holdings.

        Args:
            price_map: Mapping from ticker symbol to current price.

        Returns:
            Total portfolio value as float.
        """
        total = self.cash
        for ticker, amount in self.holdings.items():
            price = price_map.get(ticker, 0)
            total += amount * price
        return total

    def to_dict(self) -> Dict[str, Any]:
        """Convert portfolio to a serializable dictionary."""
        return {
            "cash": self.cash,
            "holdings": dict(self.holdings),
        }

    def buy(self, ticker: str, quantity: float, price: float) -> None:
        """
        Buys a specified amount of a stock.
        Updates cash, adds the ticker to holdings, and autosaves.

        Args:
            ticker: The stock symbol (e.g., 'AAPL').
            quantity: The amount of shares to buy.
            price: The current market price per share.

        Raises:
            ValueError: If the user does not have enough cash.
        """
        cost = quantity * price

        if cost > self.cash:
            raise ValueError(
                f"Insufficient funds. Cost: {cost:.2f}, Cash: {self.cash:.2f}"
            )

        self.cash -= cost

        current_qty = self.holdings.get(ticker, 0.0)
        self.holdings[ticker] = current_qty + quantity

        self.save()
        log.info("Autosaved portfolio after buying %s (%.2f units)", ticker, quantity)

    def sell(self, ticker: str, quantity: float, price: float) -> None:
        """Sell an asset and update cash/holdings + autosave."""
        if ticker not in self.holdings:
            raise ValueError(f"You do not own any shares of '{ticker}'.")

        current_quantity = self.holdings[ticker]
        if quantity > current_quantity:
            raise ValueError(
                f"Not enough shares. You have {current_quantity}, tried to sell {quantity}."
            )

        revenue = quantity * price
        self.cash += revenue
        self.holdings[ticker] -= quantity

        if self.holdings[ticker] <= 0:
            del self.holdings[ticker]

        self.save()
        log.info("Autosaved portfolio after selling %s (%.2f units)", ticker, quantity)

    def save(self, path: Path | None = None) -> bool:
        """Save portfolio to JSON. Returns True on success, False on error."""
        target = (DATA_DIR / DEFAULT_FILENAME) if path is None else Path(path)

        payload = {
            "schema_version": SCHEMA_VERSION,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            **self.to_dict(),
        }

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            _atomic_write_json(target, payload)
            return True
        except OSError as exc:
            log.error(
                "Failed to save portfolio to '%s': %s", target, exc, exc_info=True
            )
            print(
                f"ERROR: Could not save portfolio to '{target}'. Check permissions/disk."
            )
            return False


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Write JSON atomically to reduce risk of partial files."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    data = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)

    tmp_path.write_text(data, encoding="utf-8")
    tmp_path.replace(path)


def parse_portfolio_dict(data: dict) -> Portfolio:
    """
    Parses a dictionary loaded from JSON and creates a validated Portfolio object.

    Raises ValueError if any required field is missing, wrong type, or invalid value.
    This function is pure (no side effects) → easy to unit test.
    """
    version = data.get("schema_version")
    if version is None or version != SCHEMA_VERSION:
        raise ValueError(f"Unsupported or missing schema_version: {version}")

    cash_raw = data.get("cash")

    if cash_raw is None:
        raise ValueError("Missing 'cash' field in portfolio data")

    try:
        cash = float(cash_raw)
    except (TypeError, ValueError):
        raise ValueError(f"Cannot convert cash to number: {cash_raw!r}")

    if cash < 0:
        raise ValueError(f"Cash cannot be negative: {cash}")

    holdings_raw = data.get("holdings", {})
    if not isinstance(holdings_raw, dict):
        raise ValueError("Holdings must be a dictionary")
    holdings = {}
    for ticker, qty_raw in holdings_raw.items():
        if not isinstance(ticker, str) or not ticker.strip():
            raise ValueError(f"Invalid ticker format: '{ticker}'")

        if not isinstance(qty_raw, (int, float)):
            raise ValueError(
                f"Invalid quantity type for {ticker}: {type(qty_raw).__name__}"
            )
        qty = float(qty_raw)
        if qty < 0:
            raise ValueError(f"Quantity cannot be negative for {ticker}: {qty}")
        if qty > 0:
            holdings[ticker.upper()] = qty
    return Portfolio(cash=cash, holdings=holdings)
