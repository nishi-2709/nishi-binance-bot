"""
API Client module for Binance Futures Order Bot
Handles all Binance Futures API interactions with authentication and error handling
"""

import time
import hmac
import hashlib
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlencode
from src.config import config
from src.logger import logger

class BinanceClient:
    """Binance Futures API client"""
    
    def __init__(self):
        self.base_url = config.binance.base_url
        self.api_key = config.binance.api_key
        self.api_secret = config.binance.api_secret
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        })
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for authenticated requests"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any] = None, 
                     signed: bool = False) -> Dict[str, Any]:
        """Make HTTP request to Binance API"""
        url = f"{self.base_url}{endpoint}"
        
        if params is None:
            params = {}
        
        # Add timestamp for signed requests
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        # Log API call
        logger.log_api_call(endpoint, method, params)
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, data=params)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.log_error(e, f"API request failed: {method} {endpoint}")
            raise
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        return self._make_request('GET', '/fapi/v2/account', signed=True)
    
    def get_balance(self) -> Dict[str, Any]:
        """Get account balance"""
        return self._make_request('GET', '/fapi/v2/balance', signed=True)
    
    def get_position_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get position information"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/fapi/v2/positionRisk', params, signed=True)
    
    def get_symbol_price_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current price for a symbol"""
        params = {'symbol': symbol}
        return self._make_request('GET', '/fapi/v1/ticker/price', params)
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> list:
        """Get kline/candlestick data"""
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        return self._make_request('GET', '/fapi/v1/klines', params)
    
    def place_order(self, order_params: Dict[str, Any]) -> Dict[str, Any]:
        """Place a new order"""
        return self._make_request('POST', '/fapi/v1/order', order_params, signed=True)
    
    def place_oco_order(self, oco_params: Dict[str, Any]) -> Dict[str, Any]:
        """Place an OCO order"""
        return self._make_request('POST', '/fapi/v1/order/oco', oco_params, signed=True)
    
    def get_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Get order status"""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._make_request('GET', '/fapi/v1/order', params, signed=True)
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._make_request('DELETE', '/fapi/v1/order', params, signed=True)
    
    def cancel_all_orders(self, symbol: str) -> Dict[str, Any]:
        """Cancel all open orders for a symbol"""
        params = {'symbol': symbol}
        return self._make_request('DELETE', '/fapi/v1/allOpenOrders', params, signed=True)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """Get open orders"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/fapi/v1/openOrders', params, signed=True)
    
    def get_order_history(self, symbol: str, limit: int = 500) -> list:
        """Get order history"""
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return self._make_request('GET', '/fapi/v1/allOrders', params, signed=True)
    
    def get_trade_history(self, symbol: str, limit: int = 500) -> list:
        """Get trade history"""
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return self._make_request('GET', '/fapi/v1/userTrades', params, signed=True)
    
    def change_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Change leverage for a symbol"""
        params = {
            'symbol': symbol,
            'leverage': leverage
        }
        return self._make_request('POST', '/fapi/v1/leverage', params, signed=True)
    
    def change_margin_type(self, symbol: str, margin_type: str) -> Dict[str, Any]:
        """Change margin type for a symbol"""
        params = {
            'symbol': symbol,
            'marginType': margin_type
        }
        return self._make_request('POST', '/fapi/v1/marginType', params, signed=True)
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information"""
        return self._make_request('GET', '/fapi/v1/exchangeInfo')
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information"""
        try:
            exchange_info = self.get_exchange_info()
            for symbol_info in exchange_info.get('symbols', []):
                if symbol_info['symbol'] == symbol:
                    return symbol_info
            return None
        except Exception as e:
            logger.log_error(e, f"Failed to get symbol info for {symbol}")
            return None 