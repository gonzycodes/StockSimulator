# src/data_fetcher.py

"""
Helpers for fetching market data (quotes, candles, etc.).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional
import yfinance as yf

from src.config import MOCK_PRICES_FILE, USE_MOCK_DATA


logger = logging.getLogger(__name__)


def get_market_state(ticker: str) -> str:
    """
    Fetch the current market state from yfinance.
    Returns 'REGULAR', 'CLOSED', 'PRE', 'POST', 'PREPRE', etc.
    Returns 'UNKNOWN' if fetch fails.
    """
    try:
        yf_ticker = yf.Ticker(ticker)
        info = yf_ticker.info
        state = info.get('marketState', 'UNKNOWN')
        return state
    except Exception:
        logger.warning("Could not fetch marketState for %s", ticker, exc_info=True)
        return 'UNKNOWN'

def is_market_likely_open(ticker: str) -> bool:
    """
    Returns True if marketState indicates regular trading hours.
    """
    state =get_market_state(ticker)
    return state == 'REGULAR' 
class FetchErrorCode(str, Enum):
    VALIDATION = "VALIDATION"
    NOT_FOUND = "NOT_FOUND"
    NETWORK = "NETWORK"
    UNKNOWN = "UNKNOWN"

class QuoteFetchError(RuntimeError):
    """
    Raised when a quote cannot be fetched or parsed.
    """

    def __init__(self, message: str, code: FetchErrorCode = FetchErrorCode.UNKNOWN):
        super().__init__(message)
        self.code = code

def _validate_ticker(ticker: str) -> str:
        if not ticker or not ticker.strip():
            raise QuoteFetchError(
                "Ticker must not be empty",
                code=FetchErrorCode.VALIDATION,
            )
        return ticker.strip().upper()

@dataclass(frozen=True)
class Quote:
    """
    A minimal latest-quote representation.
    """
    ticker: str
    price: float
    currency: str
    timestamp: datetime
    company_name: Optional[str] = None
    price_sek: Optional[float] = None
    fx_pair: Optional[str] = None
    fx_rate_to_sek: Optional[float] = None
    
    
def fetch_latest_quote(ticker: str) -> Quote:
    """
    Fetch the latest price for a ticker using yfinance.
    """
    ticker = _validate_ticker(ticker)

    if not is_market_likely_open(ticker):
        print("Warning: Market appears to be closed for this ticker - showing last known price")
        logger.info("Market likely closed for ticker: %s (marketState: %s)",
                    ticker, get_market_state(ticker))

    try:
        yf_ticker = yf.Ticker(ticker)
        
        price = _try_fast_info_price(yf_ticker)
        if price is None:
            price = _try_history_price(yf_ticker)

        if price is None:
            raise QuoteFetchError(
                f"Ticker '{ticker}' not found or has no price data.",
                code=FetchErrorCode.NOT_FOUND,
            )

        
        company_name = _try_company_name(yf_ticker)
        currency = _try_currency(yf_ticker) or "UNKNOWN"
        
        ts = datetime.now(timezone.utc)
        
        # Best-effort SEK conversion
        price_sek, fx_pair, fx_rate = _try_convert_to_sek(price=float(price), currency=currency)
        

        return Quote(
            ticker=ticker,
            price=float(price),
            currency=currency,
            timestamp=ts,
            company_name=company_name,
            price_sek=price_sek,
            fx_pair=fx_pair,
            fx_rate_to_sek=fx_rate,
        )
    
    except QuoteFetchError as exc:
        raise

    except Exception as exc:
        logger.error(
            "Network or unexpected error while fetching ticker=%s",
            ticker,
            exc_info=True,
        )
    
        # Try fallback if we have mock enabled or want to use it in case of network errors
        logger.warning("Network error...falling back to mock for %s", ticker)
        try:
            return _quote_from_mock(ticker)
        except QuoteFetchError:
            # If mock cannot be used: throw correct network error
            raise QuoteFetchError(
                "Network error while fetching market data.",
                code=FetchErrorCode.NETWORK,
            ) from exc



    
    
def _try_currency(yf_ticker: yf.Ticker) -> Optional[str]:
    """
    Try to get the instrument currency (e.g. USD, SEK).
    """
    try:
        info = None
        if hasattr(yf_ticker, "get_info"):
            info = yf_ticker.get_info()
        else:
            info = getattr(yf_ticker, "info", None)

        if not isinstance(info, dict):
            return None

        ccy = info.get("currency")
        if isinstance(ccy, str):
            ccy = ccy.strip().upper()
            return ccy or None
        return None
    except Exception:
        return None
    
    
def _try_convert_to_sek(price: float, currency: str) -> tuple[Optional[float], Optional[str], Optional[float]]:
    """
    Convert a price in <currency> to SEK using Yahoo FX tickers (best effort).
    """
    ccy = (currency or "").strip().upper()
    if not ccy or ccy == "UNKNOWN":
        return None, None, None

    if ccy == "SEK":
        return float(price), "SEK", 1.0

    fx_pair = f"{ccy}SEK=X"  # e.g. USDSEK=X, EURSEK=X
    try:
        fx_ticker = yf.Ticker(fx_pair)

        fx_rate = _try_fast_info_price(fx_ticker)
        if fx_rate is None:
            fx_rate = _try_history_price(fx_ticker)

        if fx_rate is None:
            return None, fx_pair, None

        price_sek = float(price) * float(fx_rate)
        return price_sek, fx_pair, float(fx_rate)
    except Exception:
        return None, fx_pair, None
    
    
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


def _quote_from_mock(ticker: str) -> Quote:
    """
    Load a quote for the given ticker from the mock prices file.
    """
    ticker = _validate_ticker(ticker)
    
    try:
        with open(MOCK_PRICES_FILE, 'r') as f:
            mock_data = json.load(f)
        
        if ticker not in mock_data:
            raise QuoteFetchError(
                f"Ticker '{ticker}' not found in mock data.",
                code=FetchErrorCode.NOT_FOUND,
            )
        
        quote_data = mock_data[ticker]
        return Quote(
            ticker=ticker,
            price=float(quote_data['price']),
            currency=quote_data.get('currency', 'USD'),
            timestamp=datetime.now(timezone.utc),
            company_name=quote_data.get('company_name'),
            price_sek=quote_data.get('price_sek'),
            fx_pair=quote_data.get('fx_pair'),
            fx_rate_to_sek=quote_data.get('fx_rate_to_sek'),
        )
    except QuoteFetchError:
        raise
    except Exception as exc:
        raise QuoteFetchError(
            f"Could not load mock data for ticker '{ticker}'.",
            code=FetchErrorCode.UNKNOWN,
        ) from exc
    
    