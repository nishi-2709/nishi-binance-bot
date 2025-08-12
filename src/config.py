"""
Configuration module for Binance Futures Order Bot
Handles API keys, settings, and constants
"""

import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class BinanceConfig:
    """Configuration for Binance API"""
    api_key: str
    api_secret: str
    testnet: bool = True
    base_url: str = "https://testnet.binancefuture.com" if testnet else "https://fapi.binance.com"

@dataclass
class TradingConfig:
    """Trading configuration"""
    default_leverage: int = 1
    max_position_size: float = 1000.0  # USDT
    risk_percentage: float = 2.0  # 2% risk per trade
    max_open_orders: int = 10

@dataclass
class LoggingConfig:
    """Logging configuration"""
    log_level: str = "INFO"
    log_file: str = "bot.log"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Common constants
SUPPORTED_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT",
    "DOTUSDT", "LINKUSDT", "MATICUSDT", "AVAXUSDT", "UNIUSDT"
]

ORDER_TYPES = {
    "MARKET": "MARKET",
    "LIMIT": "LIMIT",
    "STOP": "STOP",
    "STOP_MARKET": "STOP_MARKET",
    "TAKE_PROFIT": "TAKE_PROFIT",
    "TAKE_PROFIT_MARKET": "TAKE_PROFIT_MARKET",
    "TRAILING_STOP_MARKET": "TRAILING_STOP_MARKET"
}

SIDE_TYPES = {
    "BUY": "BUY",
    "SELL": "SELL"
}

TIME_IN_FORCE = {
    "GTC": "GTC",  # Good Till Cancel
    "IOC": "IOC",  # Immediate or Cancel
    "FOK": "FOK"   # Fill or Kill
}

class Config:
    """Main configuration class"""
    
    def __init__(self):
        self._binance_config = None
        self.trading = TradingConfig()
        self.logging = LoggingConfig()
    
    @property
    def binance(self) -> BinanceConfig:
        """Lazy load Binance configuration"""
        if self._binance_config is None:
            self._binance_config = self._load_binance_config()
        return self._binance_config
    
    def _load_binance_config(self) -> BinanceConfig:
        """Load Binance configuration from environment variables"""
        api_key = os.getenv("BINANCE_API_KEY", "")
        api_secret = os.getenv("BINANCE_API_SECRET", "")
        testnet = os.getenv("BINANCE_TESTNET", "true").lower() == "true"
        
        if not api_key or not api_secret:
            raise ValueError(
                "BINANCE_API_KEY and BINANCE_API_SECRET environment variables must be set. "
                "Please set them or create a .env file."
            )
        
        return BinanceConfig(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet
        )
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            "X-MBX-APIKEY": self.binance.api_key
        }

# Global configuration instance
config = Config() 