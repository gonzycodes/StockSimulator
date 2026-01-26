# src/cli.py

"""
Command-line interface (CLI) layer for StockSimulator.

This module parses CLI arguments, configures logging (optionally overriding
the default), and logs central events such as quote requests.
"""

import argparse

from src.logger import init_logging, get_logger

log = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """
    Create and return the CLI argument parser.

    Returns:
        An argparse.ArgumentParser configured for the CLI.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-level", default="INFO", help="DEBUG|INFO|WARNING|ERROR|CRITICAL")
    parser.add_argument("symbol", help="Stock symbol, e.g. AAPL")
    return parser


def run_cli(argv: list[str]) -> int:
    """
    Execute the CLI workflow.

    Args:
        argv: List of arguments excluding the program name (sys.argv[1:]).

    Returns:
        0 on success, 1 on failure.
    """
    args = build_parser().parse_args(argv)
    
    init_logging(level=args.log_level)  # Override default if provided
    log.info("CLI start")
    log.info("Quote requested symbol=%s", args.symbol)
    
    try:
        # Example:
        # quote = quote_service.get_quote(args.symbol)
        # log.info("Quote received symbol=%s price=%s", args.symbol, quote.price)
        return 0
    except Exception:
        log.exception("Quote call failed symbol=%s", args.symbol)
        return 1
    finally:
        log.info("CLI exit")
        
        