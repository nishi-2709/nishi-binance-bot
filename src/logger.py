"""
Logging module for Binance Futures Order Bot
Provides structured logging with timestamps and error traces
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from src.config import config

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record):
        """Format log record with structured data"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
        
        return json.dumps(log_entry, ensure_ascii=False)

class BotLogger:
    """Main logger class for the trading bot"""
    
    def __init__(self, name: str = "binance_bot"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, config.logging.log_level))
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # File handler for structured logging
        file_handler = logging.FileHandler(
            log_dir / config.logging.log_file,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())
        
        # Console handler for human-readable output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add handlers if not already added
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def log_order_placed(self, order_data: Dict[str, Any], order_id: str):
        """Log order placement"""
        extra_data = {
            "event_type": "order_placed",
            "order_id": order_id,
            "symbol": order_data.get("symbol"),
            "side": order_data.get("side"),
            "order_type": order_data.get("type"),
            "quantity": order_data.get("quantity"),
            "price": order_data.get("price")
        }
        self.logger.info("Order placed successfully", extra={"extra_data": extra_data})
    
    def log_order_executed(self, order_id: str, execution_data: Dict[str, Any]):
        """Log order execution"""
        extra_data = {
            "event_type": "order_executed",
            "order_id": order_id,
            "execution_price": execution_data.get("price"),
            "executed_qty": execution_data.get("executedQty"),
            "commission": execution_data.get("commission")
        }
        self.logger.info("Order executed", extra={"extra_data": extra_data})
    
    def log_order_cancelled(self, order_id: str, reason: str = ""):
        """Log order cancellation"""
        extra_data = {
            "event_type": "order_cancelled",
            "order_id": order_id,
            "reason": reason
        }
        self.logger.info("Order cancelled", extra={"extra_data": extra_data})
    
    def log_error(self, error: Exception, context: str = ""):
        """Log errors with context"""
        extra_data = {
            "event_type": "error",
            "error_type": type(error).__name__,
            "context": context
        }
        self.logger.error(f"Error occurred: {str(error)}", 
                         extra={"extra_data": extra_data}, 
                         exc_info=True)
    
    def log_api_call(self, endpoint: str, method: str, params: Dict[str, Any] = None):
        """Log API calls"""
        extra_data = {
            "event_type": "api_call",
            "endpoint": endpoint,
            "method": method,
            "params": params or {}
        }
        self.logger.debug("API call made", extra={"extra_data": extra_data})
    
    def log_validation_error(self, field: str, value: Any, message: str):
        """Log validation errors"""
        extra_data = {
            "event_type": "validation_error",
            "field": field,
            "value": value,
            "message": message
        }
        self.logger.warning(f"Validation error: {message}", extra={"extra_data": extra_data})
    
    def log_strategy_event(self, strategy_name: str, event: str, data: Dict[str, Any] = None):
        """Log strategy-specific events"""
        extra_data = {
            "event_type": "strategy_event",
            "strategy": strategy_name,
            "event": event,
            "data": data or {}
        }
        self.logger.info(f"Strategy event: {strategy_name} - {event}", 
                        extra={"extra_data": extra_data})
    
    def log_balance_update(self, asset: str, free: float, locked: float):
        """Log balance updates"""
        extra_data = {
            "event_type": "balance_update",
            "asset": asset,
            "free": free,
            "locked": locked
        }
        self.logger.info(f"Balance updated: {asset}", extra={"extra_data": extra_data})
    
    def log_position_update(self, symbol: str, side: str, size: float, entry_price: float):
        """Log position updates"""
        extra_data = {
            "event_type": "position_update",
            "symbol": symbol,
            "side": side,
            "size": size,
            "entry_price": entry_price
        }
        self.logger.info(f"Position updated: {symbol}", extra={"extra_data": extra_data})

# Global logger instance
logger = BotLogger() 