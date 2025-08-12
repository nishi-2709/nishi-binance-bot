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
    
    def execute_grid_strategy(self, 
                            grid_strategy: Dict[str, Any],
                            auto_rebalance: bool = True,
                            max_concurrent_orders: int = 5) -> Dict[str, Any]:
        """
        Execute a grid trading strategy
        
        Args:
            grid_strategy: Grid strategy configuration
            auto_rebalance: Whether to automatically rebalance the grid
            max_concurrent_orders: Maximum number of concurrent orders
            
        Returns:
            Grid execution results
        """
        try:
            symbol = grid_strategy["symbol"]
            grid_orders = grid_strategy["grid_orders"]
            
            # Get current market price
            ticker = self.client.get_symbol_price_ticker(symbol)
            current_price = float(ticker['price'])
            
            # Log grid execution start
            logger.log_strategy_event("Grid", "execution_started", {
                "symbol": symbol,
                "current_price": current_price,
                "grid_levels": len(grid_orders)
            })
            
            execution_results = {
                "symbol": symbol,
                "current_price": current_price,
                "execution_start": datetime.now().isoformat(),
                "placed_orders": [],
                "executed_orders": [],
                "total_profit": 0,
                "status": "executing"
            }
            
            # Place initial grid orders
            placed_orders = []
            for grid_level in grid_orders:
                try:
                    # Place buy order if current price is above buy price
                    if current_price > grid_level["buy_price"]:
                        buy_order = self.limit_order.place_limit_buy_order(
                            symbol, grid_level["buy_quantity"], grid_level["buy_price"]
                        )
                        placed_orders.append({
                            "grid_level": grid_level["level"],
                            "order_type": "buy",
                            "order_id": buy_order.get("orderId"),
                            "price": grid_level["buy_price"],
                            "quantity": grid_level["buy_quantity"]
                        })
                    
                    # Place sell order if current price is below sell price
                    if current_price < grid_level["sell_price"]:
                        sell_order = self.limit_order.place_limit_sell_order(
                            symbol, grid_level["sell_quantity"], grid_level["sell_price"]
                        )
                        placed_orders.append({
                            "grid_level": grid_level["level"],
                            "order_type": "sell",
                            "order_id": sell_order.get("orderId"),
                            "price": grid_level["sell_price"],
                            "quantity": grid_level["sell_quantity"]
                        })
                    
                    # Limit concurrent orders
                    if len(placed_orders) >= max_concurrent_orders:
                        break
                        
                except Exception as e:
                    logger.log_error(e, f"Grid order placement failed for level {grid_level['level']}")
            
            execution_results["placed_orders"] = placed_orders
            
            # Monitor and manage grid orders
            if auto_rebalance:
                self._monitor_and_rebalance_grid(grid_strategy, execution_results)
            
            execution_results["status"] = "completed"
            execution_results["execution_end"] = datetime.now().isoformat()
            
            # Log grid execution completion
            logger.log_strategy_event("Grid", "execution_completed", {
                "total_profit": execution_results["total_profit"],
                "executed_orders": len(execution_results["executed_orders"])
            })
            
            return execution_results
            
        except Exception as e:
            logger.log_error(e, f"Grid strategy execution failed for {symbol}")
            raise
    
    def _monitor_and_rebalance_grid(self, 
                                  grid_strategy: Dict[str, Any],
                                  execution_results: Dict[str, Any]) -> None:
        """Monitor grid orders and rebalance as needed"""
        try:
            symbol = grid_strategy["symbol"]
            grid_orders = grid_strategy["grid_orders"]
            
            # Monitor for a reasonable time period
            monitoring_duration = 3600  # 1 hour
            start_time = time.time()
            
            while time.time() - start_time < monitoring_duration:
                # Check for filled orders
                open_orders = self.client.get_open_orders(symbol)
                
                for placed_order in execution_results["placed_orders"]:
                    order_id = placed_order["order_id"]
                    
                    # Check if order is still open
                    if not any(order["orderId"] == order_id for order in open_orders):
                        # Order was filled, get execution details
                        order_status = self.client.get_order(symbol, order_id)
                        
                        if order_status.get("status") == "FILLED":
                            executed_quantity = float(order_status.get("executedQty", 0))
                            executed_price = float(order_status.get("avgPrice", 0))
                            
                            # Calculate profit/loss
                            grid_level = placed_order["grid_level"]
                            if placed_order["order_type"] == "buy":
                                # Buy order filled, place corresponding sell order
                                sell_price = grid_orders[grid_level - 1]["sell_price"]
                                sell_order = self.limit_order.place_limit_sell_order(
                                    symbol, executed_quantity, sell_price
                                )
                                
                                execution_results["executed_orders"].append({
                                    "grid_level": grid_level,
                                    "buy_order_id": order_id,
                                    "buy_price": executed_price,
                                    "buy_quantity": executed_quantity,
                                    "sell_order_id": sell_order.get("orderId"),
                                    "sell_price": sell_price,
                                    "potential_profit": (sell_price - executed_price) * executed_quantity
                                })
                            else:
                                # Sell order filled, place corresponding buy order
                                buy_price = grid_orders[grid_level - 1]["buy_price"]
                                buy_order = self.limit_order.place_limit_buy_order(
                                    symbol, executed_quantity, buy_price
                                )
                                
                                # Calculate realized profit
                                profit = (executed_price - buy_price) * executed_quantity
                                execution_results["total_profit"] += profit
                                
                                execution_results["executed_orders"].append({
                                    "grid_level": grid_level,
                                    "sell_order_id": order_id,
                                    "sell_price": executed_price,
                                    "sell_quantity": executed_quantity,
                                    "buy_order_id": buy_order.get("orderId"),
                                    "buy_price": buy_price,
                                    "realized_profit": profit
                                })
                
                # Wait before next check
                time.sleep(30)  # Check every 30 seconds
                
        except Exception as e:
            logger.log_error(e, f"Grid monitoring failed for {symbol}")
    
    def create_martingale_grid(self, 
                             symbol: str, 
                             base_price: float,
                             grid_number: int,
                             total_investment: float,
                             multiplier: float = 2.0) -> Dict[str, Any]:
        """
        Create a Martingale grid strategy (increasing position sizes)
        
        Args:
            symbol: Trading symbol
            base_price: Base price for the grid
            grid_number: Number of grid levels
            total_investment: Total investment amount
            multiplier: Position size multiplier for each level
        """
        try:
            # Validate inputs
            validator.validate_symbol(symbol)
            base_price = validator.validate_price(base_price)
            
            if grid_number < 2:
                raise ValidationError("Grid number must be at least 2")
            
            if multiplier <= 1.0:
                raise ValidationError("Multiplier must be greater than 1.0")
            
            # Calculate grid levels with increasing position sizes
            grid_orders = []
            price_step = base_price * 0.01  # 1% price step
            
            for i in range(grid_number):
                # Calculate position size with multiplier
                position_size = total_investment * (multiplier ** i) / sum(multiplier ** j for j in range(grid_number))
                
                # Calculate grid prices
                buy_price = base_price - (i * price_step)
                sell_price = base_price + (i * price_step)
                
                buy_quantity = position_size / buy_price
                sell_quantity = position_size / sell_price
                
                grid_level = {
                    "level": i + 1,
                    "buy_price": buy_price,
                    "buy_quantity": buy_quantity,
                    "sell_price": sell_price,
                    "sell_quantity": sell_quantity,
                    "investment": position_size,
                    "multiplier": multiplier ** i
                }
                
                grid_orders.append(grid_level)
            
            grid_strategy = {
                "symbol": symbol,
                "base_price": base_price,
                "grid_number": grid_number,
                "multiplier": multiplier,
                "total_investment": total_investment,
                "grid_orders": grid_orders,
                "grid_type": "martingale",
                "created_at": datetime.now().isoformat(),
                "status": "created"
            }
            
            logger.log_strategy_event("MartingaleGrid", "created", {
                "symbol": symbol,
                "grid_number": grid_number,
                "multiplier": multiplier
            })
            
            return grid_strategy
            
        except Exception as e:
            logger.log_error(e, f"Martingale grid creation failed for {symbol}")
            raise

