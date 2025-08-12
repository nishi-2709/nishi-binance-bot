# Nishi Binance Futures Order Bot

A comprehensive CLI-based trading bot for Binance USDT-M Futures that supports multiple order types with robust logging, validation, and documentation.

## Features

### Core Orders (Mandatory)
- **Market Orders**: Immediate execution at current market price
- **Limit Orders**: Execution at specified price or better
- **Stop-Limit Orders**: Trigger limit orders when stop price is hit

### Advanced Orders (Bonus)
- **OCO Orders**: One-Cancels-the-Other orders for take-profit and stop-loss
- **TWAP Orders**: Time-Weighted Average Price execution strategy
- **Grid Orders**: Automated buy-low/sell-high within a price range

### Additional Features
- **Comprehensive Validation**: Input validation for all parameters
- **Structured Logging**: Detailed logging with timestamps and error traces
- **Error Handling**: Robust error handling and recovery
- **CLI Interface**: Easy-to-use command-line interface
- **Configuration Management**: Environment-based configuration

## Project Structure

```
[project_root]/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── logger.py              # Structured logging
│   ├── validator.py           # Input validation
│   ├── api_client.py          # Binance API client
│   ├── market_orders.py       # Market order implementation
│   ├── limit_orders.py        # Limit order implementation
│   ├── main.py                # CLI interface
│   └── advanced/
│       ├── __init__.py
│       ├── oco.py             # OCO orders
│       ├── twap.py            # TWAP strategy
│       └── grid_orders.py     # Grid trading
├── logs/                      # Log files (auto-created)
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- Binance Futures account with API access
- API key and secret from Binance

### 2. Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/nishi-binance-bot.git
cd nishi-binance-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create a .env file in the project root
echo "BINANCE_API_KEY=your_api_key_here" > .env
echo "BINANCE_API_SECRET=your_api_secret_here" >> .env
echo "BINANCE_TESTNET=true" >> .env  # Set to false for live trading
```

### 3. API Setup

