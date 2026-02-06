# src/reporting.py

"""
File helper: Daily trade report generation (text).

Builds a deterministic, testable report based on:
- transaction history (data/transactions.json)
- current portfolio state (cash + holdings)
- current prices (via injected price_provider)

Designed for CLI usage (command "report") and unit tests.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from src.config import DATA_DIR, TRANSACTIONS_FILE
from src.errors import FileError
from src.portfolio import Portfolio

try:
    from src.logger import get_logger  # type: ignore
except Exception:  # pragma: no cover
    get_logger = None  # type: ignore

try:
    from src.data_fetcher import fetch_latest_quote  # default provider
except Exception:  # pragma: no cover
    fetch_latest_quote = None  # type: ignore

# Prefer using TR-241 analytics if present (single source of truth for P/L).
try:
    from src.analytics import compute_pl, load_transactions_df  # type: ignore
except Exception:  # pragma: no cover
    compute_pl = None  # type: ignore
    load_transactions_df = None  # type: ignore


log = (get_logger(__name__) if callable(get_logger) else logging.getLogger(__name__))

Clock = Callable[[], datetime]
PriceProvider = Callable[[str], float]


@dataclass(frozen=True)
class TradeLine:
    """Minimal representation for rendering recent trades."""
    timestamp: str
    side: str
    ticker: str
    quantity: float
    price: float
    total: float
    cash_after: float


@dataclass(frozen=True)
class ReportData:
    """All values needed to render a report."""
    generated_at: str
    period_label: str
    period_start: str | None
    period_end: str | None

    trades_count: int
    realized_pl: float
    unrealized_pl: float
    total_pl: float

    cash: float
    holdings: dict[str, float]
    prices: dict[str, float]
    holdings_value: float
    total_value: float

    recent_trades: list[TradeLine]
    notes: list[str]


def _default_clock() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


def _default_price_provider(ticker: str) -> float:
    """Fetch a latest price using src.data_fetcher (best effort)."""
    if fetch_latest_quote is None:  # pragma: no cover
        raise RuntimeError("Default price provider is unavailable (data_fetcher import failed).")
    quote = fetch_latest_quote(ticker)
    return float(quote.price)


def _parse_iso_ts(value: str) -> datetime | None:
    """Parse ISO timestamps, accepting Z suffix."""
    if not value or not isinstance(value, str):
        return None
    try:
        v = value.strip()
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        dt = datetime.fromisoformat(v)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _read_transaction_records(path: Path) -> list[dict[str, Any]]:
    """Load transaction history records from JSON (safe)."""
    if not path.exists():
        return []
    if not path.is_file():
        log.error("Transaction history path is not a file: %s", path)
        return []

    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, list):
            log.error("transactions.json must be a list, got: %s", type(data).__name__)
            return []
        return [r for r in data if isinstance(r, dict)]
    except json.JSONDecodeError:
        log.error("transactions.json is invalid JSON: %s", path, exc_info=True)
        return []
    except OSError:
        log.error("Failed reading transaction history: %s", path, exc_info=True)
        return []


def _to_trade_line(record: Mapping[str, Any]) -> TradeLine | None:
    """Convert a raw record to a TradeLine (or None if invalid)."""
    try:
        ts = str(record.get("timestamp", "")).strip()
        side = str(record.get("side", "")).strip().upper()
        ticker = str(record.get("ticker", "")).strip().upper()
        qty = float(record.get("quantity", 0.0))
        price = float(record.get("price", 0.0))
        total = float(record.get("total", qty * price))
        cash_after = float(record.get("cash_after", 0.0))

        if not ticker or side not in {"BUY", "SELL"} or qty <= 0:
            return None

        return TradeLine(
            timestamp=ts,
            side=side,
            ticker=ticker,
            quantity=qty,
            price=price,
            total=total,
            cash_after=cash_after,
        )
    except Exception:
        return None


def _extract_period_from_trade_lines(trades: list[TradeLine]) -> tuple[str | None, str | None]:
    """Get (start,end) ISO timestamps from trade timestamps (best effort)."""
    dts = [_parse_iso_ts(t.timestamp) for t in trades]
    dts = [d for d in dts if d is not None]
    if not dts:
        return None, None
    start = min(dts).isoformat().replace("+00:00", "Z")
    end = max(dts).isoformat().replace("+00:00", "Z")
    return start, end


def build_report_data(
    *,
    portfolio: Portfolio,
    transactions_path: Path | None = None,
    price_provider: PriceProvider | None = None,
    clock: Clock | None = None,
    recent_n: int = 5,
    period_label: str = "Latest activity (from transaction history)",
) -> ReportData:
    """
    Build a ReportData object for rendering.

    Uses transaction history for trade stats + P/L,
    and portfolio state for end-of-report cash/holdings.
    """
    tx_path = transactions_path or TRANSACTIONS_FILE
    now = (clock or _default_clock)().astimezone(timezone.utc)
    generated_at = now.isoformat().replace("+00:00", "Z")

    provider = price_provider or _default_price_provider

    # End-state truth for holdings + valuation.
    holdings = {k.upper(): float(v) for k, v in (portfolio.holdings or {}).items()}
    cash = float(portfolio.cash)

    notes: list[str] = []
    prices: dict[str, float] = {}

    for ticker in holdings.keys():
        try:
            prices[ticker] = float(provider(ticker))
        except Exception:
            prices[ticker] = 0.0
            notes.append(f"Price unavailable for {ticker}; valued as 0.00.")

    holdings_value = sum(qty * prices.get(t, 0.0) for t, qty in holdings.items())
    total_value = cash + holdings_value

    # Trade history: we keep JSON parsing (no pandas required for report basics).
    records = _read_transaction_records(tx_path)
    trade_lines = [tl for tl in (_to_trade_line(r) for r in records) if tl is not None]

    trades_count = len(trade_lines)
    period_start, period_end = _extract_period_from_trade_lines(trade_lines)
    recent_trades = list(reversed(trade_lines[-recent_n:])) if recent_n > 0 else []

    # P/L: prefer TR-241 analytics (single source of truth) when available.
    realized_pl = 0.0
    unrealized_pl = 0.0
    total_pl = 0.0

    if callable(compute_pl) and callable(load_transactions_df):
        try:
            df = load_transactions_df(tx_path)  # analytics handles missing/invalid safely
            pl = compute_pl(df=df, latest_prices=prices)
            realized_pl = float(pl.get("realized_pl", 0.0))
            unrealized_pl = float(pl.get("unrealized_pl", 0.0))
            total_pl = float(pl.get("total_pl", realized_pl + unrealized_pl))
        except Exception:
            log.warning("Analytics compute_pl failed; defaulting P/L to 0.", exc_info=True)
            notes.append("P/L unavailable (analytics failed); showing 0.00.")
            realized_pl = unrealized_pl = total_pl = 0.0
    else:
        notes.append("P/L unavailable (analytics not installed); showing 0.00.")

    return ReportData(
        generated_at=generated_at,
        period_label=period_label,
        period_start=period_start,
        period_end=period_end,
        trades_count=trades_count,
        realized_pl=realized_pl,
        unrealized_pl=unrealized_pl,
        total_pl=total_pl,
        cash=cash,
        holdings=holdings,
        prices=prices,
        holdings_value=holdings_value,
        total_value=total_value,
        recent_trades=recent_trades,
        notes=notes,
    )


def render_report(data: ReportData) -> str:
    """Render ReportData to a human-readable text report."""
    lines: list[str] = []

    lines.append("StockSimulator - Trade Report")
    lines.append(f"Generated: {data.generated_at}")
    lines.append(f"Period: {data.period_label}")
    if data.period_start and data.period_end:
        lines.append(f"Range: {data.period_start} — {data.period_end}")
    else:
        lines.append("Range: (no transactions found)")
    lines.append("")

    lines.append("Summary")
    lines.append(f"Trades: {data.trades_count}")
    lines.append(f"Realized P/L: {data.realized_pl:,.2f}")
    lines.append(f"Unrealized P/L: {data.unrealized_pl:,.2f}")
    lines.append(f"Total P/L: {data.total_pl:,.2f}")
    lines.append("")

    lines.append("Portfolio")
    lines.append(f"Cash: {data.cash:,.2f}")
    if not data.holdings:
        lines.append("Holdings: (none)")
    else:
        lines.append("Holdings:")
        for ticker in sorted(data.holdings.keys()):
            qty = data.holdings[ticker]
            px = data.prices.get(ticker, 0.0)
            value = qty * px
            lines.append(f"- {ticker}: {qty:g} @ {px:,.2f} = {value:,.2f}")
    lines.append(f"Holdings value: {data.holdings_value:,.2f}")
    lines.append(f"Total value: {data.total_value:,.2f}")
    lines.append("")

    if data.recent_trades:
        lines.append(f"Recent trades (last {len(data.recent_trades)})")
        for t in data.recent_trades:
            lines.append(
                f"- {t.timestamp} | {t.side:<4} {t.ticker:<6} "
                f"qty={t.quantity:g} price={t.price:,.2f} total={t.total:,.2f} cash_after={t.cash_after:,.2f}"
            )
        lines.append("")

    if data.notes:
        lines.append("Notes")
        for n in data.notes:
            lines.append(f"- {n}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_report_text(
    *,
    text: str,
    out_dir: Path | None = None,
    clock: Clock | None = None,
    filename_prefix: str = "report",
) -> Path:
    """
    Write report text to data/ as a dated file.

    Raises:
        FileError on write failure.
    """
    target_dir = out_dir or DATA_DIR
    now = (clock or _default_clock)().astimezone(timezone.utc)
    date_str = now.date().isoformat()
    out_path = target_dir / f"{filename_prefix}_{date_str}.txt"

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        return out_path
    except OSError as exc:
        log.error("Failed to write report file: %s", out_path, exc_info=True)
        raise FileError(f"Could not write report to '{out_path}': {exc}") from exc


def generate_and_write_report(
    *,
    portfolio: Portfolio,
    transactions_path: Path | None = None,
    price_provider: PriceProvider | None = None,
    clock: Clock | None = None,
    recent_n: int = 5,
) -> Path:
    """High-level helper: build -> render -> write."""
    data = build_report_data(
        portfolio=portfolio,
        transactions_path=transactions_path,
        price_provider=price_provider,
        clock=clock,
        recent_n=recent_n,
    )
    text = render_report(data)
    return write_report_text(text=text, clock=clock)