class GridOrderManager:
    """Manager for grid order operations"""
    
    def __init__(self, client: BinanceClient):
        self.client = client
        self.grid_order = GridOrder(client)
    
    def create_adaptive_grid(self, 
                           symbol: str, 
                           volatility_period: int = 24,
                           grid_number: int = 10,
                           total_investment: float = 1000.0) -> Dict[str, Any]:
        """
        Create an adaptive grid based on market volatility
        
        Args:
            symbol: Trading symbol
            volatility_period: Period for volatility calculation (hours)
            grid_number: Number of grid levels
            total_investment: Total investment amount
        """
        try:
            # Get historical price data
            klines = self.client.get_klines(symbol, "1h", volatility_period)
            
            if len(klines) < 2:
                raise ValidationError("Insufficient price data for volatility calculation")
            
            # Calculate price range and volatility
            prices = [float(kline[4]) for kline in klines]  # Close prices
            min_price = min(prices)
            max_price = max(prices)
            current_price = prices[-1]
            
            # Calculate volatility
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            volatility = (sum(r*r for r in returns) / len(returns)) ** 0.5
            
            # Adjust grid parameters based on volatility
            if volatility > 0.05:  # High volatility
                price_range_multiplier = 2.0
                grid_type = "geometric"
            else:  # Low volatility
                price_range_multiplier = 1.0
                grid_type = "arithmetic"
            
            # Calculate grid boundaries
            price_range = (max_price - min_price) * price_range_multiplier
            upper_price = current_price + (price_range / 2)
            lower_price = current_price - (price_range / 2)
            
            logger.logger.info(f"Adaptive grid: volatility={volatility:.4f}, range_multiplier={price_range_multiplier}")
            
            return self.grid_order.create_grid_strategy(
                symbol, upper_price, lower_price, grid_number, total_investment, grid_type
            )
            
        except Exception as e:
            logger.log_error(e, f"Adaptive grid creation failed for {symbol}")
            raise 