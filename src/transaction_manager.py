from __future__ import annotations

import logging
from typing import Callable

from src.data_fetcher import QuoteFetchError, fetch_latest_quote
from src.errors import ValidationError
from src.logger import get_logger
from src.portfolio import Portfolio
from src.snapshot_store import SnapshotStore
from src.transaction_logger import log_transaction, utc_timestamp_iso_z
from src.validators import validate_positive_number, validate_ticker
from src.models.transaction import Transaction


# =========================
# Domain Exceptions
# =========================
class TransactionError(Exception):
    """Base class for all transaction related errors."""


class InvalidTickerError(TransactionError):
    """Raised when ticker is missing or invalid."""


class InvalidQuantityError(TransactionError):
    """Raised when quantity <= 0 or not numeric."""


class InvalidPriceError(TransactionError):
    """Raised when price <= 0 or not numeric."""


class PriceFetchError(TransactionError):
    """Raised when price provider/data fetcher fails."""


class MarketClosedError(TransactionError):
    """Raised when attempting to trade outside regular market hours."""


class InsufficientFundsError(TransactionError):
    """Raised when there is not enough cash to buy."""


class InsufficientHoldingsError(TransactionError):
    """Raised when trying to sell more than owned."""


PriceProvider = Callable[[str], float]
MarketOpenCheck = Callable[[str], bool]
MarketStateProvider = Callable[[str], str]
TxLogger = Callable[[Transaction], bool]