1. Go to [Binance Futures](https://www.binance.com/en/futures)
2. Create an account and complete KYC if required
3. Go to API Management
4. Create a new API key with Futures trading permissions
5. Add your IP address to the whitelist
6. Copy the API key and secret to your `.env` file

**⚠️ Important Security Notes:**
- Never share your API keys
- Use testnet for testing (`BINANCE_TESTNET=true`)
- Enable IP whitelist in Binance
- Use minimal required permissions

## Usage Examples

### Market Orders

```bash
# Market buy order
python src/main.py market-buy BTCUSDT 0.01

# Market sell order
python src/main.py market-sell BTCUSDT 0.01

# Market buy using USDT amount
python src/main.py market-buy-quote BTCUSDT 100

# Market sell using USDT amount
python src/main.py market-sell-quote BTCUSDT 100
```

### Limit Orders

```bash
# Limit buy order
python src/main.py limit-buy BTCUSDT 0.01 50000

# Limit sell order
python src/main.py limit-sell BTCUSDT 0.01 55000

# Stop-limit buy order
python src/main.py stop-limit-buy BTCUSDT 0.01 50000 49000

# Stop-limit sell order
python src/main.py stop-limit-sell BTCUSDT 0.01 55000 56000
```

### Advanced Orders

#### OCO Orders (One-Cancels-the-Other)
```bash
# OCO buy order (take profit + stop loss)
python src/main.py oco-buy BTCUSDT 0.01 55000 45000 44000

# OCO sell order (take profit + stop loss)
python src/main.py oco-sell BTCUSDT 0.01 45000 55000 56000
```

#### TWAP Orders (Time-Weighted Average Price)
```bash
# TWAP buy strategy (0.1 BTC over 1 hour in 10 chunks)
python src/main.py twap-buy BTCUSDT 0.1 3600 10

# TWAP sell strategy with limit orders
python src/main.py twap-sell BTCUSDT 0.1 3600 10 --use-limit-orders
```

#### Grid Orders
```bash
# Create grid strategy (10 levels between $45k-$55k, $1000 investment)
python src/main.py grid-create BTCUSDT 55000 45000 10 1000

# Create geometric grid
python src/main.py grid-create BTCUSDT 55000 45000 10 1000 --grid-type geometric
```

### Utility Commands

```bash
# Get account information
python src/main.py account

# Get account balance
python src/main.py balance

# Get position information
python src/main.py positions

# Get open orders
python src/main.py open-orders

# Get current price
python src/main.py price BTCUSDT

# Cancel specific order
python src/main.py cancel-order BTCUSDT 123456789

# Cancel all orders for a symbol
python src/main.py cancel-all BTCUSDT
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BINANCE_API_KEY` | Your Binance API key | Required |
| `BINANCE_API_SECRET` | Your Binance API secret | Required |
| `BINANCE_TESTNET` | Use testnet (true/false) | true |

### Supported Symbols

The bot supports the following trading pairs:
- BTCUSDT, ETHUSDT, BNBUSDT
- ADAUSDT, SOLUSDT, DOTUSDT
- LINKUSDT, MATICUSDT, AVAXUSDT, UNIUSDT

## Logging

The bot provides comprehensive logging with the following features:

- **Structured Logs**: JSON-formatted logs in `logs/bot.log`
- **Console Output**: Human-readable console output
- **Event Tracking**: Order placement, execution, and errors
- **API Calls**: All API interactions are logged
- **Validation Errors**: Input validation failures

### Log Levels
- `DEBUG`: Detailed debugging information
- `INFO`: General information and order events
- `WARNING`: Validation errors and warnings
- `ERROR`: API errors and exceptions

## Error Handling

The bot includes robust error handling:

- **Input Validation**: All parameters are validated before API calls
- **API Error Handling**: Proper handling of Binance API errors
- **Network Resilience**: Retry logic for network issues
- **Graceful Degradation**: Continues operation when possible

## Security Features

- **API Key Protection**: Keys stored in environment variables
- **Input Sanitization**: All inputs are validated and sanitized
- **Error Logging**: No sensitive data in error logs
- **Testnet Support**: Safe testing environment

## Testing

### Testnet Usage
For testing, use Binance Testnet:
1. Set `BINANCE_TESTNET=true` in your `.env` file
2. Get testnet API keys from [Binance Testnet](https://testnet.binance.vision/)
3. Test all features without real money

### Live Trading
For live trading:
1. Set `BINANCE_TESTNET=false` in your `.env` file
2. Use real API keys from Binance Futures
3. Start with small amounts
4. Monitor logs carefully

## Risk Management

### Built-in Protections
- **Position Size Limits**: Configurable maximum position sizes
- **Risk Percentage**: Per-trade risk limits
- **Order Validation**: All orders are validated before placement
- **Slippage Protection**: TWAP orders include slippage controls

### Best Practices
- Always test on testnet first
- Start with small position sizes
- Monitor your positions regularly
- Set appropriate stop-loss orders
- Don't risk more than you can afford to lose

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Verify API key and secret are correct
   - Check IP whitelist settings
   - Ensure API has Futures trading permissions

2. **Validation Errors**
   - Check symbol format (e.g., BTCUSDT not BTC/USDT)
   - Verify quantity and price are positive numbers
   - Ensure supported symbols are used

3. **Network Errors**
   - Check internet connection
   - Verify Binance API status
   - Check firewall settings

### Getting Help

1. Check the logs in `logs/bot.log`
2. Verify your configuration
3. Test with simple market orders first
4. Use testnet for debugging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational purposes. Use at your own risk.

## Disclaimer

This software is for educational and research purposes only. Trading cryptocurrencies involves substantial risk of loss and is not suitable for all investors. The authors are not responsible for any financial losses incurred through the use of this software.

Always:
- Test thoroughly on testnet
- Start with small amounts
- Understand the risks involved
- Never invest more than you can afford to lose
