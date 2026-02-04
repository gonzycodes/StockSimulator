from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
from src.portfolio import Portfolio
from src.snapshot_store import SnapshotStore

from src.transaction_logger import log_transaction
from src.models.transaction import Transaction

# =========================
# Domain Exceptions
# =========================
class TransactionError(Exception):
    """Base class for all transaction related errors."""
    pass


class InvalidTickerError(TransactionError):
    """Raised when ticker is missing or invalid."""
    pass


class InvalidQuantityError(TransactionError):
    """Raised when quantity <= 0 or not numeric"""
    pass


class InvalidPriceError(TransactionError):
    """Raised when price <= 0 or not numeric"""
    pass


class InsufficientFundsError(TransactionError):
    """Raised when there is not enough cash to buy."""
    pass


class InsufficientHoldingsError(TransactionError):
    """Raised when trying to sell more than owned."""
    pass

# ===========================================================
# Central class for managing transactions
# ===========================================================

class TransactionManager:
    """Manages buy/sell transactions for a portfolio."""
    def __init__(self, snapshot_store: SnapshotStore | None = None) -> None:
        self.snapshot_store = snapshot_store

    def buy(
            self,
            portfolio: Portfolio,
            ticker: str,
            quantity: float,
            price: float
    ) -> Transaction:
        self.validate_inputs(ticker, quantity, price)
        
        gross_amount = quantity * price
        
        if portfolio.cash < gross_amount:
            raise InsufficientFundsError(
                f"Not enough cash to buy {quantity} shares of {ticker}."
            )

        portfolio.cash -= gross_amount
        portfolio.holdings[ticker] = portfolio.holdings.get(ticker, 0.0) + quantity
        if self.snapshot_store:
            holdings_value = portfolio.holdings.get(ticker, 0.0) * price
            self.snapshot_store.append_snapshot(
                event="BUY",
                ticker=ticker,
                quantity=quantity,
                price=price,
                cash=portfolio.cash,
                holdings_value=holdings_value,
            )



        
        tx = Transaction(
            kind='buy',
            ticker=ticker,
            quantity=quantity,
            price=price,
            gross_amount=gross_amount,
            cash_after=portfolio.cash
        )
        
        log_transaction(tx)
        return tx
    

    def sell(
            self,
            portfolio: Portfolio,
            ticker: str,
            quantity: float,
            price: float
    ) -> Transaction:
        self.validate_inputs(ticker, quantity, price)
        
        owned = portfolio.holdings.get(ticker, 0.0)
        
        if owned < quantity:
            raise InsufficientHoldingsError(
                f"Not enough shares to sell {quantity} of {ticker}."
            )
        
        gross_amount = quantity * price
        portfolio.cash += gross_amount
        
        remaining = owned - quantity
        if remaining <= 0:
            portfolio.holdings.pop(ticker, None)
        else:
            portfolio.holdings[ticker] = remaining
        
        if self.snapshot_store:
            holdings_value = portfolio.holdings.get(ticker, 0.0) * price
            self.snapshot_store.append_snapshot(
                event="SELL",
                ticker=ticker,
                quantity=quantity,
                price=price,
                cash=portfolio.cash,
                holdings_value=holdings_value,
            )


        
        tx = Transaction(
            kind='sell',
            ticker=ticker,
            quantity=quantity,
            price=price,
            gross_amount=gross_amount,
            cash_after=portfolio.cash
        )
        
        log_transaction(tx)
        return tx
    
    
    # =========================
    # Input Validation
    # =========================
    def validate_inputs(
            self,
            ticker: str,
            quantity: float,
            price: float
    ) -> None:
        """Validates basic transaction inputs."""

        # Validate ticker
        if not isinstance(ticker, str) or not ticker.strip():
            raise InvalidTickerError("Ticker must be a non-empty string.")

        # Validate quantity
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            raise InvalidQuantityError("Quantity must be a positive number.")

        # Validate price
        if not isinstance(price, (int, float)) or price <= 0:
            raise InvalidPriceError("Price must be a positive number.")
        
if __name__ == "__main__":
    from src.logger import init_logging_from_env
    from src.portfolio import Portfolio
    
    # Starta loggning
    init_logging_from_env()
    
    print("Starting test with buy and sell...\n")
    
    p = Portfolio(cash=10000.0)
    tm = TransactionManager()
    
    # Test 1: Buy 20 stocks from ERIC-B.ST for 95 kr/each
    try:
        tx_buy = tm.buy(p, ticker="ERIC-B.ST", quantity=20, price=95.0)
        print("buy completed!")
        print(f"  Cash after transaction: {p.cash:.2f} kr")
        print(f"  Holding after buy: {p.holdings}\n")
    except Exception as e:
        print("transaction failed:", e)
    
    # Test 2: Sell 8 stocks from ERIC-B.ST for 98 kr/each
    try:
        tx_sell = tm.sell(p, ticker="ERIC-B.ST", quantity=8, price=98.0)
        print("Sell completed!")
        print(f"  Cash after transaction: {p.cash:.2f} kr")
        print(f"  Holding after sell: {p.holdings}\n")
    except Exception as e:
        print("transaction failed:", e)
    
    print("Control now:")
    print("  • data/transactions.json   ← should have two posts (buy + sell)")
    print("  • logs/app.log            ← should have two INFO-lines")