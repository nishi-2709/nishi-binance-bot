"""
OCO (One-Cancels-the-Other) Orders module for Binance Futures Order Bot
Handles OCO order placement, execution, and management
"""

import time
from typing import Dict, Any, Optional
from src.config import config, SIDE_TYPES, TIME_IN_FORCE
from src.logger import logger
from src.validator import validator, ValidationError
from src.api_client import BinanceClient

class OCOOrder:
    """OCO (One-Cancels-the-Other) order implementation"""
    
    def __init__(self, client: BinanceClient):
        self.client = client
    
    def place_oco_order(self, 
                       symbol: str, 
                       side: str, 
                       quantity: float,
                       price: float,
                       stop_price: float,
                       stop_limit_price: float,
                       stop_limit_time_in_force: str = "GTC",
                       list_client_order_id: Optional[str] = None,
                       limit_client_order_id: Optional[str] = None,
                       stop_client_order_id: Optional[str] = None,
                       limit_iceberg_qty: Optional[float] = None,
                       stop_iceberg_qty: Optional[float] = None,
                       stop_limit_iceberg_qty: Optional[float] = None,
                       limit_strategy_id: Optional[int] = None,
                       stop_strategy_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Place an OCO (One-Cancels-the-Other) order
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            price: Limit price (take profit)
            stop_price: Stop price (stop loss trigger)
            stop_limit_price: Stop limit price (stop loss execution)
            stop_limit_time_in_force: Time in force for stop limit order
            list_client_order_id: Client order ID for the OCO list
            limit_client_order_id: Client order ID for the limit order
            stop_client_order_id: Client order ID for the stop order
            limit_iceberg_qty: Iceberg quantity for limit order
            stop_iceberg_qty: Iceberg quantity for stop order
            stop_limit_iceberg_qty: Iceberg quantity for stop limit order
            limit_strategy_id: Strategy ID for limit order
            stop_strategy_id: Strategy ID for stop order
            
        Returns:
            OCO order response from Binance API
        """
        try:
            # Validate inputs
            validator.validate_symbol(symbol)
            validator.validate_side(side)
            quantity = validator.validate_quantity(quantity)
            price = validator.validate_price(price)
            stop_price = validator.validate_stop_price(stop_price)
            stop_limit_price = validator.validate_price(stop_limit_price)
            validator.validate_time_in_force(stop_limit_time_in_force)
            
            # Prepare OCO order parameters
            oco_params = {
                "symbol": symbol.upper(),
                "side": side.upper(),
                "quantity": quantity,
                "price": price,
                "stopPrice": stop_price,
                "stopLimitPrice": stop_limit_price,
                "stopLimitTimeInForce": stop_limit_time_in_force.upper()
            }
            
            # Add optional parameters if provided
            if list_client_order_id:
                oco_params["listClientOrderId"] = list_client_order_id
            if limit_client_order_id:
                oco_params["limitClientOrderId"] = limit_client_order_id
            if stop_client_order_id:
                oco_params["stopClientOrderId"] = stop_client_order_id
            if limit_iceberg_qty:
                oco_params["limitIcebergQty"] = limit_iceberg_qty
            if stop_iceberg_qty:
                oco_params["stopIcebergQty"] = stop_iceberg_qty
            if stop_limit_iceberg_qty:
                oco_params["stopLimitIcebergQty"] = stop_limit_iceberg_qty
            if limit_strategy_id:
                oco_params["limitStrategyId"] = limit_strategy_id
            if stop_strategy_id:
                oco_params["stopStrategyId"] = stop_strategy_id
            
            # Log the OCO order attempt
            logger.logger.info(f"Placing OCO order: {symbol} {side} {quantity} @ {price} (stop: {stop_price})")
            
            # Place the OCO order
            response = self.client.place_oco_order(oco_params)
            
            # Log successful OCO order placement
            logger.log_order_placed(oco_params, response.get('orderListId', 'unknown'))
            
            return response
            
        except ValidationError as e:
            logger.log_error(e, f"OCO order validation failed for {symbol}")
            raise
        except Exception as e:
            logger.log_error(e, f"OCO order placement failed for {symbol}")
            raise
    
    def place_oco_buy_order(self, 
                           symbol: str, 
                           quantity: float,
                           take_profit_price: float,
                           stop_loss_price: float,
                           stop_limit_price: float,
                           **kwargs) -> Dict[str, Any]:
        """Place an OCO buy order (take profit + stop loss)"""
        return self.place_oco_order(
            symbol, SIDE_TYPES["BUY"], quantity, 
            take_profit_price, stop_loss_price, stop_limit_price, **kwargs
        )
    
    def place_oco_sell_order(self, 
                            symbol: str, 
                            quantity: float,
                            take_profit_price: float,
                            stop_loss_price: float,
                            stop_limit_price: float,
                            **kwargs) -> Dict[str, Any]:
        """Place an OCO sell order (take profit + stop loss)"""
        return self.place_oco_order(
            symbol, SIDE_TYPES["SELL"], quantity, 
            take_profit_price, stop_loss_price, stop_limit_price, **kwargs
        )
    
    def place_oco_order_by_quote_quantity(self,
                                        symbol: str,
                                        side: str,
                                        quote_quantity: float,
                                        take_profit_price: float,
                                        stop_loss_price: float,
                                        stop_limit_price: float,
                                        **kwargs) -> Dict[str, Any]:
        """
        Place an OCO order using quote quantity (USDT amount)
        
        Args:
            symbol: Trading symbol
            side: Order side
            quote_quantity: Amount in quote currency (USDT)
            take_profit_price: Take profit price
            stop_loss_price: Stop loss trigger price
            stop_limit_price: Stop loss execution price
            **kwargs: Additional parameters
        """
        try:
            # Validate inputs
            validator.validate_symbol(symbol)
            validator.validate_side(side)
            quote_quantity = validator.validate_quantity(quote_quantity)
            take_profit_price = validator.validate_price(take_profit_price)
            stop_loss_price = validator.validate_stop_price(stop_loss_price)
            stop_limit_price = validator.validate_price(stop_limit_price)
            
            # Calculate quantity based on quote amount and take profit price
            quantity = quote_quantity / take_profit_price
            
            # Place the OCO order
            return self.place_oco_order(
                symbol, side, quantity, 
                take_profit_price, stop_loss_price, stop_limit_price, **kwargs
            )
            
        except Exception as e:
            logger.log_error(e, f"OCO order by quote quantity failed for {symbol}")
            raise
    
    def place_oco_buy_by_quote(self, 
                              symbol: str, 
                              usdt_amount: float,
                              take_profit_price: float,
                              stop_loss_price: float,
                              stop_limit_price: float,
                              **kwargs) -> Dict[str, Any]:
        """Place an OCO buy order using USDT amount"""
        return self.place_oco_order_by_quote_quantity(
            symbol, SIDE_TYPES["BUY"], usdt_amount,
            take_profit_price, stop_loss_price, stop_limit_price, **kwargs
        )
    
    def place_oco_sell_by_quote(self, 
                               symbol: str, 
                               usdt_amount: float,
                               take_profit_price: float,
                               stop_loss_price: float,
                               stop_limit_price: float,
                               **kwargs) -> Dict[str, Any]:
        """Place an OCO sell order using USDT amount"""
        return self.place_oco_order_by_quote_quantity(
            symbol, SIDE_TYPES["SELL"], usdt_amount,
            take_profit_price, stop_loss_price, stop_limit_price, **kwargs
        )

class OCOOrderManager:
    """Manager for OCO order operations"""
    
    def __init__(self, client: BinanceClient):
        self.client = client
        self.oco_order = OCOOrder(client)
    
    def place_trailing_stop_oco(self, 
                               symbol: str, 
                               side: str, 
                               quantity: float,
                               take_profit_percentage: float,
                               stop_loss_percentage: float,
                               current_price: float) -> Dict[str, Any]:
        """
        Place an OCO order with trailing stop based on percentages
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            take_profit_percentage: Take profit percentage (e.g., 0.05 for 5%)
            stop_loss_percentage: Stop loss percentage (e.g., 0.03 for 3%)
            current_price: Current market price
        """
        try:
            # Calculate prices based on percentages
            if side == SIDE_TYPES["BUY"]:
                take_profit_price = current_price * (1 + take_profit_percentage)
                stop_loss_price = current_price * (1 - stop_loss_percentage)
                stop_limit_price = stop_loss_price * 0.99  # Slightly below stop price
            else:
                take_profit_price = current_price * (1 - take_profit_percentage)
                stop_loss_price = current_price * (1 + stop_loss_percentage)
                stop_limit_price = stop_loss_price * 1.01  # Slightly above stop price
            
            # Place OCO order
            return self.oco_order.place_oco_order(
                symbol, side, quantity,
                take_profit_price, stop_loss_price, stop_limit_price
            )
            
        except Exception as e:
            logger.log_error(e, f"Trailing stop OCO order failed for {symbol}")
            raise
    
    def place_risk_reward_oco(self, 
                             symbol: str, 
                             side: str, 
                             quantity: float,
                             risk_reward_ratio: float,
                             entry_price: float,
                             stop_loss_price: float) -> Dict[str, Any]:
        """
        Place an OCO order with specific risk-reward ratio
        
        Args:
            symbol: Trading symbol
            side: Order side
            quantity: Order quantity
            risk_reward_ratio: Risk-reward ratio (e.g., 2.0 for 1:2)
            entry_price: Entry price
            stop_loss_price: Stop loss price
        """
        try:
            # Calculate take profit based on risk-reward ratio
            if side == SIDE_TYPES["BUY"]:
                risk = entry_price - stop_loss_price
                take_profit_price = entry_price + (risk * risk_reward_ratio)
            else:
                risk = stop_loss_price - entry_price
                take_profit_price = entry_price - (risk * risk_reward_ratio)
            
            # Calculate stop limit price
            if side == SIDE_TYPES["BUY"]:
                stop_limit_price = stop_loss_price * 0.99
            else:
                stop_limit_price = stop_loss_price * 1.01
            
            # Place OCO order
            return self.oco_order.place_oco_order(
                symbol, side, quantity,
                take_profit_price, stop_loss_price, stop_limit_price
            )
            
        except Exception as e:
            logger.log_error(e, f"Risk-reward OCO order failed for {symbol}")
            raise
    
    def place_multiple_oco_orders(self, 
                                symbol: str, 
                                side: str, 
                                total_quantity: float,
                                price_levels: list,
                                take_profit_percentages: list,
                                stop_loss_percentages: list) -> list:
        """
        Place multiple OCO orders at different price levels
        
        Args:
            symbol: Trading symbol
            side: Order side
            total_quantity: Total quantity to distribute
            price_levels: List of price levels
            take_profit_percentages: List of take profit percentages
            stop_loss_percentages: List of stop loss percentages
        """
        try:
            if len(price_levels) != len(take_profit_percentages) or len(price_levels) != len(stop_loss_percentages):
                raise ValueError("All lists must have the same length")
            
            quantity_per_order = total_quantity / len(price_levels)
            orders = []
            
            for i, (price, tp_pct, sl_pct) in enumerate(zip(price_levels, take_profit_percentages, stop_loss_percentages)):
                # Calculate take profit and stop loss prices
                if side == SIDE_TYPES["BUY"]:
                    take_profit_price = price * (1 + tp_pct)
                    stop_loss_price = price * (1 - sl_pct)
                    stop_limit_price = stop_loss_price * 0.99
                else:
                    take_profit_price = price * (1 - tp_pct)
                    stop_loss_price = price * (1 + sl_pct)
                    stop_limit_price = stop_loss_price * 1.01
                
                # Place OCO order
                order = self.oco_order.place_oco_order(
                    symbol, side, quantity_per_order,
                    take_profit_price, stop_loss_price, stop_limit_price
                )
                orders.append(order)
                
                logger.logger.info(f"Multiple OCO order {i+1} placed: {order.get('orderListId')}")
            
            return orders
            
        except Exception as e:
            logger.log_error(e, f"Multiple OCO orders failed for {symbol}")
            raise 