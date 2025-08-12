"""
Market Orders module for Binance Futures Order Bot
Handles market order placement, execution, and management
"""

import time
from typing import Dict, Any, Optional
from src.config import config, ORDER_TYPES, SIDE_TYPES
from src.logger import logger
from src.validator import validator, ValidationError
from src.api_client import BinanceClient

class MarketOrder:
    """Market order implementation"""
    
    def __init__(self, client: BinanceClient):
        self.client = client
    
    def place_market_order(self, 
                          symbol: str, 
                          side: str, 
                          quantity: float,
                          time_in_force: str = "IOC",
                          reduce_only: bool = False,
                          close_on_trigger: bool = False) -> Dict[str, Any]:
        """
        Place a market order
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            time_in_force: Time in force ('IOC', 'FOK', 'GTC')
            reduce_only: Whether to reduce position only
            close_on_trigger: Whether to close position on trigger
            
        Returns:
            Order response from Binance API
        """
        try:
            # Validate inputs
            validator.validate_symbol(symbol)
            validator.validate_side(side)
            quantity = validator.validate_quantity(quantity)
            validator.validate_time_in_force(time_in_force)
            
            # Prepare order parameters
            order_params = {
                "symbol": symbol.upper(),
                "side": side.upper(),
                "type": ORDER_TYPES["MARKET"],
                "quantity": quantity,
                "timeInForce": time_in_force.upper(),
                "reduceOnly": reduce_only,
                "closeOnTrigger": close_on_trigger
            }
            
            # Log the order attempt
            logger.logger.info(f"Placing market order: {symbol} {side} {quantity}")
            
            # Place the order
            response = self.client.place_order(order_params)
            
            # Log successful order placement
            logger.log_order_placed(order_params, response.get('orderId', 'unknown'))
            
            return response
            
        except ValidationError as e:
            logger.log_error(e, f"Market order validation failed for {symbol}")
            raise
        except Exception as e:
            logger.log_error(e, f"Market order placement failed for {symbol}")
            raise
    
    def place_market_buy_order(self, 
                              symbol: str, 
                              quantity: float,
                              **kwargs) -> Dict[str, Any]:
        """Place a market buy order"""
        return self.place_market_order(symbol, SIDE_TYPES["BUY"], quantity, **kwargs)
    
    def place_market_sell_order(self, 
                               symbol: str, 
                               quantity: float,
                               **kwargs) -> Dict[str, Any]:
        """Place a market sell order"""
        return self.place_market_order(symbol, SIDE_TYPES["SELL"], quantity, **kwargs)
    
    def place_market_order_by_quote_quantity(self,
                                           symbol: str,
                                           side: str,
                                           quote_quantity: float,
                                           **kwargs) -> Dict[str, Any]:
        """
        Place a market order using quote quantity (USDT amount)
        
        Args:
            symbol: Trading symbol
            side: Order side
            quote_quantity: Amount in quote currency (USDT)
            **kwargs: Additional parameters
        """
        try:
            # Validate inputs
            validator.validate_symbol(symbol)
            validator.validate_side(side)
            quote_quantity = validator.validate_quantity(quote_quantity)
            
            # Get current market price
            ticker = self.client.get_symbol_price_ticker(symbol)
            current_price = float(ticker['price'])
            
            # Calculate quantity based on quote amount
            quantity = quote_quantity / current_price
            
            # Place the order
            return self.place_market_order(symbol, side, quantity, **kwargs)
            
        except Exception as e:
            logger.log_error(e, f"Market order by quote quantity failed for {symbol}")
            raise
    
    def place_market_buy_by_quote(self, 
                                 symbol: str, 
                                 usdt_amount: float,
                                 **kwargs) -> Dict[str, Any]:
        """Place a market buy order using USDT amount"""
        return self.place_market_order_by_quote_quantity(symbol, SIDE_TYPES["BUY"], usdt_amount, **kwargs)
    
    def place_market_sell_by_quote(self, 
                                  symbol: str, 
                                  usdt_amount: float,
                                  **kwargs) -> Dict[str, Any]:
        """Place a market sell order using USDT amount"""
        return self.place_market_order_by_quote_quantity(symbol, SIDE_TYPES["SELL"], usdt_amount, **kwargs)
    
    def get_order_status(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Get the status of a specific order"""
        try:
            validator.validate_symbol(symbol)
            
            response = self.client.get_order(symbol, order_id)
            
            # Log order status
            status = response.get('status', 'unknown')
            logger.logger.info(f"Order {order_id} status: {status}")
            
            return response
            
        except Exception as e:
            logger.log_error(e, f"Failed to get order status for {order_id}")
            raise
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Cancel a specific order"""
        try:
            validator.validate_symbol(symbol)
            
            response = self.client.cancel_order(symbol, order_id)
            
            # Log order cancellation
            logger.log_order_cancelled(order_id, "User requested cancellation")
            
            return response
            
        except Exception as e:
            logger.log_error(e, f"Failed to cancel order {order_id}")
            raise
    
    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """Get all open orders for a symbol or all symbols"""
        try:
            if symbol:
                validator.validate_symbol(symbol)
            
            response = self.client.get_open_orders(symbol)
            
            # Log open orders count
            count = len(response)
            logger.logger.info(f"Retrieved {count} open orders for {symbol or 'all symbols'}")
            
            return response
            
        except Exception as e:
            logger.log_error(e, f"Failed to get open orders for {symbol or 'all symbols'}")
            raise
    
    def cancel_all_orders(self, symbol: str) -> Dict[str, Any]:
        """Cancel all open orders for a symbol"""
        try:
            validator.validate_symbol(symbol)
            
            response = self.client.cancel_all_orders(symbol)
            
            # Log cancellation
            cancelled_count = len(response.get('cancelledOrders', []))
            logger.logger.info(f"Cancelled {cancelled_count} orders for {symbol}")
            
            return response
            
        except Exception as e:
            logger.log_error(e, f"Failed to cancel all orders for {symbol}")
            raise

class MarketOrderManager:
    """Manager for market order operations"""
    
    def __init__(self, client: BinanceClient):
        self.client = client
        self.market_order = MarketOrder(client)
    
    def execute_quick_trade(self, 
                           symbol: str, 
                           side: str, 
                           quantity: float,
                           max_slippage: float = 0.01) -> Dict[str, Any]:
        """
        Execute a quick trade with slippage protection
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            max_slippage: Maximum allowed slippage (1% default)
        """
        try:
            # Get current market price before order
            ticker_before = self.client.get_symbol_price_ticker(symbol)
            price_before = float(ticker_before['price'])
            
            # Place the order
            order_response = self.market_order.place_market_order(symbol, side, quantity)
            
            # Get execution details
            order_id = order_response.get('orderId')
            if order_id:
                order_status = self.market_order.get_order_status(symbol, order_id)
                
                # Check for slippage
                if order_status.get('status') == 'FILLED':
                    avg_price = float(order_status.get('avgPrice', 0))
                    if avg_price > 0:
                        slippage = abs(avg_price - price_before) / price_before
                        
                        if slippage > max_slippage:
                            logger.logger.warning(f"High slippage detected: {slippage:.4f} for {symbol}")
                        
                        # Log execution
                        logger.log_order_executed(order_id, {
                            'price': avg_price,
                            'executedQty': order_status.get('executedQty'),
                            'commission': order_status.get('commission', '0')
                        })
            
            return order_response
            
        except Exception as e:
            logger.log_error(e, f"Quick trade execution failed for {symbol}")
            raise
    
    def execute_dca_strategy(self, 
                           symbol: str, 
                           total_amount: float,
                           num_orders: int,
                           interval_seconds: int = 300) -> list:
        """
        Execute Dollar Cost Averaging (DCA) strategy
        
        Args:
            symbol: Trading symbol
            total_amount: Total USDT amount to invest
            num_orders: Number of orders to split into
            interval_seconds: Interval between orders in seconds
        """
        try:
            orders = []
            amount_per_order = total_amount / num_orders
            
            logger.logger.info(f"Starting DCA strategy: {symbol}, {num_orders} orders, {interval_seconds}s intervals")
            
            for i in range(num_orders):
                try:
                    # Place market buy order
                    order = self.market_order.place_market_buy_by_quote(symbol, amount_per_order)
                    orders.append(order)
                    
                    logger.logger.info(f"DCA order {i+1}/{num_orders} placed: {order.get('orderId')}")
                    
                    # Wait for next order (except for the last one)
                    if i < num_orders - 1:
                        time.sleep(interval_seconds)
                        
                except Exception as e:
                    logger.log_error(e, f"DCA order {i+1} failed")
                    # Continue with remaining orders
            
            logger.logger.info(f"DCA strategy completed: {len(orders)} orders placed")
            return orders
            
        except Exception as e:
            logger.log_error(e, f"DCA strategy failed for {symbol}")
            raise 