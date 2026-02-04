# src/main.py

"""
Application entry point for TradeSim.

Implements a safe interactive simulation loop:
- Expected errors (validation, file, API) are shown as friendly messages.
- Unexpected errors are logged with stacktrace and the loop continues.
"""

from __future__ import annotations

import sys
import shlex
from dataclasses import dataclass
from typing import Callable

from src.logger import init_logging_from_env, get_logger
from src.errors import ValidationError, FileError
from src.data_fetcher import fetch_latest_quote, QuoteFetchError, FetchErrorCode
from src.portfolio import Portfolio
from src.cli import load_portfolio, save_portfolio, validate_ticker
from src.snapshot_store import SnapshotStore
from src.transactions import TransactionManager, TransactionError


log = get_logger(__name__)

SIM_COMMANDS: list[tuple[str, str]] = [
    ("quote <TICKER>", "Show latest price for a ticker"),
    ("buy <TICKER> <QTY>", "Buy shares into your portfolio"),
    ("sell <TICKER> <QTY>", "Sell shares from your portfolio"),
    ("portfolio", "Show cash and holdings"),
    ("help | ?", "Show available commands"),
    ("exit | quit", "Return to the main menu"),
]


def print_sim_help() -> None:
    """Print available simulation commands."""
    print("\n--- Commands ---")
    for usage, desc in SIM_COMMANDS:
        print(f"{usage:<22} {desc}")
    print("----------------\n")


def print_menu_help() -> None:
    """Print the main menu help text."""
    print("\n--- Help Menu ---")
    print("1. In the Main Menu, choose 'Start' to enter the simulation.")
    print("2. Inside the simulation, use commands like: quote, sell, portfolio.")
    print("3. Type 'exit' or 'quit' to return to the menu.")
    print("---------------------")
    input("\nPress Enter to return to the main menu...")


@dataclass
class SimDeps:
    """Dependencies for the simulation dispatch (helps unit testing)."""

    fetch_quote: Callable = fetch_latest_quote
    load_pf: Callable = load_portfolio
    save_pf: Callable = save_portfolio


@dataclass
class SimState:
    """Runtime state for the simulation loop."""

    portfolio: Portfolio


def _print_quote(ticker: str, quote) -> None:
    """Print a quote in a user-friendly format."""
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
        fx_part = f" (FX: {fx_pair} {float(fx_rate):.4f})" if fx_pair and fx_rate else ""
        print(f"{ticker}{name_part} {price_native} {currency} | {price_sek} SEK (Fetched at: {ts_str}){fx_part}")
    else:
        print(f"{ticker}{name_part} {price_native} {currency} | SEK: N/A (Fetched at: {ts_str})")


def dispatch_line(line: str, state: SimState, deps: SimDeps) -> bool:
    """
    Dispatch a single simulation command.

    Returns:
        True to continue, False to exit simulation to main menu.

    Raises:
        ValidationError: invalid user input.
        FileError: portfolio load/save failed.
        QuoteFetchError: market data fetch failed.
        Exception: unexpected errors.
    """
    def _deps_price_provider(deps: SimDeps):
        def _get_price(ticker: str) -> float:
            quote = deps.fetch_quote(ticker)
            return float(quote.price)
        return _get_price
    
    tokens = shlex.split(line)
    if not tokens:
        return True

    cmd = tokens[0].lower()

    if cmd in {"exit", "quit"}:
        return False

    if cmd in {"help", "?"}:
        print_sim_help()
        return True

    if cmd == "portfolio":
        pf = state.portfolio
        print("\n--- Portfolio ---")
        print(f"Cash: {pf.cash:.2f}")
        if not pf.holdings:
            print("Holdings: (empty)")
        else:
            print("Holdings:")
            for t, qty in pf.holdings.items():
                print(f"  {t}: {qty}")
        print("-----------------\n")
        return True

    if cmd == "quote":
        if len(tokens) != 2:
            raise ValidationError("Usage: quote <TICKER>")
        ticker = validate_ticker(tokens[1])
        quote = deps.fetch_quote(ticker)
        _print_quote(ticker, quote)
        return True
    
    if cmd == "buy":
        if len(tokens) != 3:
            raise ValidationError("Usage: buy <TICKER> <QTY>")
        ticker = validate_ticker(tokens[1])

        try:
            qty = float(tokens[2])
        except ValueError as exc:
            raise ValidationError("Quantity must be a number.") from exc

        if qty <= 0:
            raise ValidationError("Quantity must be greater than 0.")

        tm_local = TransactionManager(
            portfolio=state.portfolio,
            price_provider=_deps_price_provider(deps),
            snapshot_store=SnapshotStore(),
            logger=log,
        )
        tx = tm_local.buy(ticker, qty)
        deps.save_pf(state.portfolio)

        print(f"SUCCESS: Bought {tx.quantity} shares of {tx.ticker} at {tx.price:.2f}.")
        print(f"Cost: {tx.gross_amount:.2f}. New Cash Balance: {state.portfolio.cash:.2f}")
        return True

    if cmd == "sell":
        if len(tokens) != 3:
            raise ValidationError("Usage: sell <TICKER> <QTY>")
        ticker = validate_ticker(tokens[1])

        try:
            qty = float(tokens[2])
        except ValueError as exc:
            raise ValidationError("Quantity must be a number.") from exc

        if qty <= 0:
            raise ValidationError("Quantity must be greater than 0.")

        tm_local = TransactionManager(
            portfolio=state.portfolio,
            price_provider=_deps_price_provider(deps),
            snapshot_store=SnapshotStore(),
            logger=log,
        )
        tx = tm_local.sell(ticker, qty)
        deps.save_pf(state.portfolio)

        print(f"SUCCESS: Sold {tx.quantity} shares of {tx.ticker} at {tx.price:.2f}.")
        print(f"Proceeds: {tx.gross_amount:.2f}. New Cash Balance: {state.portfolio.cash:.2f}")
        return True

    print(f"Unknown command: '{cmd}'. Type 'help' for a list of commands.")
    return True


