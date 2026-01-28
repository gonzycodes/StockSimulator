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
        
    def buy(self, ticker:str, quantity: float, price: float) -> None:
        cost = quantity * price
        if cost > self.cash:
            raise ValueError("Not enough cash")
        self.cash -= cost
        self.holdings[ticker] = self.holdings.get(ticker,0) +  quantity
        
    def sell(self, ticker: str, quantity: float, price: float) -> None:
        """
        Sells a specified amount of a stock.
        Updates cash and removes the ticker from holdings if amount becomes 0.
        
        Args:
            ticker: The stock symbol (e.g., 'AAPL').
            quantity: The amount of shares to sell.
            price: The current market price per share.
            
        Raises:
            ValueError: If user does not own the stock or tries to sell more than owned.
        """
        # 1. Validation: Do we own this ticker?
        # FIX: Removed "or self.holdings" which caused the bug
        if ticker not in self.holdings:
            raise ValueError(f"You do not own any shares of '{ticker}'.")
        
        # 2. Validation: Do we have enough shares?
        current_quantity = self.holdings[ticker]
        if quantity > current_quantity:
            raise ValueError(f"Not enough shares. You have {current_quantity}, tried to sell {quantity}.")

        # 3. Execute Transaction
        revenue = quantity * price
        self.cash += revenue
        self.holdings[ticker] -= quantity

        # 4. Cleanup: Remove ticker if holding is zero (or extremely close to zero)
        if self.holdings[ticker] <= 0:
            del self.holdings[ticker]