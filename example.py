#!/usr/bin/env python3
"""
Example script demonstrating the Binance Futures Order Bot functionality
This script shows basic usage examples for different order types
"""

import os
import sys
from src.api_client import BinanceClient
from src.market_orders import MarketOrderManager
from src.limit_orders import LimitOrderManager
from src.advanced.oco import OCOOrderManager
from src.advanced.twap import TWAPManager
from src.advanced.grid_orders import GridOrderManager
from src.logger import logger

def main():
    """Main example function"""
    print("=== Binance Futures Order Bot - Example Usage ===\n")
    
    try:
        # Initialize the bot
        client = BinanceClient()
        
        # Test connection
        print("1. Testing API connection...")
        account_info = client.get_account_info()
        print(f"   ✓ Connected successfully! Account type: {account_info.get('accountType', 'Unknown')}")
        
        # Get current BTC price
        print("\n2. Getting current BTC price...")
        btc_price = client.get_symbol_price_ticker("BTCUSDT")
        print(f"   ✓ BTC/USDT: ${float(btc_price['price']):,.2f}")
        
        # Example 1: Market Order
        print("\n3. Market Order Example:")
        print("   python src/main.py market-buy BTCUSDT 0.001")
        print("   python src/main.py market-sell BTCUSDT 0.001")
        
        # Example 2: Limit Order
        print("\n4. Limit Order Example:")
        current_price = float(btc_price['price'])
        limit_buy_price = current_price * 0.99  # 1% below current price
        limit_sell_price = current_price * 1.01  # 1% above current price
        print(f"   python src/main.py limit-buy BTCUSDT 0.001 {limit_buy_price:.2f}")
        print(f"   python src/main.py limit-sell BTCUSDT 0.001 {limit_sell_price:.2f}")
        
        # Example 3: Stop-Limit Order
        print("\n5. Stop-Limit Order Example:")
        stop_price = current_price * 0.98  # 2% below current price
        limit_price = stop_price * 0.99  # Slightly below stop price
        print(f"   python src/main.py stop-limit-buy BTCUSDT 0.001 {limit_price:.2f} {stop_price:.2f}")
        
        # Example 4: OCO Order
        print("\n6. OCO Order Example:")
        take_profit = current_price * 1.05  # 5% take profit
        stop_loss = current_price * 0.95   # 5% stop loss
        stop_limit = stop_loss * 0.99      # Slightly below stop loss
        print(f"   python src/main.py oco-buy BTCUSDT 0.001 {take_profit:.2f} {stop_loss:.2f} {stop_limit:.2f}")
        
        # Example 5: TWAP Order
        print("\n7. TWAP Order Example:")
        print("   python src/main.py twap-buy BTCUSDT 0.01 3600 10")
        print("   # Executes 0.01 BTC over 1 hour in 10 chunks")
        
        # Example 6: Grid Order
        print("\n8. Grid Order Example:")
        upper_price = current_price * 1.05
        lower_price = current_price * 0.95
        print(f"   python src/main.py grid-create BTCUSDT {upper_price:.2f} {lower_price:.2f} 10 1000")
        print("   # Creates 10-level grid between 95% and 105% of current price")
        
        # Example 7: Utility Commands
        print("\n9. Utility Commands:")
        print("   python src/main.py account          # Get account info")
        print("   python src/main.py balance          # Get balance")
        print("   python src/main.py positions        # Get positions")
        print("   python src/main.py open-orders      # Get open orders")
        print("   python src/main.py price BTCUSDT    # Get current price")
        
        print("\n=== Example completed successfully! ===")
        print("\nNote: These are examples only. No actual orders were placed.")
        print("To place real orders, use the CLI commands shown above.")
        
    except Exception as e:
        logger.log_error(e, "Example script failed")
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. Set up your .env file with API keys")
        print("2. Installed dependencies: pip install -r requirements.txt")
        print("3. Have a valid Binance Futures account")
        sys.exit(1)

if __name__ == "__main__":
    main() 