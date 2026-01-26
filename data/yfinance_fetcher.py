import yfinance as yf
from datetime import datetime
import logging


def _extract_price_and_time(info: dict) -> tuple[float, str]:
    """
    Pure logic function: Parses the yfinance .info dictionary and extracts
    the latest price and formatted timestamp.

    This function contains NO network I/O it only processes already fetched data.
    Makes the code unit-testable without mocking external libraries.

    Args:
        info: The dictionary returned by yf.Ticker(ticker).info

    Returns:
        tuple[float, str]: (price as float, timestamp as ISO-like string "YYYY-MM-DD HH:MM:SS")

    Raises:
        ValueError: If price or timestamp is missing or in invalid format
    """
    # Try to get the most up-to-date price field first, fallback to regular market price
    price = info.get("currentPrice") or info.get("regularMarketPrice")

    # Unix timestamp (seconds since 1970-01-01) when the price was last updated
    ts_unix = info.get("regularMarketTime")

    # Basic validation – fail fast with clear error messages
    if price is None:
        raise ValueError("No price found in yfinance response (missing 'currentPrice' and 'regularMarketPrice')")
    
    if ts_unix is None:
        raise ValueError("No timestamp found in yfinance response (missing 'regularMarketTime')")

    try:
        # Convert Unix timestamp → human-readable string in local time
        # Format: 2025-12-31 23:59:59
        ts_str = datetime.fromtimestamp(ts_unix).strftime("%Y-%m-%d %H:%M:%S")
        return float(price), ts_str
    except (TypeError, ValueError) as e:
        # Protect against corrupt or unexpected timestamp values
        raise ValueError(f"Invalid timestamp format in yfinance data: {e}")


def get_latest_price(ticker: str) -> tuple[float, str]:
    """
    Fetches the latest price and timestamp for a given stock ticker using yfinance.

    This is the public API function that performs the actual network request.
    All business logic / parsing is delegated to _extract_price_and_time().

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL", "ERIC-B.ST", "TSLA")

    Returns:
        tuple[float, str]: (current price, formatted timestamp string)

    Raises:
        ValueError: If ticker is invalid
        Exception: If network request fails or yfinance returns unexpected data
                   (original exception is logged and re-raised)
    """
    # Input validation – prevent useless network calls
    if not ticker or not isinstance(ticker, str):
        raise ValueError("Ticker must be a non-empty string")

    try:
        # Create yfinance Ticker object and fetch latest market data
        stock = yf.Ticker(ticker)
        
        # This is the actual network I/O call – fetches all available info
        info = stock.info

        # Delegate parsing to the pure function (easy to test separately)
        return _extract_price_and_time(info)

    except Exception as e:
        # Log the error with context so we can debug later
        logging.error(f"Failed to fetch price for ticker '{ticker}': {e}")
        # Re-raise so caller can decide how to handle the failure
        raise


# Example usage / quick test when running the file directly
if __name__ == "__main__":
    try:
        price, timestamp = get_latest_price("AAPL")
        print(f"AAPL latest price: {price:.2f} at {timestamp}")
    except Exception as e:
        print(f"Error: {e}")