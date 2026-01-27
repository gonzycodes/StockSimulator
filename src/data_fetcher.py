# src/data_fetcher.py

"""
Helpers for fetching market data (quotes, candles, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Optional

import yfinance as yf

logger = logging.getLogger(__name__)


class QuoteFetchError(RuntimeError):
    """
    Raised when a quote cannot be fetched or parsed.
    """
    
    
@dataclass(frozen=True)
class Quote:
    """
    A minimal latest-quote representation.
    """
    ticker: str
    price: float
    timestamp: datetime
    company_name: Optional[str] = None
    
    
def fetch_latest_quote(ticker: str) -> Quote:
    """
    Fetch the latest price for a ticker using yfinance.
    """
    try:
        yf_ticker = yf.Ticker(ticker)
        
        price = _try_fast_info_price(yf_ticker)
        if price is None:
            price = _try_history_price(yf_ticker)
            
        if price is None:
            raise QuoteFetchError("No price data returned (invalid ticker or no data).")
        
        company_name = _try_company_name(yf_ticker)
        ts = datetime.now(timezone.utc)
        return Quote(ticker=ticker, price=float(price), timestamp=ts, company_name=company_name)
    
    except QuoteFetchError:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch quote for %s", ticker)
        raise QuoteFetchError(f"Failed to fetch quote: {exc}") from exc
    
    
def _try_company_name(yf_ticker: yf.Ticker) -> Optional[str]:
    """
    Try to resolve a human-friendly company name for the ticker.
    """
    try:
        info = None

        # Some yfinance versions provide get_info(); otherwise .info is common.
        if hasattr(yf_ticker, "get_info"):
            info = yf_ticker.get_info()
        else:
            info = getattr(yf_ticker, "info", None)

        if not isinstance(info, dict):
            return None

        name = info.get("shortName") or info.get("longName") or info.get("displayName")
        if isinstance(name, str):
            name = name.strip()
            return name or None
        return None
    except Exception:
        return None
    

def _try_fast_info_price(yf_ticker: yf.Ticker) -> Optional[float]:
    """
    Try to read a last price from yfinance fast_info.
    """
    try:
        fast_info = getattr(yf_ticker, "fast_info", None)
        if not fast_info:
            return None
        price = fast_info.get("last_price")
        return float(price) if price is not None else None
    except Exception:
        return None
    

def _try_history_price(yf_ticker: yf.Ticker) -> Optional[float]:
    """
    Fallback: derive a price from recent history close values.
    """
    try:
        hist = yf_ticker.history(period="1d", interval="1m")
        if hist is not None and not hist.empty:
            closes = hist.get("Close")
            if closes is not None:
                closes = closes.dropna()
                if not closes.empty:
                    return float(closes.iloc[-1])
                
        hist = yf_ticker.history(period="5d", interval="1d")
        if hist is not None and not hist.empty:
            closes = hist.get("Close")
            if closes is not None:
                closes = closes.dropna()
                if not closes.empty:
                    return float(closes.iloc[-1])
                
        return None
    except Exception:
        return None
    
    