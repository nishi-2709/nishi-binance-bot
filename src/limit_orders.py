"""
Limit Orders module for Binance Futures Order Bot
Handles limit order placement, execution, and management
"""

import time
from typing import Dict, Any, Optional
from src.config import config, ORDER_TYPES, SIDE_TYPES, TIME_IN_FORCE
from src.logger import logger
from src.validator import validator, ValidationError
from src.api_client import BinanceClient

class LimitOrder:
    """Limit order implementation"""
    
    def __init__(self, client: BinanceClient):
        self.client = client
    
    def place_limit_order(self, 
                         symbol: str, 
                         side: str, 
                         quantity: float,
                         price: float,
                         time_in_force: str = "GTC",
                         reduce_only: bool = False,
                         close_on_trigger: bool = False) -> Dict[str, Any]:
        """
        Place a limit order
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            price: Limit price
            time_in_force: Time in force ('GTC', 'IOC', 'FOK')
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
            price = validator.validate_price(price)
            validator.validate_time_in_force(time_in_force)
            
            # Prepare order parameters
            order_params = {
                "symbol": symbol.upper(),
                "side": side.upper(),
                "type": ORDER_TYPES["LIMIT"],
                "quantity": quantity,
                "price": price,
                "timeInForce": time_in_force.upper(),
                "reduceOnly": reduce_only,
                "closeOnTrigger": close_on_trigger
            }
            
            # Log the order attempt
            logger.logger.info(f"Placing limit order: {symbol} {side} {quantity} @ {price}")
            
            # Place the order
            response = self.client.place_order(order_params)
            
            # Log successful order placement
            logger.log_order_placed(order_params, response.get('orderId', 'unknown'))
            
            return response
            
        except ValidationError as e:
            logger.log_error(e, f"Limit order validation failed for {symbol}")
            raise
        except Exception as e:
            logger.log_error(e, f"Limit order placement failed for {symbol}")
            raise
    
    def place_limit_buy_order(self, 
                             symbol: str, 
                             quantity: float,
                             price: float,
                             **kwargs) -> Dict[str, Any]:
        """Place a limit buy order"""
        return self.place_limit_order(symbol, SIDE_TYPES["BUY"], quantity, price, **kwargs)
    
    def place_limit_sell_order(self, 
                              symbol: str, 
                              quantity: float,
                              price: float,
                              **kwargs) -> Dict[str, Any]:
        """Place a limit sell order"""
        return self.place_limit_order(symbol, SIDE_TYPES["SELL"], quantity, price, **kwargs)
    
    def place_limit_order_by_quote_quantity(self,
                                          symbol: str,
                                          side: str,
                                          quote_quantity: float,
                                          price: float,
                                          **kwargs) -> Dict[str, Any]:
        """
        Place a limit order using quote quantity (USDT amount)
        
        Args:
            symbol: Trading symbol
            side: Order side
            quote_quantity: Amount in quote currency (USDT)
            price: Limit price
            **kwargs: Additional parameters
        """
        try:
            # Validate inputs
            validator.validate_symbol(symbol)
            validator.validate_side(side)
            quote_quantity = validator.validate_quantity(quote_quantity)
            price = validator.validate_price(price)
            
            # Calculate quantity based on quote amount and price
            quantity = quote_quantity / price
            
            # Place the order
            return self.place_limit_order(symbol, side, quantity, price, **kwargs)
            
        except Exception as e:
            logger.log_error(e, f"Limit order by quote quantity failed for {symbol}")
            raise
    
    def place_limit_buy_by_quote(self, 
                                symbol: str, 
                                usdt_amount: float,
                                price: float,
                                **kwargs) -> Dict[str, Any]:
        """Place a limit buy order using USDT amount"""
        return self.place_limit_order_by_quote_quantity(symbol, SIDE_TYPES["BUY"], usdt_amount, price, **kwargs)
    
    def place_limit_sell_by_quote(self, 
                                 symbol: str, 
                                 usdt_amount: float,
                                 price: float,
                                 **kwargs) -> Dict[str, Any]:
        """Place a limit sell order using USDT amount"""
        return self.place_limit_order_by_quote_quantity(symbol, SIDE_TYPES["SELL"], usdt_amount, price, **kwargs)
    
    def place_stop_limit_order(self, 
                              symbol: str, 
                              side: str, 
                              quantity: float,
                              price: float,
                              stop_price: float,
                              time_in_force: str = "GTC",
                              reduce_only: bool = False,
                              close_on_trigger: bool = False) -> Dict[str, Any]:
        """
        Place a stop-limit order
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            price: Limit price
            stop_price: Stop price (trigger price)
            time_in_force: Time in force
            reduce_only: Whether to reduce position only
            close_on_trigger: Whether to close position on trigger
        """
        try:
            # Validate inputs
            validator.validate_symbol(symbol)
            validator.validate_side(side)
            quantity = validator.validate_quantity(quantity)
            price = validator.validate_price(price)
            stop_price = validator.validate_stop_price(stop_price)
            validator.validate_time_in_force(time_in_force)
            
            # Prepare order parameters
            order_params = {
                "symbol": symbol.upper(),
                "side": side.upper(),
                "type": ORDER_TYPES["STOP"],
                "quantity": quantity,
                "price": price,
                "stopPrice": stop_price,
                "timeInForce": time_in_force.upper(),
                "reduceOnly": reduce_only,
                "closeOnTrigger": close_on_trigger
            }
            
            # Log the order attempt
            logger.logger.info(f"Placing stop-limit order: {symbol} {side} {quantity} @ {price} (stop: {stop_price})")
            
            # Place the order
            response = self.client.place_order(order_params)
            
            # Log successful order placement
            logger.log_order_placed(order_params, response.get('orderId', 'unknown'))
            
            return response
            
        except ValidationError as e:
            logger.log_error(e, f"Stop-limit order validation failed for {symbol}")
            raise
        except Exception as e:
            logger.log_error(e, f"Stop-limit order placement failed for {symbol}")
            raise
    
    def place_take_profit_order(self, 
                               symbol: str, 
                               side: str, 
                               quantity: float,
                               price: float,
                               time_in_force: str = "GTC",
                               reduce_only: bool = True) -> Dict[str, Any]:
        """Place a take profit order"""
        return self.place_limit_order(symbol, side, quantity, price, time_in_force, reduce_only)
    
    def place_stop_loss_order(self, 
                             symbol: str, 
                             side: str, 
                             quantity: float,
                             price: float,
                             time_in_force: str = "GTC",
                             reduce_only: bool = True) -> Dict[str, Any]:
        """Place a stop loss order"""
        return self.place_limit_order(symbol, side, quantity, price, time_in_force, reduce_only)

class LimitOrderManager:
    """Manager for limit order operations"""
    
    def __init__(self, client: BinanceClient):
        self.client = client
        self.limit_order = LimitOrder(client)
    
    def place_bracket_orders(self, 
                           symbol: str, 
                           side: str, 
                           quantity: float,
                           entry_price: float,
                           take_profit_price: float,
                           stop_loss_price: float) -> Dict[str, Any]:
        """
        Place bracket orders (entry + take profit + stop loss)
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            entry_price: Entry limit price
            take_profit_price: Take profit price
            stop_loss_price: Stop loss price
        """
        try:
            orders = {}
            
            # Place entry order
            entry_order = self.limit_order.place_limit_order(
                symbol, side, quantity, entry_price
            )
            orders['entry'] = entry_order
            
            # Determine opposite side for TP/SL
            opposite_side = SIDE_TYPES["SELL"] if side == SIDE_TYPES["BUY"] else SIDE_TYPES["BUY"]
            
            # Place take profit order
            tp_order = self.limit_order.place_take_profit_order(
                symbol, opposite_side, quantity, take_profit_price
            )
            orders['take_profit'] = tp_order
            
            # Place stop loss order
            sl_order = self.limit_order.place_stop_loss_order(
                symbol, opposite_side, quantity, stop_loss_price
            )
            orders['stop_loss'] = sl_order
            
            logger.logger.info(f"Bracket orders placed for {symbol}: Entry={entry_order.get('orderId')}, "
                             f"TP={tp_order.get('orderId')}, SL={sl_order.get('orderId')}")
            
            return orders
            
        except Exception as e:
            logger.log_error(e, f"Bracket orders placement failed for {symbol}")
            raise
    
    def place_scaled_orders(self, 
                          symbol: str, 
                          side: str, 
                          total_quantity: float,
                          price_levels: list,
                          quantities: list) -> list:
        """
        Place scaled orders at different price levels
        
        Args:
            symbol: Trading symbol
            side: Order side
            total_quantity: Total quantity to distribute
            price_levels: List of price levels
            quantities: List of quantities for each level
        """
        try:
            if len(price_levels) != len(quantities):
                raise ValueError("Price levels and quantities must have the same length")
            
            if sum(quantities) != total_quantity:
                raise ValueError("Sum of quantities must equal total quantity")
            
            orders = []
            
            for price, quantity in zip(price_levels, quantities):
                order = self.limit_order.place_limit_order(symbol, side, quantity, price)
                orders.append(order)
                
                logger.logger.info(f"Scaled order placed: {symbol} {side} {quantity} @ {price}")
            
            return orders
            
        except Exception as e:
            logger.log_error(e, f"Scaled orders placement failed for {symbol}")
            raise
    
    def place_iceberg_order(self, 
                          symbol: str, 
                          side: str, 
                          total_quantity: float,
                          price: float,
                          iceberg_qty: float) -> Dict[str, Any]:
        """
        Place an iceberg order (large order split into smaller visible parts)
        
        Args:
            symbol: Trading symbol
            side: Order side
            total_quantity: Total order quantity
            price: Limit price
            iceberg_qty: Visible quantity for each part
        """
        try:
            # Validate inputs
            validator.validate_symbol(symbol)
            validator.validate_side(side)
            total_quantity = validator.validate_quantity(total_quantity)
            price = validator.validate_price(price)
            iceberg_qty = validator.validate_quantity(iceberg_qty)
            
            if iceberg_qty >= total_quantity:
                raise ValueError("Iceberg quantity must be less than total quantity")
            
            # Prepare order parameters
            order_params = {
                "symbol": symbol.upper(),
                "side": side.upper(),
                "type": ORDER_TYPES["LIMIT"],
                "quantity": total_quantity,
                "price": price,
                "timeInForce": TIME_IN_FORCE["GTC"],
                "icebergQty": iceberg_qty
            }
            
            # Log the order attempt
            logger.logger.info(f"Placing iceberg order: {symbol} {side} {total_quantity} @ {price} (iceberg: {iceberg_qty})")
            
            # Place the order
            response = self.client.place_order(order_params)
            
            # Log successful order placement
            logger.log_order_placed(order_params, response.get('orderId', 'unknown'))
            
            return response
            
        except Exception as e:
            logger.log_error(e, f"Iceberg order placement failed for {symbol}")
            raise
    
    def monitor_order_fill(self, symbol: str, order_id: str, timeout: int = 3600) -> Dict[str, Any]:
        """
        Monitor an order until it's filled or timeout
        
        Args:
            symbol: Trading symbol
            order_id: Order ID to monitor
            timeout: Timeout in seconds (default: 1 hour)
        """
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                order_status = self.client.get_order(symbol, order_id)
                status = order_status.get('status')
                
                if status == 'FILLED':
                    logger.logger.info(f"Order {order_id} filled successfully")
                    logger.log_order_executed(order_id, order_status)
                    return order_status
                elif status == 'CANCELED':
                    logger.logger.info(f"Order {order_id} was canceled")
                    logger.log_order_cancelled(order_id, "Order was canceled")
                    return order_status
                elif status == 'REJECTED':
                    logger.logger.error(f"Order {order_id} was rejected")
                    return order_status
                
                # Wait before checking again
                time.sleep(5)
            
            logger.logger.warning(f"Order {order_id} monitoring timed out")
            return self.client.get_order(symbol, order_id)
            
        except Exception as e:
            logger.log_error(e, f"Order monitoring failed for {order_id}")
            raise 