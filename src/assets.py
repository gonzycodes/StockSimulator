# src/assets.py

"""
Domain model for financial assets (stocks).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any, Dict

from src.validators import validate_ticker


@dataclass
class Asset:
    """
    Represents a financial asset (e.g., a stock).

    Attributes:
        ticker (str): The symbol (e.g., 'AAPL'). Normalized to uppercase.
        price (float): The current or last known price.
        timestamp (datetime): When the price was last updated (UTC).
        name (str, optional): The full company name. Defaults to ticker if unknown.
    """

    ticker: str
    price: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    name: Optional[str] = None

    def __post_init__(self):
        """
        Validate and normalize data after initialization.
        """
        # Requirement: Ticker normalized (strip + uppercase)
        self.ticker = validate_ticker(self.ticker)

        # Requirement: Price validation
        # We allow 0.0 only if strictly needed, but usually price > 0.
        # Using validate_positive_float ensures it's a valid number.
        if self.price < 0:
            raise ValueError(f"Price cannot be negative: {self.price}")

        # Requirement: Name defaults to ticker if not provided
        if not self.name:
            self.name = self.ticker

    def update_price(
        self, new_price: float, timestamp: Optional[datetime] = None
    ) -> None:
        """
        Updates the price and timestamp of the asset.
        """
        if new_price < 0:
            raise ValueError(f"Price cannot be negative: {new_price}")

        self.price = float(new_price)
        self.timestamp = timestamp if timestamp else datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the asset to a dictionary (useful for saving to JSON).
        """
        return {
            "ticker": self.ticker,
            "name": self.name,
            "price": self.price,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Asset:
        """
        Creates an Asset instance from a dictionary.
        """
        return cls(
            ticker=data["ticker"],
            price=float(data["price"]),
            name=data.get("name"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )
