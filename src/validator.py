"""
Validation module for Binance Futures Order Bot
Validates inputs (symbol, quantity, price thresholds) with comprehensive error handling
"""

import re
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal, InvalidOperation
from src.config import SUPPORTED_SYMBOLS, ORDER_TYPES, SIDE_TYPES, TIME_IN_FORCE
from src.logger import logger

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class OrderValidator:
    """Validator for order parameters"""
    
    def __init__(self):
        self.symbol_pattern = re.compile(r'^[A-Z0-9]+$')
        self.price_pattern = re.compile(r'^\d+(\.\d+)?$')
        self.quantity_pattern = re.compile(r'^\d+(\.\d+)?$')
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate trading symbol"""
        if not symbol:
            logger.log_validation_error("symbol", symbol, "Symbol cannot be empty")
            raise ValidationError("Symbol cannot be empty")
        
        if not isinstance(symbol, str):
            logger.log_validation_error("symbol", symbol, "Symbol must be a string")
            raise ValidationError("Symbol must be a string")
        
        symbol = symbol.upper()
        
        if not self.symbol_pattern.match(symbol):
            logger.log_validation_error("symbol", symbol, "Invalid symbol format")
            raise ValidationError("Invalid symbol format")
        
        if symbol not in SUPPORTED_SYMBOLS:
            logger.log_validation_error("symbol", symbol, f"Symbol {symbol} not supported")
            raise ValidationError(f"Symbol {symbol} not supported. Supported symbols: {', '.join(SUPPORTED_SYMBOLS)}")
        
        return True
    
    def validate_side(self, side: str) -> bool:
        """Validate order side"""
        if not side:
            logger.log_validation_error("side", side, "Side cannot be empty")
            raise ValidationError("Side cannot be empty")
        
        side = side.upper()
        
        if side not in SIDE_TYPES:
            logger.log_validation_error("side", side, f"Invalid side: {side}")
            raise ValidationError(f"Invalid side: {side}. Must be one of: {', '.join(SIDE_TYPES.keys())}")
        
        return True
    
    def validate_order_type(self, order_type: str) -> bool:
        """Validate order type"""
        if not order_type:
            logger.log_validation_error("order_type", order_type, "Order type cannot be empty")
            raise ValidationError("Order type cannot be empty")
        
        order_type = order_type.upper()
        
        if order_type not in ORDER_TYPES:
            logger.log_validation_error("order_type", order_type, f"Invalid order type: {order_type}")
            raise ValidationError(f"Invalid order type: {order_type}. Must be one of: {', '.join(ORDER_TYPES.keys())}")
        
        return True
    
    def validate_quantity(self, quantity: Any) -> float:
        """Validate and convert quantity to float"""
        if quantity is None:
            logger.log_validation_error("quantity", quantity, "Quantity cannot be None")
            raise ValidationError("Quantity cannot be None")
        
        try:
            quantity_float = float(quantity)
        except (ValueError, TypeError):
            logger.log_validation_error("quantity", quantity, "Quantity must be a valid number")
            raise ValidationError("Quantity must be a valid number")
        
        if quantity_float <= 0:
            logger.log_validation_error("quantity", quantity_float, "Quantity must be positive")
            raise ValidationError("Quantity must be positive")
        
        if quantity_float > 1000000:  # Reasonable upper limit
            logger.log_validation_error("quantity", quantity_float, "Quantity too large")
            raise ValidationError("Quantity too large (max: 1,000,000)")
        
        return quantity_float
    
    def validate_price(self, price: Any, allow_zero: bool = False) -> float:
        """Validate and convert price to float"""
        if price is None:
            logger.log_validation_error("price", price, "Price cannot be None")
            raise ValidationError("Price cannot be None")
        
        try:
            price_float = float(price)
        except (ValueError, TypeError):
            logger.log_validation_error("price", price, "Price must be a valid number")
            raise ValidationError("Price must be a valid number")
        
        if not allow_zero and price_float <= 0:
            logger.log_validation_error("price", price_float, "Price must be positive")
            raise ValidationError("Price must be positive")
        
        if price_float > 1000000:  # Reasonable upper limit
            logger.log_validation_error("price", price_float, "Price too large")
            raise ValidationError("Price too large (max: 1,000,000)")
        
        return price_float
    
    def validate_time_in_force(self, time_in_force: str) -> bool:
        """Validate time in force parameter"""
        if not time_in_force:
            logger.log_validation_error("time_in_force", time_in_force, "Time in force cannot be empty")
            raise ValidationError("Time in force cannot be empty")
        
        time_in_force = time_in_force.upper()
        
        if time_in_force not in TIME_IN_FORCE:
            logger.log_validation_error("time_in_force", time_in_force, f"Invalid time in force: {time_in_force}")
            raise ValidationError(f"Invalid time in force: {time_in_force}. Must be one of: {', '.join(TIME_IN_FORCE.keys())}")
        
        return True
    
    def validate_stop_price(self, stop_price: Any) -> float:
        """Validate stop price for stop orders"""
        return self.validate_price(stop_price)
    
    def validate_take_profit_price(self, take_profit_price: Any) -> float:
        """Validate take profit price"""
        return self.validate_price(take_profit_price)
    
    def validate_stop_loss_price(self, stop_loss_price: Any) -> float:
        """Validate stop loss price"""
        return self.validate_price(stop_loss_price)
    
    def validate_leverage(self, leverage: Any) -> int:
        """Validate leverage value"""
        if leverage is None:
            logger.log_validation_error("leverage", leverage, "Leverage cannot be None")
            raise ValidationError("Leverage cannot be None")
        
        try:
            leverage_int = int(leverage)
        except (ValueError, TypeError):
            logger.log_validation_error("leverage", leverage, "Leverage must be an integer")
            raise ValidationError("Leverage must be an integer")
        
        if leverage_int < 1 or leverage_int > 125:
            logger.log_validation_error("leverage", leverage_int, "Leverage must be between 1 and 125")
            raise ValidationError("Leverage must be between 1 and 125")
        
        return leverage_int
    
    def validate_market_order_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate market order parameters"""
        validated_params = {}
        
        # Required fields
        validated_params['symbol'] = params.get('symbol')
        validated_params['side'] = params.get('side')
        validated_params['quantity'] = params.get('quantity')
        
        # Validate required fields
        self.validate_symbol(validated_params['symbol'])
        self.validate_side(validated_params['side'])
        validated_params['quantity'] = self.validate_quantity(validated_params['quantity'])
        
        # Optional fields
        if 'timeInForce' in params:
            self.validate_time_in_force(params['timeInForce'])
            validated_params['timeInForce'] = params['timeInForce'].upper()
        
        return validated_params
    
    def validate_limit_order_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate limit order parameters"""
        validated_params = self.validate_market_order_params(params)
        
        # Additional required field for limit orders
        validated_params['price'] = params.get('price')
        validated_params['price'] = self.validate_price(validated_params['price'])
        
        return validated_params
    
    def validate_stop_limit_order_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate stop-limit order parameters"""
        validated_params = self.validate_limit_order_params(params)
        
        # Additional required field for stop-limit orders
        validated_params['stopPrice'] = params.get('stopPrice')
        validated_params['stopPrice'] = self.validate_stop_price(validated_params['stopPrice'])
        
        return validated_params
    
    def validate_oco_order_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate OCO order parameters"""
        validated_params = {}
        
        # Required fields
        validated_params['symbol'] = params.get('symbol')
        validated_params['side'] = params.get('side')
        validated_params['quantity'] = params.get('quantity')
        validated_params['price'] = params.get('price')
        validated_params['stopPrice'] = params.get('stopPrice')
        validated_params['stopLimitPrice'] = params.get('stopLimitPrice')
        
        # Validate required fields
        self.validate_symbol(validated_params['symbol'])
        self.validate_side(validated_params['side'])
        validated_params['quantity'] = self.validate_quantity(validated_params['quantity'])
        validated_params['price'] = self.validate_price(validated_params['price'])
        validated_params['stopPrice'] = self.validate_stop_price(validated_params['stopPrice'])
        validated_params['stopLimitPrice'] = self.validate_price(validated_params['stopLimitPrice'])
        
        # Optional fields
        if 'timeInForce' in params:
            self.validate_time_in_force(params['timeInForce'])
            validated_params['timeInForce'] = params['timeInForce'].upper()
        
        return validated_params
    
    def validate_twap_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate TWAP order parameters"""
        validated_params = {}
        
        # Required fields
        validated_params['symbol'] = params.get('symbol')
        validated_params['side'] = params.get('side')
        validated_params['totalQuantity'] = params.get('totalQuantity')
        validated_params['duration'] = params.get('duration')  # in seconds
        validated_params['chunks'] = params.get('chunks')
        
        # Validate required fields
        self.validate_symbol(validated_params['symbol'])
        self.validate_side(validated_params['side'])
        validated_params['totalQuantity'] = self.validate_quantity(validated_params['totalQuantity'])
        
        # Validate duration
        duration = validated_params['duration']
        if not isinstance(duration, (int, float)) or duration <= 0:
            logger.log_validation_error("duration", duration, "Duration must be a positive number")
            raise ValidationError("Duration must be a positive number")
        
        # Validate chunks
        chunks = validated_params['chunks']
        if not isinstance(chunks, int) or chunks < 1:
            logger.log_validation_error("chunks", chunks, "Chunks must be a positive integer")
            raise ValidationError("Chunks must be a positive integer")
        
        return validated_params
    
    def validate_grid_order_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate grid order parameters"""
        validated_params = {}
        
        # Required fields
        validated_params['symbol'] = params.get('symbol')
        validated_params['upperPrice'] = params.get('upperPrice')
        validated_params['lowerPrice'] = params.get('lowerPrice')
        validated_params['gridNumber'] = params.get('gridNumber')
        validated_params['totalInvestment'] = params.get('totalInvestment')
        
        # Validate required fields
        self.validate_symbol(validated_params['symbol'])
        validated_params['upperPrice'] = self.validate_price(validated_params['upperPrice'])
        validated_params['lowerPrice'] = self.validate_price(validated_params['lowerPrice'])
        
        # Validate price range
        if validated_params['upperPrice'] <= validated_params['lowerPrice']:
            logger.log_validation_error("price_range", f"{validated_params['lowerPrice']}-{validated_params['upperPrice']}", 
                                      "Upper price must be greater than lower price")
            raise ValidationError("Upper price must be greater than lower price")
        
        # Validate grid number
        grid_number = validated_params['gridNumber']
        if not isinstance(grid_number, int) or grid_number < 2:
            logger.log_validation_error("gridNumber", grid_number, "Grid number must be at least 2")
            raise ValidationError("Grid number must be at least 2")
        
        # Validate total investment
        total_investment = validated_params['totalInvestment']
        if not isinstance(total_investment, (int, float)) or total_investment <= 0:
            logger.log_validation_error("totalInvestment", total_investment, "Total investment must be positive")
            raise ValidationError("Total investment must be positive")
        
        return validated_params

# Global validator instance
validator = OrderValidator() 