def safe_dispatch(line: str, state: SimState, deps: SimDeps) -> bool:
    """
    Safe wrapper around dispatch_line().

    Expected errors show friendly messages; unexpected errors are logged and
    the loop continues.
    """
    try:
        return dispatch_line(line, state, deps)

    except ValidationError as exc:
        print(f"Input error: {exc}")
        return True

    except FileError as exc:
        print(f"File error: {exc}")
        return True

    except QuoteFetchError as exc:
        code = getattr(exc, "code", FetchErrorCode.UNKNOWN)
        if code == FetchErrorCode.NOT_FOUND:
            print(f"Market error: Ticker not found or no price data. ({exc})")
        elif code == FetchErrorCode.NETWORK:
            print(f"Market error: Network issue while fetching data. ({exc})")
        else:
            print(f"Market error: {exc}")
        return True
    
    except TransactionError as exc:
        print(f"Transaction error: {exc}")
        return True

    except Exception:
        log.exception("Unexpected error in simulation loop")
        print("Unexpected error occurred.")
        return True


def run_simulation() -> None:
    """
    Active simulation loop.

    The loop is safe: expected errors do not crash the program, and unexpected
    errors are logged with stacktrace while the loop continues.
    """
    print("\n--- Stock Simulator ---")
    print("Type 'help' or '?' for commands. Type 'exit' or 'quit' to return to the main menu.\n")

    deps = SimDeps()

    try:
        portfolio = deps.load_pf()
    except FileError as exc:
        log.warning("Portfolio load failed, starting fresh: %s", exc, exc_info=True)
        print("Warning: Could not load portfolio. Starting with a new portfolio.")
        portfolio = Portfolio()

    state = SimState(portfolio=portfolio)

    while True:
        try:
            line = input("TradeSim (Active) > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nReturning to main menu.")
            return

        if line == "":
            continue

        keep_running = safe_dispatch(line, state, deps)
        if not keep_running:
            print("Saving data... Returning to main menu.")
            try:
                deps.save_pf(state.portfolio)
            except FileError as exc:
                log.warning("Portfolio save failed on exit: %s", exc, exc_info=True)
                print("Warning: Could not save portfolio on exit.")
            return


def main_menu() -> None:
    """Show the main menu and route user actions."""
    while True:
        print("\n===============================")
        print("   Welcome to TradeSim         ")
        print("===============================")
        print("1. Start Simulation")
        print("2. Help")
        print("3. Exit")
        print("===============================")

        choice = input("Please select an option (1-3): ").strip()

        if choice == "1":
            log.info("User started simulation")
            run_simulation()
        elif choice == "2":
            print_menu_help()
        elif choice == "3":
            print("Exiting TradeSim. Goodbye!")
            return
        else:
            print("Invalid choice. Please select 1, 2, or 3.")


def main() -> int:
    """
    Run the application and return an exit code.

    Returns:
        0 on normal exit, 1 on unhandled errors.
    """
    init_logging_from_env()
    log.info("App start")

    try:
        if len(sys.argv) > 1:
            from src.cli import main as cli_main
            return int(cli_main(sys.argv[1:]))

        main_menu()
        return 0

    except Exception:
        log.exception("Unhandled exception")
        return 1

    finally:
        log.info("App exit")


if __name__ == "__main__":
    raise SystemExit(main())
