from dataclasses import dataclass, field
from typing import Dict

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
    
    def to_dict(self):
        return {
            "cash": self.cash,
            "holdings": dict(self.holdings)
        }