class TransactionManager:
    """
    Central business logic for buy/sell.

    - No I/O (no input/print).
    - Price lookup is injected (mockable).
    - Validates via src.validators.
    - Optional market open check (injectable) to support MarketClosedError.
    """

    def __init__(
        self,
        *,
        portfolio: Portfolio,
        price_provider: PriceProvider | None = None,
        logger: logging.Logger | None = None,
        transaction_logger: TxLogger = log_transaction,
        snapshot_store: SnapshotStore | None = None,
        market_open_check: MarketOpenCheck | None = None,
        market_state_provider: MarketStateProvider | None = None,
    ) -> None:
        self.portfolio = portfolio
        self.price_provider = price_provider or self._default_price_provider
        self.log = logger or get_logger(__name__)
        self.transaction_logger = transaction_logger
        self.snapshot_store = snapshot_store

        # Optional: enables MarketClosedError when provided
        self.market_open_check = market_open_check
        self.market_state_provider = market_state_provider

    # -------------------------
    # Public API (AC)
    # -------------------------
    def buy(self, ticker: str, amount: float) -> Transaction:
        clean_ticker = self._validate_ticker(ticker)
        qty = self._validate_quantity(amount)

        self._ensure_market_open(clean_ticker)

        price = self._get_price(clean_ticker)
        total_cost = qty * price

        if self.portfolio.cash < total_cost:
            raise InsufficientFundsError(
                f"Not enough cash to buy {qty} shares of {clean_ticker}. "
                f"Need {total_cost:.2f}, have {self.portfolio.cash:.2f}."
            )

        # mutate after all checks => atomic on expected failures
        self.portfolio.cash -= total_cost
        self.portfolio.holdings[clean_ticker] = self.portfolio.holdings.get(clean_ticker, 0.0) + qty

        if self.snapshot_store:
            holdings_value = self.portfolio.holdings.get(clean_ticker, 0.0) * price
            self.snapshot_store.append_snapshot(
                event="BUY",
                ticker=clean_ticker,
                quantity=qty,
                price=price,
                cash=self.portfolio.cash,
                holdings_value=holdings_value,
            )

        tx = Transaction(
            kind="buy",
            ticker=clean_ticker,
            quantity=qty,
            price=price,
            gross_amount=total_cost,
            cash_after=self.portfolio.cash,
            timestamp=utc_timestamp_iso_z(),
        )

        self.transaction_logger(tx)
        self.log.info(
            "TRADE BUY ticker=%s qty=%s price=%s total=%s ts=%s cash_after=%s",
            tx.ticker,
            tx.quantity,
            tx.price,
            tx.gross_amount,
            tx.timestamp,
            tx.cash_after,
        )
        return tx

    def sell(self, ticker: str, amount: float) -> Transaction:
        clean_ticker = self._validate_ticker(ticker)
        qty = self._validate_quantity(amount)

        self._ensure_market_open(clean_ticker)

        owned = self.portfolio.holdings.get(clean_ticker, 0.0)
        if owned < qty:
            raise InsufficientHoldingsError(
                f"Not enough shares to sell {qty} of {clean_ticker}. "
                f"Owned {owned}."
            )

        price = self._get_price(clean_ticker)
        total_proceeds = qty * price

        # mutate after all checks => atomic on expected failures
        self.portfolio.cash += total_proceeds

        remaining = owned - qty
        if remaining <= 0:
            self.portfolio.holdings.pop(clean_ticker, None)
        else:
            self.portfolio.holdings[clean_ticker] = remaining

        if self.snapshot_store:
            holdings_value = self.portfolio.holdings.get(clean_ticker, 0.0) * price
            self.snapshot_store.append_snapshot(
                event="SELL",
                ticker=clean_ticker,
                quantity=qty,
                price=price,
                cash=self.portfolio.cash,
                holdings_value=holdings_value,
            )

        tx = Transaction(
            kind="sell",
            ticker=clean_ticker,
            quantity=qty,
            price=price,
            gross_amount=total_proceeds,
            cash_after=self.portfolio.cash,
            timestamp=utc_timestamp_iso_z(),
        )

        self.transaction_logger(tx)
        self.log.info(
            "TRADE SELL ticker=%s qty=%s price=%s total=%s ts=%s cash_after=%s",
            tx.ticker,
            tx.quantity,
            tx.price,
            tx.gross_amount,
            tx.timestamp,
            tx.cash_after,
        )
        return tx

    # -------------------------
    # Internals
    # -------------------------
    def _ensure_market_open(self, ticker: str) -> None:
        """
        Optional market-hours gate.
        Only enforced when a market_open_check is provided.
        """
        if self.market_open_check is None:
            return

        try:
            is_open = bool(self.market_open_check(ticker))
        except Exception as exc:
            # Fail-open to avoid random blocking if check fails
            self.log.warning("Market open check failed for %s: %s", ticker, exc, exc_info=True)
            return

        if not is_open:
            state = ""
            if self.market_state_provider is not None:
                try:
                    state = str(self.market_state_provider(ticker))
                except Exception:
                    state = ""
            msg = f"Cannot trade {ticker} - market is not in regular trading hours"
            if state:
                msg += f" (current state: {state})"
            raise MarketClosedError(msg)

    def _default_price_provider(self, ticker: str) -> float:
        quote = fetch_latest_quote(ticker)
        return float(quote.price)

    def _get_price(self, ticker: str) -> float:
        try:
            price = self.price_provider(ticker)
        except QuoteFetchError as exc:
            raise PriceFetchError(f"Could not fetch latest price for '{ticker}'. ({exc})") from exc
        except Exception as exc:
            raise PriceFetchError(f"Could not fetch latest price for '{ticker}'. ({exc})") from exc

        if not isinstance(price, (int, float)):
            raise PriceFetchError(f"Price provider returned non-numeric price for '{ticker}'.")

        price_f = float(price)
        if price_f <= 0:
            raise PriceFetchError(f"Price provider returned invalid price {price_f} for '{ticker}'.")

        return price_f

    def _validate_ticker(self, ticker: object) -> str:
        if not isinstance(ticker, str):
            raise InvalidTickerError("Ticker must be a non-empty string.")
        try:
            return validate_ticker(ticker)
        except ValidationError as exc:
            raise InvalidTickerError(str(exc)) from exc

    def _validate_quantity(self, qty: object) -> float:
        try:
            return validate_positive_number(qty, name="quantity")
        except ValidationError as exc:
            raise InvalidQuantityError(str(exc)) from exc
