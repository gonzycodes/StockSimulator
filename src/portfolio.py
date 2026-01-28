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
from typing import Dict, Any

from src.config import DATA_DIR
from src.logger import get_logger

log = get_logger(__name__)

DEFAULT_FILENAME = "portfolio.json"
SCHEMA_VERSION = 1


@dataclass
class Portfolio:
    cash: float = 10000.0
    holdings: Dict[str,float] = field(default_factory=dict)
    
    def total_value(self, price_map: Dict[str, float]) -> float:
        """Calculate total portfolio value including cash and holdings

        Args:
            price_map: Mapping from ticker symbol to current price

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
            "holdings": dict(self.holdings)
        }
        
    def buy(self, ticker:str, quantity: float, price: float) -> None:
        """Buy an asset and update cash/holdings."""
        cost = quantity * price
        if cost > self.cash:
            raise ValueError("Not enough cash")
        self.cash -= cost
        self.holdings[ticker] = self.holdings.get(ticker,0) + quantity
        
    def save(self, path: Path | None = None) -> bool:
        """Save portfolio to JSON. Returns True on success, False on error."""
        target = (DATA_DIR / DEFAULT_FILENAME) if path is None else Path(path)
        
        payload = {
            "scema_version": SCHEMA_VERSION,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            **self.to_dict(),
        }
        
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            _atomic_write_json(target, payload)
            return True
        except OSError as exc:
            log.error("Failed to save portfolio to '%s': %s", target, exc, exc_info=True)
            print(f"ERROR: Could not save portfolio to '{target}'. Check permissions/disk.")
            return False
        
        
def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Write JSON atomically to reduce risk of partial files."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    data = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    
    tmp_path.write_text(data, encoding="utf-8")
    tmp_path.replace(path)
        