"""
TWAP (Time-Weighted Average Price) Orders module for Binance Futures Order Bot
Handles TWAP order placement, execution, and management
"""

import time
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from src.config import config, SIDE_TYPES, ORDER_TYPES
from src.logger import logger
from src.validator import validator, ValidationError
from src.api_client import BinanceClient
from src.market_orders import MarketOrder

class TWAPOrder:
    """TWAP (Time-Weighted Average Price) order implementation"""
    
    def __init__(self, client: BinanceClient):
        self.client = client
        self.market_order = MarketOrder(client)
    
    def execute_twap_strategy(self, 
                            symbol: str, 
                            side: str, 
                            total_quantity: float,
                            duration_seconds: int,
                            num_chunks: int,
                            use_limit_orders: bool = False,
                            limit_price_offset: float = 0.001,
                            randomize_intervals: bool = True,
                            max_slippage: float = 0.01) -> Dict[str, Any]:
        """
        Execute TWAP strategy by splitting large orders into smaller chunks over time
        
        Args:
            symbol: Trading symbol
            side: Order side ('BUY' or 'SELL')
            total_quantity: Total quantity to execute
            duration_seconds: Total duration in seconds
            num_chunks: Number of chunks to split the order into
            use_limit_orders: Whether to use limit orders instead of market orders
            limit_price_offset: Price offset for limit orders (percentage)
            randomize_intervals: Whether to randomize intervals between orders
            max_slippage: Maximum allowed slippage per order
            
        Returns:
            TWAP execution results
        """
        try:
            # Validate inputs
            validator.validate_symbol(symbol)
            validator.validate_side(side)
            total_quantity = validator.validate_quantity(total_quantity)
            
            if duration_seconds <= 0:
                raise ValidationError("Duration must be positive")
            if num_chunks <= 0:
                raise ValidationError("Number of chunks must be positive")
            if num_chunks > total_quantity:
                raise ValidationError("Number of chunks cannot exceed total quantity")
            
            # Calculate chunk size and interval
            chunk_size = total_quantity / num_chunks
            base_interval = duration_seconds / num_chunks
            
            # Log TWAP strategy start
            logger.log_strategy_event("TWAP", "started", {
                "symbol": symbol,
                "side": side,
                "total_quantity": total_quantity,
                "num_chunks": num_chunks,
                "duration_seconds": duration_seconds
            })
            
            execution_results = {
                "symbol": symbol,
                "side": side,
                "total_quantity": total_quantity,
                "num_chunks": num_chunks,
                "duration_seconds": duration_seconds,
                "start_time": datetime.now().isoformat(),
                "chunks": [],
                "total_executed": 0,
                "total_cost": 0,
                "average_price": 0
            }
            
            start_time = time.time()
            
            for i in range(num_chunks):
                try:
                    # Calculate interval with optional randomization
                    if randomize_intervals:
                        interval = base_interval * (0.8 + random.random() * 0.4)  # ±20% variation
                    else:
                        interval = base_interval
                    
                    # Wait for next execution (except for first chunk)
                    if i > 0:
                        time.sleep(interval)
                    
                    # Get current market price
                    ticker = self.client.get_symbol_price_ticker(symbol)
                    current_price = float(ticker['price'])
                    
                    # Execute chunk
                    if use_limit_orders:
                        # Calculate limit price
                        if side == SIDE_TYPES["BUY"]:
                            limit_price = current_price * (1 + limit_price_offset)
                        else:
                            limit_price = current_price * (1 - limit_price_offset)
                        
                        chunk_result = self._execute_limit_chunk(
                            symbol, side, chunk_size, limit_price, i + 1
                        )
                    else:
                        chunk_result = self._execute_market_chunk(
                            symbol, side, chunk_size, current_price, max_slippage, i + 1
                        )
                    
                    execution_results["chunks"].append(chunk_result)
                    execution_results["total_executed"] += chunk_result.get("executed_quantity", 0)
                    execution_results["total_cost"] += chunk_result.get("cost", 0)
                    
                    # Log chunk execution
                    logger.logger.info(f"TWAP chunk {i+1}/{num_chunks} executed: {chunk_result.get('executed_quantity')} @ {chunk_result.get('price')}")
                    
                except Exception as e:
                    logger.log_error(e, f"TWAP chunk {i+1} failed")
                    execution_results["chunks"].append({
                        "chunk_number": i + 1,
                        "status": "failed",
                        "error": str(e)
                    })
            
            # Calculate average price
            if execution_results["total_executed"] > 0:
                execution_results["average_price"] = execution_results["total_cost"] / execution_results["total_executed"]
            
            execution_results["end_time"] = datetime.now().isoformat()
            execution_results["actual_duration"] = time.time() - start_time
            
            # Log TWAP strategy completion
            logger.log_strategy_event("TWAP", "completed", {
                "total_executed": execution_results["total_executed"],
                "average_price": execution_results["average_price"],
                "actual_duration": execution_results["actual_duration"]
            })
            
            return execution_results
            
        except Exception as e:
            logger.log_error(e, f"TWAP strategy failed for {symbol}")
            raise
    
    def _execute_market_chunk(self, 
                            symbol: str, 
                            side: str, 
                            quantity: float,
                            expected_price: float,
                            max_slippage: float,
                            chunk_number: int) -> Dict[str, Any]:
        """Execute a single market order chunk"""
        try:
            # Place market order
            order_response = self.market_order.place_market_order(symbol, side, quantity)
            
            # Get execution details
            order_id = order_response.get('orderId')
            if order_id:
                order_status = self.client.get_order(symbol, order_id)
                
                if order_status.get('status') == 'FILLED':
                    executed_quantity = float(order_status.get('executedQty', 0))
                    avg_price = float(order_status.get('avgPrice', 0))
                    
                    # Check slippage
                    slippage = abs(avg_price - expected_price) / expected_price
                    
                    return {
                        "chunk_number": chunk_number,
                        "status": "executed",
                        "order_id": order_id,
                        "executed_quantity": executed_quantity,
                        "price": avg_price,
                        "cost": executed_quantity * avg_price,
                        "slippage": slippage,
                        "within_slippage": slippage <= max_slippage
                    }
            
            return {
                "chunk_number": chunk_number,
                "status": "pending",
                "order_id": order_id
            }
            
        except Exception as e:
            logger.log_error(e, f"Market chunk {chunk_number} execution failed")
            return {
                "chunk_number": chunk_number,
                "status": "failed",
                "error": str(e)
            }
    
    def _execute_limit_chunk(self, 
                           symbol: str, 
                           side: str, 
                           quantity: float,
                           limit_price: float,
                           chunk_number: int) -> Dict[str, Any]:
        """Execute a single limit order chunk"""
        try:
            from src.limit_orders import LimitOrder
            limit_order = LimitOrder(self.client)
            
            # Place limit order
            order_response = limit_order.place_limit_order(symbol, side, quantity, limit_price)
            
            # Monitor order for a short time
            order_id = order_response.get('orderId')
            if order_id:
                # Wait a bit for potential fill
                time.sleep(2)
                
                order_status = self.client.get_order(symbol, order_id)
                
                if order_status.get('status') == 'FILLED':
                    executed_quantity = float(order_status.get('executedQty', 0))
                    avg_price = float(order_status.get('avgPrice', 0))
                    
                    return {
                        "chunk_number": chunk_number,
                        "status": "executed",
                        "order_id": order_id,
                        "executed_quantity": executed_quantity,
                        "price": avg_price,
                        "cost": executed_quantity * avg_price
                    }
                else:
                    # Cancel unfilled order
                    self.client.cancel_order(symbol, order_id)
                    return {
                        "chunk_number": chunk_number,
                        "status": "cancelled",
                        "order_id": order_id,
                        "reason": "unfilled limit order"
                    }
            
            return {
                "chunk_number": chunk_number,
                "status": "pending",
                "order_id": order_id
            }
            
        except Exception as e:
            logger.log_error(e, f"Limit chunk {chunk_number} execution failed")
            return {
                "chunk_number": chunk_number,
                "status": "failed",
                "error": str(e)
            }

