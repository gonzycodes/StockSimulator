# src/analytics.py

"""
Analytics for simple P/L calculation (TR-241).

- Uses pandas for basic analytics.
- Average cost model.
- Returns data only (presentation via CLI).
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Callable
import pandas as pd
from src.config import DATA_DIR
from src.data_fetcher import QuoteFetchError, fetch_latest_quote
from src.logger import get_logger

log = get_logger(__name__)

TRANSACTIONS_FILE = DATA_DIR / "transactions.json"


def load_transactions_df(path: Path | None = None) -> pd.DataFrame:
    """
    Load transaction history (JSON/CSV) into a DataFrame.
    Returns empty DataFrame if file is missing/invalid (no crash).
    """
    path = path or TRANSACTIONS_FILE

    if not path.exists():
        return pd.DataFrame()

    try:
        # Support both JSON and CSV (TR-241)
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path)
        else:
            df = pd.read_json(path)
    except Exception as e:
        log.error("Could not read transactions file %s: %s", path, e)
        return pd.DataFrame()

    if df is None or df.empty:
        return pd.DataFrame()

    # Always return normalized schema to keep compute_pl simpler/testable
    return normalize_transactions_df(df)


def normalize_transactions_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize to the schema compute_pl expects:
    ticker, side (BUY/SELL), quantity, price.
    """
    df = df.copy()

    # Standardize column names from whatever the file uses
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Allow both 'side' and 'kind' naming conventions
    if "side" not in df.columns and "kind" in df.columns:
        df["side"] = df["kind"]

    required = {"ticker", "side", "quantity", "price"}
    if not required.issubset(df.columns):
        log.warning("Transactions missing required columns: %s", required)
        return pd.DataFrame()

    # Convert types + normalize casing (defensive parsing)
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    df["side"] = df["side"].astype(str).str.strip().str.upper()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    # Remove invalid rows so analytics never crashes later
    df = df.dropna(subset=["ticker", "side", "quantity", "price"])
    df = df[df["side"].isin(["BUY", "SELL"])]
    df = df[(df["quantity"] > 0) & (df["price"] > 0)]

    return df.reset_index(drop=True)


def compute_pl(
    df: pd.DataFrame | None = None,
    *,
    tx_path: Path | None = None,
    latest_prices: dict[str, float] | None = None,
    price_fetcher: Callable[[str], Any] = fetch_latest_quote,
) -> dict[str, Any]:
    """
    Compute P/L using a simple average cost model (TR-241).
    Returns dict (presentation via CLI).
    """
    # If caller doesn't pass a DF, load from default transactions file.
    df = df if df is not None else load_transactions_df(tx_path)

    # Acceptance criteria: no crash if no data
    if df.empty:
        return {
            "no_data": True,
            "realized_pl": 0.0,
            "unrealized_pl": 0.0,
            "total_pl": 0.0,
            "per_ticker": {},
        }

    # Normalize injected prices (tests) to uppercase keys
    latest_prices = {k.upper(): float(v) for k, v in (latest_prices or {}).items()}

    # Track cost basis + remaining quantity per ticker (average cost)
    total_cost: dict[str, float] = {}
    total_qty: dict[str, float] = {}
    realized_pl = 0.0

    # --- Realized P/L: apply sells against current average cost ---
    for row in df.itertuples(index=False):
        ticker = row.ticker
        side = row.side
        qty = float(row.quantity)
        price = float(row.price)

        total_cost.setdefault(ticker, 0.0)
        total_qty.setdefault(ticker, 0.0)

        if side == "BUY":
            total_cost[ticker] += qty * price
            total_qty[ticker] += qty
            continue

        # SELL
        if total_qty[ticker] <= 0:
            log.warning("Sell without holdings for %s. Skipping.", ticker)
            continue

        avg_cost = total_cost[ticker] / total_qty[ticker]
        sold = min(qty, total_qty[ticker])

        realized_pl += (price - avg_cost) * sold

        # Reduce remaining position at avg_cost
        total_qty[ticker] -= sold
        total_cost[ticker] -= avg_cost * sold

    unrealized_pl = 0.0
    per_ticker: dict[str, Any] = {}

    # --- Unrealized P/L: value remaining holdings at latest price ---
    for ticker, qty_left in total_qty.items():
        if qty_left <= 0:
            continue

        avg_cost = total_cost[ticker] / qty_left

        # Prefer injected price (tests), else fetch (runtime)
        latest = latest_prices.get(ticker)
        if latest is None:
            try:
                quote = price_fetcher(ticker)
                latest = float(getattr(quote, "price"))
            except (QuoteFetchError, Exception) as e:
                log.warning("Could not fetch latest price for %s: %s", ticker, e)
                continue

        u = (latest - avg_cost) * qty_left
        unrealized_pl += u

        per_ticker[ticker] = {
            "qty": round(qty_left, 4),
            "avg_cost": round(avg_cost, 4),
            "latest_price": round(float(latest), 4),
            "unrealized_pl": round(u, 4),
        }

    total_pl = realized_pl + unrealized_pl

    return {
        "no_data": False,
        "realized_pl": round(realized_pl, 4),
        "unrealized_pl": round(unrealized_pl, 4),
        "total_pl": round(total_pl, 4),
        "per_ticker": per_ticker,
    }