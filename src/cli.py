from __future__ import annotations

import argparse
import sys
import json
from pathlib import Path
from typing import Dict

from json import JSONDecodeError


# Data fetch och errors
from src.transactions import (
    TransactionManager,
    TransactionError,
    MarketClosedError,
    InsufficientFundsError,
    InsufficientHoldingsError,
)
from src.data_fetcher import QuoteFetchError, fetch_latest_quote

# Portfolio, config, errors, validators, formatters
from src.portfolio import Portfolio
from src.config import DATA_DIR
from src.errors import FileError, ValidationError
from src.validators import validate_ticker, validate_positive_float
from src.formatters import format_portfolio_output
from src.snapshot_store import SnapshotStore

# Analytics
from src.analytics import compute_pl

try:
    from src.logger import init_logging, get_logger

    log = get_logger(__name__)
    
except Exception:  # pragma: no cover
    # Fallback if src.logger is not available yet
    import logging

    def init_logging(
        *,
        level: str = "INFO",
        log_file: str | Path = "logs/app.log",
        console: bool = True,
        max_bytes: int = 2000000,
        backup_count: int = 5,
    ) -> None:
        """Initialize basic logging."""
        logging.basicConfig(level=level)

    def get_logger(name: str):
        """Get a logger instance."""
        return logging.getLogger(name)

    log = get_logger(__name__)

PORTFOLIO_FILE = DATA_DIR / "portfolio.json"

def load_portfolio(path: Path = PORTFOLIO_FILE) -> Portfolio:
    """Load portfolio from disk. Returns a new portfolio if file not found."""
    if not path.exists():
        log.info("Portfolio file not found at %s, creating new portfolio.", path)
        print(f"No file found at {path}. Starting fresh.")
        return Portfolio()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        p = Portfolio()
        p.cash = float(data.get("cash", 10000.0))
        p.holdings = dict(data.get("holdings", {}))
        
        log.info("Loaded portfolio from %s", path)
        return p

    except (OSError, JSONDecodeError, ValueError, TypeError) as exc:
        # Log full detail for debugging, show friendly error via FileError
        log.warning("Failed to load portfolio file: %s", path, exc_info=True)
        print(f"Warning: Could not load portfolio ({exc}). Starting with default.")
        return Portfolio() # Return empty instead of crashing
    
    
