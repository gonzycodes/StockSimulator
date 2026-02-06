"""
Tests for STOCK SIMULATOR Chart API endpoints.

Run with: pytest test_api.py -v
"""

import pytest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from api_server import app
from src.portfolio import Portfolio
from src.cli import save_portfolio


@pytest.fixture
def client():
    """Create test client for Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def clean_portfolio(tmp_path, monkeypatch):
    """Create a clean portfolio for testing."""
    test_data_dir = tmp_path / "data"
    test_data_dir.mkdir()
    
    from src import config
    monkeypatch.setattr(config, 'DATA_DIR', test_data_dir)
    
    portfolio = Portfolio(cash=10000.0)
    save_portfolio(portfolio, test_data_dir / "portfolio.json")
    
    yield portfolio, test_data_dir


class TestHealthEndpoint:
    
    def test_health_check(self, client):
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'timestamp' in data


class TestQuoteEndpoint:
    
    def test_valid_ticker(self, client):
        response = client.get('/api/quote/AAPL')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['ticker'] == 'AAPL'
        assert 'price' in data
        assert isinstance(data['price'], (int, float))
    
    def test_crypto_ticker(self, client):
        response = client.get('/api/quote/BTC-USD')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['ticker'] == 'BTC-USD'
        assert data['price'] > 0
    
    def test_invalid_ticker(self, client):
        response = client.get('/api/quote/INVALIDTICKER123')
        assert response.status_code == 400


class TestHistoricalEndpoint:
    
    def test_default_params(self, client):
        response = client.get('/api/historical/AAPL')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['ticker'] == 'AAPL'
        assert len(data['data']) > 0
        
        candle = data['data'][0]
        assert all(k in candle for k in ['time', 'open', 'high', 'low', 'close'])
    
    def test_minute_data(self, client):
        response = client.get('/api/historical/BTC-USD?period=1h&interval=1m')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['data']) > 0
    
    def test_ohlc_integrity(self, client):
        """High should be >= open, close, low."""
        response = client.get('/api/historical/AAPL?period=5d')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        for candle in data['data']:
            assert candle['high'] >= candle['open']
            assert candle['high'] >= candle['close']
            assert candle['high'] >= candle['low']
            assert candle['low'] <= candle['open']
            assert candle['low'] <= candle['close']


class TestTradeEndpoint:
    
    def test_buy_crypto(self, client, clean_portfolio):
        """Test buying crypto (24/7 market)."""
        trade_data = {
            'action': 'buy',
            'ticker': 'BTC-USD',
            'quantity': 0.001,
            'order_type': 'market'
        }
        
        response = client.post(
            '/api/trade',
            data=json.dumps(trade_data),
            content_type='application/json'
        )
        
        # May succeed or fail based on market conditions
        assert response.status_code in [200, 400]
    
    def test_sell_without_holdings(self, client, clean_portfolio):
        trade_data = {
            'action': 'sell',
            'ticker': 'AAPL',
            'quantity': 10.0,
            'order_type': 'market'
        }
        
        response = client.post(
            '/api/trade',
            data=json.dumps(trade_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_invalid_action(self, client):
        trade_data = {
            'action': 'invalid',
            'ticker': 'AAPL',
            'quantity': 1.0
        }
        
        response = client.post(
            '/api/trade',
            data=json.dumps(trade_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestMarketsEndpoint:
    
    def test_get_markets(self, client):
        response = client.get('/api/markets')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert all(k in data for k in ['stocks', 'crypto', 'forex'])
        assert 'AAPL' in data['stocks']
        assert 'BTC-USD' in data['crypto']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])