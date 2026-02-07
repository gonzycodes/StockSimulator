"""
Flask API server for STOCK SIMULATOR Chart Interface.

Provides REST endpoints for the chart trading interface to interact with
the existing STOCK SIMULATOR portfolio and market data functionality.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timezone, timedelta
import sys
import os
from pathlib import Path
import pandas as pd
import pytz

# Add src to path - handle both direct execution and module import
current_dir = Path(__file__).parent
if current_dir not in sys.path:
    sys.path.insert(0, str(current_dir))

# Now import from src
try:
    from src.portfolio import Portfolio
    from src.data_fetcher import fetch_latest_quote, QuoteFetchError
    from src.transaction_manager import (
        TransactionManager, 
        TransactionError,
        MarketClosedError,
        InsufficientFundsError,
        InsufficientHoldingsError
    )
    from src.snapshot_store import SnapshotStore
    from src.cli import load_portfolio, save_portfolio
    from src.logger import init_logging, get_logger
    from src.config import DATA_DIR
except ImportError as e:
    print(f"Error importing from src: {e}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    raise

app = Flask(__name__)
CORS(app)  # Enable CORS for local development

log = get_logger(__name__)


@app.route('/api/quote/<ticker>', methods=['GET'])
def get_quote(ticker):
    """
    Get latest quote for a ticker.
    
    Returns:
        {
            "ticker": "AAPL",
            "price": 150.25,
            "currency": "USD",
            "timestamp": "2024-...",
            "company_name": "Apple Inc.",
            "price_sek": 1650.75,
            "fx_pair": "USDSEK=X",
            "fx_rate": 11.005
        }
    """
    try:
        quote = fetch_latest_quote(ticker.upper())
        
        return jsonify({
            'ticker': quote.ticker,
            'price': float(quote.price),
            'currency': quote.currency,
            'timestamp': quote.timestamp.isoformat(),
            'company_name': quote.company_name,
            'price_sek': float(quote.price_sek) if quote.price_sek else None,
            'fx_pair': quote.fx_pair,
            'fx_rate': float(quote.fx_rate_to_sek) if quote.fx_rate_to_sek else None,
        })
    
    except QuoteFetchError as e:
        return jsonify({'error': str(e), 'code': e.code}), 400
    except Exception as e:
        log.exception("Error fetching quote")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/historical/<ticker>', methods=['GET'])
def get_historical(ticker):
    """Get historical price data for charting with Swedish timezone."""
    import yfinance as yf
    
    try:
        period = request.args.get('period', '5d')
        interval = request.args.get('interval', None)
        
        if not interval:
            interval_map = {'1h': '1m', '1d': '5m', '5d': '15m', '1mo': '1h', '3mo': '1d', '1y': '1d'}
            interval = interval_map.get(period, '1d')
        
        log.info(f"Fetching: {ticker} period={period} interval={interval}")
        
        # Fetch MAXIMUM data for smooth charts
        fetch_map = {'1h': '7d', '1d': '7d', '5d': '60d', '1mo': '730d', '3mo': '3mo', '1y': '1y'}
        fetch_period = fetch_map.get(period, period)
        
        yf_ticker = yf.Ticker(ticker.upper())
        hist = yf_ticker.history(period=fetch_period, interval=interval)
        
        if hist.empty:
            return jsonify({'error': f'No data for {ticker}'}), 404
        
        # Filter to display period - show MORE data
        if fetch_period != period:
            tail_map = {
                ('1h', '1m'): 2880,  # 2 days worth of 1m candles (48 hours)
                ('1d', '5m'): 576,   # 2 days of 5m candles  
                ('5d', '15m'): 960,  # 10 days of 15m candles
                ('1mo', '1h'): 1440  # 60 days of 1h candles
            }
            tail_count = tail_map.get((period, interval))
            if tail_count:
                hist = hist.tail(tail_count)
        
        # Convert to Swedish timezone
        swedish_tz = pytz.timezone('Europe/Stockholm')
        data = []
        
        for index, row in hist.iterrows():
            try:
                if pd.isna(row['Close']) or pd.isna(row['Open']) or row['Close'] == 0:
                    continue
                
                # Convert to Swedish time
                if index.tz is None: # type: ignore
                    utc_time = index.tz_localize('UTC') # type: ignore
                else:
                    utc_time = index.tz_convert('UTC') # type: ignore
                swedish_time = utc_time.tz_convert(swedish_tz)
                    
                data.append({
                    'time': int(swedish_time.timestamp()),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume']) if 'Volume' in row and not pd.isna(row['Volume']) else 0,
                })
            except Exception as e:
                continue
        
        if not data:
            return jsonify({'error': 'No valid data'}), 404
        
        log.info(f"Returning {len(data)} candles for {ticker}")
        return jsonify({'ticker': ticker.upper(), 'period': period, 'interval': interval, 'data': data})
    
    except Exception as e:
        log.exception("Error fetching historical")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """
    Get current portfolio status.
    
    Returns:
        {
            "cash": 10000.00,
            "holdings": {
                "AAPL": 10.5,
                "MSFT": 5.0
            },
            "total_value": 12500.00
        }
    """
    try:
        portfolio = load_portfolio()
        
        # Calculate total value (simplified - uses current market prices)
        total_value = portfolio.cash
        holdings_with_prices = {}
        
        for ticker, qty in portfolio.holdings.items():
            try:
                quote = fetch_latest_quote(ticker)
                price = float(quote.price)
                total_value += qty * price
                holdings_with_prices[ticker] = {
                    'quantity': qty,
                    'current_price': price,
                    'value': qty * price,
                }
            except QuoteFetchError:
                holdings_with_prices[ticker] = {
                    'quantity': qty,
                    'current_price': None,
                    'value': 0,
                }
        
        return jsonify({
            'cash': portfolio.cash,
            'holdings': portfolio.holdings,
            'holdings_detailed': holdings_with_prices,
            'total_value': total_value,
        })
    
    except Exception as e:
        log.exception("Error getting portfolio")
        return jsonify({'error': str(e)}), 500


@app.route('/api/trade', methods=['POST'])
def execute_trade():
    """
    Execute a buy or sell trade.
    
    Request body:
        {
            "action": "buy" | "sell",
            "ticker": "AAPL",
            "quantity": 10.5,
            "order_type": "market" | "limit",
            "limit_price": 150.00  // optional, for limit orders
        }
    
    Returns:
        {
            "success": true,
            "transaction": {...},
            "portfolio": {...}
        }
    """
    try:
        data = request.get_json()
        
        action = data.get('action')
        ticker = data.get('ticker', '').upper()
        quantity = float(data.get('quantity', 0))
        order_type = data.get('order_type', 'market')
        limit_price = data.get('limit_price')
        
        if action not in ['buy', 'sell']:
            return jsonify({'error': 'Invalid action'}), 400
        
        if not ticker or quantity <= 0:
            return jsonify({'error': 'Invalid ticker or quantity'}), 400
        
        # Get current market price
        quote = fetch_latest_quote(ticker)
        price = float(quote.price)
        
        # Use limit price if specified
        if order_type == 'limit' and limit_price:
            price = float(limit_price)
        
        # Load portfolio and execute trade
        portfolio = load_portfolio()
        
        # Create TransactionManager instance for this trade
        tm = TransactionManager(portfolio=portfolio, snapshot_store=SnapshotStore())
        
        if action == 'buy':
            tx = tm.buy(ticker, quantity)
        else:
            tx = tm.sell(ticker, quantity)
        
        # Save portfolio
        save_portfolio(portfolio)
        
        # Calculate total from transaction
        total = quantity * price
        
        return jsonify({
            'success': True,
            'transaction': {
                'action': action,
                'ticker': ticker,
                'quantity': quantity,
                'price': price,
                'total': total,
                'cash_after': portfolio.cash,
                'timestamp': datetime.now(timezone.utc).isoformat(),
            },
            'portfolio': {
                'cash': portfolio.cash,
                'holdings': portfolio.holdings,
            }
        })
    
    except MarketClosedError as e:
        log.warning("Market closed error: %s", str(e))
        return jsonify({'error': f'Market is closed: {str(e)}'}), 400
    except InsufficientFundsError as e:
        log.warning("Insufficient funds: %s", str(e))
        return jsonify({'error': f'Insufficient funds: {str(e)}'}), 400
    except InsufficientHoldingsError as e:
        log.warning("Insufficient holdings: %s", str(e))
        return jsonify({'error': f'Insufficient holdings: {str(e)}'}), 400
    except TransactionError as e:
        log.error("Transaction error: %s", str(e))
        return jsonify({'error': str(e)}), 400
    except QuoteFetchError as e:
        log.error("Quote fetch error: %s", str(e))
        return jsonify({'error': f'Market data error: {e}'}), 400
    except Exception as e:
        log.exception("Error executing trade")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/markets', methods=['GET'])
def get_markets():
    """
    Get list of available markets/symbols.
    
    Returns:
        {
            "stocks": ["AAPL", "MSFT", ...],
            "crypto": ["BTC-USD", "ETH-USD", ...],
            "forex": ["EURUSD=X", ...]
        }
    """
    return jsonify({
        'stocks': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX'],
        'crypto': ['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD', 'DOGE-USD'],
        'forex': ['EURUSD=X', 'GBPUSD=X', 'USDSEK=X', 'USDJPY=X', 'AUDUSD=X'],
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })


if __name__ == '__main__':
    init_logging(level='INFO')
    log.info("Starting STOCK SIMULATOR Chart API server")
    
    # Ensure data directory exists
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        log.info(f"Data directory ready: {DATA_DIR}")
    except Exception as e:
        log.error(f"Failed to create data directory: {e}")
    
    print("\n" + "="*60)
    print("🚀 STOCK SIMULATOR Chart API Server")
    print("="*60)
    print(f"📡 API running at: http://localhost:5000")
    print(f"📊 Chart UI at: trading_chart.html")
    print(f"💾 Data directory: {DATA_DIR}")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')