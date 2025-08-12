"""
Main CLI interface for Binance Futures Order Bot
Provides command-line interface for all order types and strategies
"""

import argparse
import sys
import os
from typing import Dict, Any
from src.config import config
from src.logger import logger
from src.api_client import BinanceClient
from src.market_orders import MarketOrder, MarketOrderManager
from src.limit_orders import LimitOrder, LimitOrderManager
from src.advanced.oco import OCOOrder, OCOOrderManager
from src.advanced.twap import TWAPOrder, TWAPManager
from src.advanced.grid_orders import GridOrder, GridOrderManager

class BinanceBotCLI:
    """Main CLI class for the Binance Futures Order Bot"""
    
    def __init__(self):
        self.client = BinanceClient()
        self.market_manager = MarketOrderManager(self.client)
        self.limit_manager = LimitOrderManager(self.client)
        self.oco_manager = OCOOrderManager(self.client)
        self.twap_manager = TWAPManager(self.client)
        self.grid_manager = GridOrderManager(self.client)
    
    def run(self):
        """Main CLI entry point"""
        parser = argparse.ArgumentParser(
            description="Binance Futures Order Bot - CLI Trading Interface",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Market Orders
  python src/main.py market-buy BTCUSDT 0.01
  python src/main.py market-sell BTCUSDT 0.01
  python src/main.py market-buy-quote BTCUSDT 100
  
  # Limit Orders
  python src/main.py limit-buy BTCUSDT 0.01 50000
  python src/main.py limit-sell BTCUSDT 0.01 55000
  
  # Stop-Limit Orders
  python src/main.py stop-limit-buy BTCUSDT 0.01 50000 49000
  
  # OCO Orders
  python src/main.py oco-buy BTCUSDT 0.01 55000 45000 44000
  
  # TWAP Orders
  python src/main.py twap-buy BTCUSDT 0.1 3600 10
  
  # Grid Orders
  python src/main.py grid-create BTCUSDT 55000 45000 10 1000
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Market Orders
        self._add_market_order_parsers(subparsers)
        
        # Limit Orders
        self._add_limit_order_parsers(subparsers)
        
        # Advanced Orders
        self._add_advanced_order_parsers(subparsers)
        
        # Utility Commands
        self._add_utility_parsers(subparsers)
        
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        try:
            # Execute the command
            command_method = getattr(self, f"cmd_{args.command.replace('-', '_')}")
            command_method(args)
        except Exception as e:
            logger.log_error(e, f"Command execution failed: {args.command}")
            print(f"Error: {e}")
            sys.exit(1)
    
    def _add_market_order_parsers(self, subparsers):
        """Add market order command parsers"""
        
        # Market Buy
        market_buy = subparsers.add_parser('market-buy', help='Place a market buy order')
        market_buy.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
        market_buy.add_argument('quantity', type=float, help='Order quantity')
        market_buy.add_argument('--time-in-force', default='IOC', choices=['IOC', 'FOK', 'GTC'], 
                               help='Time in force (default: IOC)')
        
        # Market Sell
        market_sell = subparsers.add_parser('market-sell', help='Place a market sell order')
        market_sell.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
        market_sell.add_argument('quantity', type=float, help='Order quantity')
        market_sell.add_argument('--time-in-force', default='IOC', choices=['IOC', 'FOK', 'GTC'], 
                                help='Time in force (default: IOC)')
        
        # Market Buy by Quote
        market_buy_quote = subparsers.add_parser('market-buy-quote', help='Place a market buy order using USDT amount')
        market_buy_quote.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
        market_buy_quote.add_argument('usdt_amount', type=float, help='USDT amount to spend')
        
        # Market Sell by Quote
        market_sell_quote = subparsers.add_parser('market-sell-quote', help='Place a market sell order using USDT amount')
        market_sell_quote.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
        market_sell_quote.add_argument('usdt_amount', type=float, help='USDT amount to receive')
    
    def _add_limit_order_parsers(self, subparsers):
        """Add limit order command parsers"""
        
        # Limit Buy
        limit_buy = subparsers.add_parser('limit-buy', help='Place a limit buy order')
        limit_buy.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
        limit_buy.add_argument('quantity', type=float, help='Order quantity')
        limit_buy.add_argument('price', type=float, help='Limit price')
        limit_buy.add_argument('--time-in-force', default='GTC', choices=['GTC', 'IOC', 'FOK'], 
                              help='Time in force (default: GTC)')
        
        # Limit Sell
        limit_sell = subparsers.add_parser('limit-sell', help='Place a limit sell order')
        limit_sell.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
        limit_sell.add_argument('quantity', type=float, help='Order quantity')
        limit_sell.add_argument('price', type=float, help='Limit price')
        limit_sell.add_argument('--time-in-force', default='GTC', choices=['GTC', 'IOC', 'FOK'], 
                               help='Time in force (default: GTC)')
        
        # Stop-Limit Buy
        stop_limit_buy = subparsers.add_parser('stop-limit-buy', help='Place a stop-limit buy order')
        stop_limit_buy.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
        stop_limit_buy.add_argument('quantity', type=float, help='Order quantity')
        stop_limit_buy.add_argument('price', type=float, help='Limit price')
        stop_limit_buy.add_argument('stop_price', type=float, help='Stop price')
        
        # Stop-Limit Sell
        stop_limit_sell = subparsers.add_parser('stop-limit-sell', help='Place a stop-limit sell order')
        stop_limit_sell.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
        stop_limit_sell.add_argument('quantity', type=float, help='Order quantity')
        stop_limit_sell.add_argument('price', type=float, help='Limit price')
        stop_limit_sell.add_argument('stop_price', type=float, help='Stop price')
    
    def _add_advanced_order_parsers(self, subparsers):
        """Add advanced order command parsers"""
        
        # OCO Orders
        oco_buy = subparsers.add_parser('oco-buy', help='Place an OCO buy order')
        oco_buy.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
        oco_buy.add_argument('quantity', type=float, help='Order quantity')
        oco_buy.add_argument('take_profit_price', type=float, help='Take profit price')
        oco_buy.add_argument('stop_loss_price', type=float, help='Stop loss trigger price')
        oco_buy.add_argument('stop_limit_price', type=float, help='Stop loss execution price')
        
        oco_sell = subparsers.add_parser('oco-sell', help='Place an OCO sell order')
        oco_sell.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
        oco_sell.add_argument('quantity', type=float, help='Order quantity')
        oco_sell.add_argument('take_profit_price', type=float, help='Take profit price')
        oco_sell.add_argument('stop_loss_price', type=float, help='Stop loss trigger price')
        oco_sell.add_argument('stop_limit_price', type=float, help='Stop loss execution price')
        
        # TWAP Orders
        twap_buy = subparsers.add_parser('twap-buy', help='Execute TWAP buy strategy')
        twap_buy.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
        twap_buy.add_argument('total_quantity', type=float, help='Total quantity to buy')
        twap_buy.add_argument('duration_seconds', type=int, help='Duration in seconds')
        twap_buy.add_argument('num_chunks', type=int, help='Number of chunks')
        twap_buy.add_argument('--use-limit-orders', action='store_true', help='Use limit orders instead of market orders')
        
        twap_sell = subparsers.add_parser('twap-sell', help='Execute TWAP sell strategy')
        twap_sell.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
        twap_sell.add_argument('total_quantity', type=float, help='Total quantity to sell')
        twap_sell.add_argument('duration_seconds', type=int, help='Duration in seconds')
        twap_sell.add_argument('num_chunks', type=int, help='Number of chunks')
        twap_sell.add_argument('--use-limit-orders', action='store_true', help='Use limit orders instead of market orders')
        
        # Grid Orders
        grid_create = subparsers.add_parser('grid-create', help='Create a grid trading strategy')
        grid_create.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
        grid_create.add_argument('upper_price', type=float, help='Upper price boundary')
        grid_create.add_argument('lower_price', type=float, help='Lower price boundary')
        grid_create.add_argument('grid_number', type=int, help='Number of grid levels')
        grid_create.add_argument('total_investment', type=float, help='Total investment in USDT')
        grid_create.add_argument('--grid-type', choices=['arithmetic', 'geometric'], default='arithmetic',
                                help='Grid type (default: arithmetic)')
    
    def _add_utility_parsers(self, subparsers):
        """Add utility command parsers"""
        
        # Account Info
        account = subparsers.add_parser('account', help='Get account information')
        
        # Balance
        balance = subparsers.add_parser('balance', help='Get account balance')
        
        # Positions
        positions = subparsers.add_parser('positions', help='Get position information')
        positions.add_argument('--symbol', help='Specific symbol (optional)')
        
        # Open Orders
        open_orders = subparsers.add_parser('open-orders', help='Get open orders')
        open_orders.add_argument('--symbol', help='Specific symbol (optional)')
        
        # Cancel Order
        cancel_order = subparsers.add_parser('cancel-order', help='Cancel a specific order')
        cancel_order.add_argument('symbol', help='Trading symbol')
        cancel_order.add_argument('order_id', help='Order ID to cancel')
        
        # Cancel All Orders
        cancel_all = subparsers.add_parser('cancel-all', help='Cancel all open orders for a symbol')
        cancel_all.add_argument('symbol', help='Trading symbol')
        
        # Price
        price = subparsers.add_parser('price', help='Get current price for a symbol')
        price.add_argument('symbol', help='Trading symbol')
    
    # Market Order Commands
    def cmd_market_buy(self, args):
        """Execute market buy command"""
        result = self.market_manager.market_order.place_market_buy_order(
            args.symbol, args.quantity, time_in_force=args.time_in_force
        )
        print(f"Market buy order placed: {result}")
    
    def cmd_market_sell(self, args):
        """Execute market sell command"""
        result = self.market_manager.market_order.place_market_sell_order(
            args.symbol, args.quantity, time_in_force=args.time_in_force
        )
        print(f"Market sell order placed: {result}")
    
    def cmd_market_buy_quote(self, args):
        """Execute market buy by quote command"""
        result = self.market_manager.market_order.place_market_buy_by_quote(
            args.symbol, args.usdt_amount
        )
        print(f"Market buy order placed: {result}")
    
    def cmd_market_sell_quote(self, args):
        """Execute market sell by quote command"""
        result = self.market_manager.market_order.place_market_sell_by_quote(
            args.symbol, args.usdt_amount
        )
        print(f"Market sell order placed: {result}")
    
    # Limit Order Commands
    def cmd_limit_buy(self, args):
        """Execute limit buy command"""
        result = self.limit_manager.limit_order.place_limit_buy_order(
            args.symbol, args.quantity, args.price, time_in_force=args.time_in_force
        )
        print(f"Limit buy order placed: {result}")
    
    def cmd_limit_sell(self, args):
        """Execute limit sell command"""
        result = self.limit_manager.limit_order.place_limit_sell_order(
            args.symbol, args.quantity, args.price, time_in_force=args.time_in_force
        )
        print(f"Limit sell order placed: {result}")
    
    def cmd_stop_limit_buy(self, args):
        """Execute stop-limit buy command"""
        result = self.limit_manager.limit_order.place_stop_limit_order(
            args.symbol, 'BUY', args.quantity, args.price, args.stop_price
        )
        print(f"Stop-limit buy order placed: {result}")
    
    def cmd_stop_limit_sell(self, args):
        """Execute stop-limit sell command"""
        result = self.limit_manager.limit_order.place_stop_limit_order(
            args.symbol, 'SELL', args.quantity, args.price, args.stop_price
        )
        print(f"Stop-limit sell order placed: {result}")
    
    # Advanced Order Commands
    def cmd_oco_buy(self, args):
        """Execute OCO buy command"""
        result = self.oco_manager.oco_order.place_oco_buy_order(
            args.symbol, args.quantity, args.take_profit_price, 
            args.stop_loss_price, args.stop_limit_price
        )
        print(f"OCO buy order placed: {result}")
    
    def cmd_oco_sell(self, args):
        """Execute OCO sell command"""
        result = self.oco_manager.oco_order.place_oco_sell_order(
            args.symbol, args.quantity, args.take_profit_price, 
            args.stop_loss_price, args.stop_limit_price
        )
        print(f"OCO sell order placed: {result}")
    
    def cmd_twap_buy(self, args):
        """Execute TWAP buy command"""
        result = self.twap_manager.twap_order.execute_twap_strategy(
            args.symbol, 'BUY', args.total_quantity, args.duration_seconds, 
            args.num_chunks, use_limit_orders=args.use_limit_orders
        )
        print(f"TWAP buy strategy executed: {result}")
    
    def cmd_twap_sell(self, args):
        """Execute TWAP sell command"""
        result = self.twap_manager.twap_order.execute_twap_strategy(
            args.symbol, 'SELL', args.total_quantity, args.duration_seconds, 
            args.num_chunks, use_limit_orders=args.use_limit_orders
        )
        print(f"TWAP sell strategy executed: {result}")
    
    def cmd_grid_create(self, args):
        """Execute grid create command"""
        result = self.grid_manager.grid_order.create_grid_strategy(
            args.symbol, args.upper_price, args.lower_price, 
            args.grid_number, args.total_investment, args.grid_type
        )
        print(f"Grid strategy created: {result}")
    
    # Utility Commands
    def cmd_account(self, args):
        """Get account information"""
        result = self.client.get_account_info()
        print(f"Account Info: {result}")
    
    def cmd_balance(self, args):
        """Get account balance"""
        result = self.client.get_balance()
        print(f"Balance: {result}")
    
    def cmd_positions(self, args):
        """Get position information"""
        result = self.client.get_position_info(args.symbol if hasattr(args, 'symbol') else None)
        print(f"Positions: {result}")
    
    def cmd_open_orders(self, args):
        """Get open orders"""
        result = self.client.get_open_orders(args.symbol if hasattr(args, 'symbol') else None)
        print(f"Open Orders: {result}")
    
    def cmd_cancel_order(self, args):
        """Cancel a specific order"""
        result = self.client.cancel_order(args.symbol, args.order_id)
        print(f"Order cancelled: {result}")
    
    def cmd_cancel_all(self, args):
        """Cancel all open orders for a symbol"""
        result = self.client.cancel_all_orders(args.symbol)
        print(f"All orders cancelled: {result}")
    
    def cmd_price(self, args):
        """Get current price for a symbol"""
        result = self.client.get_symbol_price_ticker(args.symbol)
        print(f"Current price for {args.symbol}: {result['price']}")

def main():
    """Main entry point"""
    try:
        cli = BinanceBotCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.log_error(e, "CLI execution failed")
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 