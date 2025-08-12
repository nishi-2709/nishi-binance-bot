"""
Grid Orders module for Binance Futures Order Bot
Handles grid order placement, execution, and management for automated buy-low/sell-high strategies
"""

import time
import math
from typing import Dict, Any, Optional, List
from datetime import datetime
from src.config import config, SIDE_TYPES, ORDER_TYPES
from src.logger import logger
from src.validator import validator, ValidationError
from src.api_client import BinanceClient
from src.limit_orders import LimitOrder

class GridOrder:
    """Grid order implementation for automated buy-low/sell-high strategies"""
    
    def __init__(self, client: BinanceClient):
        self.client = client
        self.limit_order = LimitOrder(client)
    
    def create_grid_strategy(self, 
                           symbol: str, 
                           upper_price: float,
                           lower_price: float,
                           grid_number: int,
                           total_investment: float,
                           grid_type: str = "arithmetic") -> Dict[str, Any]:
        """
        Create a grid trading strategy
        
        Args:
            symbol: Trading symbol
            upper_price: Upper price boundary
            lower_price: Lower price boundary
            grid_number: Number of grid levels
            total_investment: Total investment amount in USDT
            grid_type: Type of grid ('arithmetic' or 'geometric')
            
        Returns:
            Grid strategy configuration
        """
        try:
            # Validate inputs
            validator.validate_symbol(symbol)
            upper_price = validator.validate_price(upper_price)
            lower_price = validator.validate_price(lower_price)
            
            if upper_price <= lower_price:
                raise ValidationError("Upper price must be greater than lower price")
            
            if grid_number < 2:
                raise ValidationError("Grid number must be at least 2")
            
            if total_investment <= 0:
                raise ValidationError("Total investment must be positive")
            
            # Calculate grid levels
            if grid_type == "arithmetic":
                price_step = (upper_price - lower_price) / (grid_number - 1)
                grid_prices = [lower_price + i * price_step for i in range(grid_number)]
            elif grid_type == "geometric":
                ratio = (upper_price / lower_price) ** (1 / (grid_number - 1))
                grid_prices = [lower_price * (ratio ** i) for i in range(grid_number)]
            else:
                raise ValidationError("Grid type must be 'arithmetic' or 'geometric'")
            
            # Calculate investment per grid level
            investment_per_grid = total_investment / grid_number
            
            # Create grid orders
            grid_orders = []
            for i in range(grid_number - 1):
                # Buy order at current level
                buy_price = grid_prices[i]
                buy_quantity = investment_per_grid / buy_price
                
                # Sell order at next level
                sell_price = grid_prices[i + 1]
                sell_quantity = buy_quantity  # Same quantity for sell
                
                grid_level = {
                    "level": i + 1,
                    "buy_price": buy_price,
                    "buy_quantity": buy_quantity,
                    "sell_price": sell_price,
                    "sell_quantity": sell_quantity,
                    "investment": investment_per_grid,
                    "potential_profit": (sell_price - buy_price) * buy_quantity
                }
                
                grid_orders.append(grid_level)
            
            grid_strategy = {
                "symbol": symbol,
                "upper_price": upper_price,
                "lower_price": lower_price,
                "grid_number": grid_number,
                "grid_type": grid_type,
                "total_investment": total_investment,
                "grid_prices": grid_prices,
                "grid_orders": grid_orders,
                "created_at": datetime.now().isoformat(),
                "status": "created"
            }
            
            # Log grid strategy creation
            logger.log_strategy_event("Grid", "created", {
                "symbol": symbol,
                "grid_number": grid_number,
                "total_investment": total_investment,
                "price_range": f"{lower_price} - {upper_price}"
            })
            
            return grid_strategy
            
        except Exception as e:
            logger.log_error(e, f"Grid strategy creation failed for {symbol}")
            raise 