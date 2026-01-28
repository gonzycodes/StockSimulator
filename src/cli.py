# src/cli.py

"""
Command-line interface (CLI) layer for StockSimulator.
"""

from __future__ import annotations

import argparse
import sys

from src.data_fetcher import QuoteFetchError, fetch_latest_quote


try:
    # Preferred (dev) logging layer
    from src.logger import init_logging, get_logger  # type: ignore

    log = get_logger(__name__)
except Exception:  # pragma: no cover
    # Fallback if src.logger is not available yet
    import logging

    def init_logging(level: str = "INFO") -> None:
        """Initialize basic logging."""
        logging.basicConfig(level=level)

    def get_logger(name: str):
        """Get a logger instance."""
        return logging.getLogger(name)

    log = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """
    Create and return the CLI argument parser.
    """
    parser = argparse.ArgumentParser(prog="stock-sim")
    parser.add_argument("--log-level", default="INFO", help="DEBUG|INFO|WARNING|ERROR|CRITICAL")

    sub = parser.add_subparsers(dest="command", required=True)

    q = sub.add_parser("quote", help="Fetch the latest price for a ticker.")
    q.add_argument("ticker", help="Ticker symbol, e.g. AAPL")

    return parser


def validate_ticker(raw: str) -> str:
    """
    Normalize and validate a ticker string.
    """
    ticker = (raw or "").strip().upper()
    if not ticker:
        raise ValueError("Ticker must not be empty.")
    return ticker


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

    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 0
    except QuoteFetchError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 0
    except Exception as exc:
        log.exception("Unexpected CLI error")
        print(f"Error: Unexpected error: {exc}", file=sys.stderr)
        return 0


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

        print("Error: Unknown command.", file=sys.stderr)
        return 0
    finally:
        log.info("CLI exit")


def run_cli(argv: list[str]) -> int:
    """
    Backward-compatible alias for older dev CLI entrypoint.
    """
    return main(argv)

