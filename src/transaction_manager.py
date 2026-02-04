from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
from src.portfolio import Portfolio
from src.snapshot_store import SnapshotStore


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


# ==========================================================
# Transaction result model
# ==========================================================
@dataclass(frozen=True)
class Transaction:
    """Represents a single completed transaction."""
    kind: Literal['buy', 'sell'] # Type of transaction
    ticker: str # Stock ticker symbol
    quantity: float # Number of shares bought/sold
    price: float # Price per share
    gross_amount: float # Quantity * Price
    cash_after: float # Cash balance after transaction


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
        """Processes a buy transaction:
        - Validates inputs
        - Checks available cash
        - Updates portfolio
        - Return Transaction result
        """

        # Validate basic input values
        self.validate_inputs(ticker, quantity, price)

        # Total cost of purchase
        gross_amount = quantity * price

        # Ensure sufficient cash
        if portfolio.cash < gross_amount:
            raise InsufficientFundsError(
                f"Not enough cash to buy {quantity} shares of {ticker}."
            )

        # Deduct cash from portfolio for purchase
        portfolio.cash -= gross_amount

        # Add or increase holdings in portfolio
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


        # Return transaction summary
        return Transaction(
            kind='buy',
            ticker=ticker,
            quantity=quantity,
            price=price,
            gross_amount=gross_amount,
            cash_after=portfolio.cash
        )
    

    def sell(
            self,
            portfolio: Portfolio,
            ticker: str,
            quantity: float,
            price: float
    ) -> Transaction:
        """Executes a sell transaction:
        - Validates inputs
        - Checks holdings
        - Updates portfolio
        - Return Transaction result
        """

        # Validate basic input values
        self.validate_inputs(ticker, quantity, price)

        # Amount currently owned
        owned = portfolio.holdings.get(ticker, 0.0)

        # Ensure sufficient holdings to sell
        if owned < quantity:
            raise InsufficientHoldingsError(
                f"Not enough shares to sell {quantity} of {ticker}."
            )
        
        # Total revenue from sale
        gross_amount = quantity * price

        # Add cash to portfolio from sale
        portfolio.cash += gross_amount

        # Update or remove holdings in portfolio
        remaining = owned - quantity
        if remaining <= 0:
            del portfolio.holdings[ticker] # Remove ticker if fully sold
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


        # Return transaction summary
        return Transaction(
            kind='sell',
            ticker=ticker,
            quantity=quantity,
            price=price,
            gross_amount=gross_amount,
            cash_after=portfolio.cash
        )
    
    
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