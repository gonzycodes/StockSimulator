# src/cli.py

"""
Command-line interface for the Stock Simulator project.
"""

from __future__ import annotations

import argparse
import logging
import sys

from src.data_fetcher import QuoteFetchError, fetch_latest_quote

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """
    Create the root argument parser.
    """
    parser = argparse.ArgumentParser(prog="stock-sim", add_help=True)
    
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
        
        # Simple output (no advanced formatting required)
        print (f"{quote.ticker} {quote.price} {quote.timestamp.isoformat()}")
        return 0
    
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 0    # "program continues" => no crash/traceback
    except QuoteFetchError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 0
    except Exception as exc:
        logger.exception("Unexpected CLI error")
        print(f"Error: Unexpected error: {exc}", file=sys.stderr)
        return 0
    
    
def main(argv: list[str] | None = None) -> int:
    """
    CLI entrypoint.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    
    if args.command == "quote":
        return cmd_quote(args.ticker)
    
    print("Error: Unknown command.", file=sys.stderr)
    return 0