def save_portfolio(portfolio: Portfolio, path: Path = PORTFOLIO_FILE) -> None:
    """Save the portfolio to disk as JSON."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(portfolio.to_dict(), f, indent=4)
        log.info("Saved portfolio to %s", path)
    except OSError as exc:
        log.error("Failed to save portfolio file: %s", path, exc_info=True)
        raise FileError(f"Could not save portfolio file: {path}") from exc


def build_parser() -> argparse.ArgumentParser:
    """
    Create and return the CLI argument parser.
    """
    parser = argparse.ArgumentParser(prog="stock-sim")
    parser.add_argument("--log-level", default="INFO", help="DEBUG|INFO|WARNING|ERROR|CRITICAL")

    sub = parser.add_subparsers(dest="command", required=True)

    q = sub.add_parser("quote", help="Fetch the latest price for a ticker.")
    q.add_argument("ticker", help="Ticker symbol, e.g. AAPL")

    s = sub.add_parser("sell", help="Sell an asset from the portfolio.")
    s.add_argument("ticker", help="Ticker symbol to sell, e.g. AAPL")
    s.add_argument("quantity", type=float, help="Number of shares to sell")
    
    b = sub.add_parser("buy", help="Buy an asset and add to the portfolio.")
    b.add_argument("ticker", help="Ticker symbol to buy, e.g. AAPL")
    b.add_argument("quantity", type=float, help="Number of shares to buy")
    
    p = sub.add_parser("portfolio", help="Show portfolio status (cash, holdings, total value).")

    sub.add_parser("analytics", help="Show Profit/Loss (realized + unrealized) from transactions.")

    sub.add_parser("save", help="Manually save the current portfolio to disk.")
    sub.add_parser("load", help="Manually reload the portfolio from disk.")

    return parser


def cmd_quote(ticker_raw: str) -> int:
    """
    Execute the quote command.
    """
    try:
        ticker = validate_ticker(ticker_raw)
        quote = fetch_latest_quote(ticker)

        currency = getattr(quote, "currency", "UNKNOWN")
        price_native = f"{quote.price:.2f}"

        local_ts = quote.timestamp.astimezone()
        ts_str = local_ts.strftime("%Y-%m-%d %H:%M:%S %Z")

        name_part = f" ({quote.company_name})" if getattr(quote, "company_name", None) else ""
        price_sek_val = getattr(quote, "price_sek", None)
        
        if price_sek_val is not None:
            price_sek = f"{float(price_sek_val):.2f}"
            
            fx_pair = getattr(quote, "fx_pair", None)
            fx_rate = getattr(quote, "fx_rate_to_sek", None)
            fx_part = ""
            if fx_pair and fx_rate:
                fx_part = f" (FX: {fx_pair} {float(fx_rate):.4f})"

            print(
                f"{quote.ticker}{name_part} "
                f"{price_native} {currency} | {price_sek} SEK "
                f"(Fetched at: {ts_str}){fx_part}"
            )
        else:
            print(
                f"{quote.ticker}{name_part} "
                f"{price_native} {currency} | SEK: N/A "
                f"(Fetched at: {ts_str})"
            )

        return 0

    except ValidationError as e:
        print(f"Input Error: {e}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 0
    except QuoteFetchError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 0
    except FileError as exc:
        print(f"File Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        log.exception("Unexpected CLI error")
        print(f"Error: Unexpected error: {exc}", file=sys.stderr)
        return 0


def cmd_buy(ticker_raw: str, quantity: float) -> int:
    """
    Execute the buy command via TransactionManager (includes market check).
    """
    try:
        ticker = validate_ticker(ticker_raw)
        valid_quantity = validate_positive_float(str(quantity))

        portfolio = load_portfolio()
        tm = TransactionManager(portfolio=portfolio, snapshot_store=SnapshotStore(), logger=log)

        tx = tm.buy(ticker, valid_quantity)
        save_portfolio(portfolio)

        print(f"SUCCESS: Bought {tx.quantity} shares of {tx.ticker} at {tx.price:.2f}.")
        print(f"Cost: {tx.gross_amount:.2f}. New Cash Balance: {portfolio.cash:.2f}")
        return 0
    
    except MarketClosedError as e:
        print(f"Trade blocked: {e}")
        log.warning("Buy blocked due to market state: %s", e)
        return 1
    except InsufficientFundsError as e:
        print(f"Insufficient funds: {e}")
        return 1
    except ValidationError as e:
        print(f"Input Error: {e}", file=sys.stderr)
        return 1
    except TransactionError as exc:
        print(f"Transaction Failed: {exc}", file=sys.stderr)
        return 1
    except FileError as exc:
        print(f"File Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        log.exception("Unexpected error during buy command")
        print(f"System Error: {exc}", file=sys.stderr)
        return 1


def cmd_sell(ticker_raw: str, quantity: float) -> int:
    """
    Execute the sell command via TransactionManager (includes market check).
    """
    try:
        ticker = validate_ticker(ticker_raw)
        valid_quantity = validate_positive_float(str(quantity))

        portfolio = load_portfolio()
        tm = TransactionManager(portfolio=portfolio, snapshot_store=SnapshotStore(), logger=log)

        tx = tm.sell(ticker, valid_quantity)
        save_portfolio(portfolio)

        print(f"SUCCESS: Sold {tx.quantity} shares of {tx.ticker} at {tx.price:.2f}.")
        print(f"Proceeds: {tx.gross_amount:.2f}. New Cash Balance: {portfolio.cash:.2f}")
        return 0

    except MarketClosedError as e:
        print(f"Trade blocked: {e}")
        log.warning("Sell blocked due to market state: %s", e)
        return 1
    except InsufficientHoldingsError as e:
        print(f"Insufficient holdings: {e}")
        return 1
    except ValidationError as e:
        print(f"Input Error: {e}", file=sys.stderr)
        return 1
    except TransactionError as exc:
        print(f"Transaction Failed: {exc}", file=sys.stderr)
        return 1
    except FileError as exc:
        print(f"File Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        log.exception("Unexpected error during sell command")
        print(f"System Error: {exc}", file=sys.stderr)
        return 1


def cmd_portfolio() -> int:
    try:
        portfolio = load_portfolio()
        price_map: Dict[str, float] = {}
        for ticker in portfolio.holdings.keys():
            try:
                quote = fetch_latest_quote(ticker)
                price_map[ticker] = float(quote.price)
            except QuoteFetchError as exc:
                log.warning("Price fetch failed for %s: %s", ticker, exc)
        output = format_portfolio_output(portfolio, price_map)
        print(output)
        return 0
    except FileError as exc:
        print(f"File Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        log.exception("Unexpected error during portfolio command")
        print(f"System error: {exc}", file=sys.stderr)
        return 1


def cmd_analytics() -> int:
    """
    Execute the analytics command (TR-241).
    Prints a simple dict for now (presentation via CLI).
    """
    try:
        result = compute_pl()
        print(result)
        return 0
    except Exception as exc:
        log.exception("Unexpected error during analytics command")
        print(f"System error: {exc}", file=sys.stderr)
        return 1


def cmd_save() -> int:
    """Execute the save command (TR-235)."""
    try:
        portfolio = load_portfolio()
        # In a real CLI loop, the portfolio object would be in memory. 
        # Here we just prove we can save the current state to the default path.
        save_portfolio(portfolio)
        print(f"Saved portfolio to {PORTFOLIO_FILE}")
        return 0
    except FileError as e:
        print(f"Error saving: {e}", file=sys.stderr)
        return 1
    except Exception as exc:
        log.exception("Unexpected error during save")
        print(f"System Error: {exc}", file=sys.stderr)
        return 1

def cmd_load() -> int:
    """Execute the load command (TR-235)."""
    try:
        # force reload from disk
        portfolio = load_portfolio() 
        print(f"Loaded portfolio from {PORTFOLIO_FILE}")
        print(f"Cash: {portfolio.cash:.2f} SEK")
        print(f"Holdings: {len(portfolio.holdings)} assets")
        return 0
    except Exception as exc:
        log.exception("Unexpected error during load")
        print(f"System Error: {exc}", file=sys.stderr)
        return 1

def main(argv: list[str] | None = None) -> int:
    """
    CLI entrypoint.
    """
    args = build_parser().parse_args(argv)

    init_logging(level=args.log_level)
    log.info("CLI start command=%s", args.command)

    try:
        if args.command == "quote":
            return cmd_quote(args.ticker)
        
        elif args.command == "sell":
            return cmd_sell(args.ticker, args.quantity)
        
        elif args.command == "buy":
            return cmd_buy(args.ticker, args.quantity)

        elif args.command == "portfolio":
            return cmd_portfolio()
        
        elif args.command == "analytics":
            return cmd_analytics()
            
        elif args.command == "save":
            return cmd_save()
            
        elif args.command == "load":
            return cmd_load()
        
        print("Error: Unknown command.", file=sys.stderr)
        return 0
    finally:
        log.info("CLI exit")


def run_cli(argv: list[str]) -> int:
    """
    Backward-compatible alias for older dev CLI entrypoint.
    """
    return main(argv)

if __name__ == "__main__":
    sys.exit(main())