class TWAPManager:
    """Manager for TWAP order operations"""
    
    def __init__(self, client: BinanceClient):
        self.client = client
        self.twap_order = TWAPOrder(client)
    
    def execute_volume_weighted_twap(self, 
                                   symbol: str, 
                                   side: str, 
                                   total_quantity: float,
                                   duration_seconds: int,
                                   volume_profile: List[float]) -> Dict[str, Any]:
        """
        Execute TWAP with volume-weighted distribution
        
        Args:
            symbol: Trading symbol
            side: Order side
            total_quantity: Total quantity to execute
            duration_seconds: Total duration in seconds
            volume_profile: List of volume weights for each time period
        """
        try:
            # Validate volume profile
            if not volume_profile or len(volume_profile) == 0:
                raise ValidationError("Volume profile cannot be empty")
            
            if abs(sum(volume_profile) - 1.0) > 0.01:
                raise ValidationError("Volume profile weights must sum to 1.0")
            
            num_chunks = len(volume_profile)
            chunk_sizes = [total_quantity * weight for weight in volume_profile]
            
            # Execute TWAP with custom chunk sizes
            return self.twap_order.execute_twap_strategy(
                symbol, side, total_quantity, duration_seconds, num_chunks
            )
            
        except Exception as e:
            logger.log_error(e, f"Volume-weighted TWAP failed for {symbol}")
            raise
    
    def execute_adaptive_twap(self, 
                            symbol: str, 
                            side: str, 
                            total_quantity: float,
                            duration_seconds: int,
                            volatility_threshold: float = 0.02) -> Dict[str, Any]:
        """
        Execute adaptive TWAP that adjusts based on market volatility
        
        Args:
            symbol: Trading symbol
            side: Order side
            total_quantity: Total quantity to execute
            duration_seconds: Total duration in seconds
            volatility_threshold: Volatility threshold for adaptation
        """
        try:
            # Get recent price data to calculate volatility
            klines = self.client.get_klines(symbol, "1m", 60)  # Last 60 minutes
            
            if len(klines) < 2:
                raise ValidationError("Insufficient price data for volatility calculation")
            
            # Calculate price volatility
            prices = [float(kline[4]) for kline in klines]  # Close prices
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            volatility = (sum(r*r for r in returns) / len(returns)) ** 0.5
            
            # Adjust strategy based on volatility
            if volatility > volatility_threshold:
                # High volatility: use more chunks with shorter intervals
                num_chunks = 20
                use_limit_orders = True
                limit_price_offset = 0.005  # 0.5% offset
            else:
                # Low volatility: use fewer chunks with longer intervals
                num_chunks = 10
                use_limit_orders = False
                limit_price_offset = 0.001  # 0.1% offset
            
            logger.logger.info(f"Adaptive TWAP: volatility={volatility:.4f}, chunks={num_chunks}, limit_orders={use_limit_orders}")
            
            return self.twap_order.execute_twap_strategy(
                symbol, side, total_quantity, duration_seconds, num_chunks,
                use_limit_orders, limit_price_offset
            )
            
        except Exception as e:
            logger.log_error(e, f"Adaptive TWAP failed for {symbol}")
            raise
    
    def execute_scheduled_twap(self, 
                             symbol: str, 
                             side: str, 
                             total_quantity: float,
                             start_time: datetime,
                             end_time: datetime,
                             num_chunks: int) -> Dict[str, Any]:
        """
        Execute TWAP within a specific time window
        
        Args:
            symbol: Trading symbol
            side: Order side
            total_quantity: Total quantity to execute
            start_time: Start time for execution
            end_time: End time for execution
            num_chunks: Number of chunks
        """
        try:
            # Calculate duration
            duration = (end_time - start_time).total_seconds()
            
            if duration <= 0:
                raise ValidationError("End time must be after start time")
            
            # Wait until start time
            now = datetime.now()
            if start_time > now:
                wait_seconds = (start_time - now).total_seconds()
                logger.logger.info(f"Waiting {wait_seconds:.0f} seconds until TWAP start time")
                time.sleep(wait_seconds)
            
            # Execute TWAP
            return self.twap_order.execute_twap_strategy(
                symbol, side, total_quantity, duration, num_chunks
            )
            
        except Exception as e:
            logger.log_error(e, f"Scheduled TWAP failed for {symbol}")
            raise 