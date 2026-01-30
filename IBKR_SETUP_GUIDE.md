# Interactive Brokers (IBKR) Setup Guide

Complete guide for setting up and using IBKR broker integration.

---

## Prerequisites

### 1. Install ib_insync Library
```bash
source venv/bin/activate
pip install ib-insync
```

### 2. Install TWS or IB Gateway

**Option A: Trader Workstation (TWS)**
- Download from: https://www.interactivebrokers.com/en/index.php?f=16042
- Full-featured trading platform

**Option B: IB Gateway (Recommended for API)**
- Download from: https://www.interactivebrokers.com/en/index.php?f=16457
- Lightweight, API-focused
- Better for automated trading

### 3. Configure TWS/IB Gateway

1. **Enable API Connections:**
   - Open TWS/Gateway
   - Go to: **Configure → API → Settings**
   - Check: **Enable ActiveX and Socket Clients**
   - Set **Socket Port**: `7497` (Paper) or `7496` (Live)
   - Check: **Download open orders on connection**
   - Click **OK**

2. **Paper Trading Setup:**
   - In TWS: **File → Global Configuration → API → Settings**
   - Set port to `7497` for paper trading
   - Set port to `7496` for live trading

3. **Start TWS/Gateway:**
   - Make sure TWS or IB Gateway is running before using the broker
   - The application will connect automatically

---

## Configuration

### Environment Variables (.env file)

```bash
# Interactive Brokers (IBKR) Configuration
IBKR_HOST=127.0.0.1          # TWS/Gateway host (default: localhost)
IBKR_PORT=7497               # 7497 = Paper Trading, 7496 = Live Trading
IBKR_CLIENT_ID=1             # Client ID (default: 1)
```

### Default Values

If not set in `.env`, defaults are:
- **Host**: `127.0.0.1` (localhost)
- **Port**: `7497` (Paper Trading)
- **Client ID**: `1`

---

## Usage

### Initialize IBKR Broker

```python
from oms.broker_ibkr import IBKRBroker

# Using defaults (from .env or defaults)
broker = IBKRBroker()

# Or with custom parameters
broker = IBKRBroker(
    host='127.0.0.1',
    port=7497,  # Paper trading
    client_id=1
)
```

### Submit Order

```python
from oms.oms import Order, OrderType

order = Order(
    symbol='AAPL',
    side='BUY',
    quantity=100,
    order_type=OrderType.MARKET,
    time_in_force='DAY'
)

result = broker.submit_order(order)
print(f"Order ID: {result['order_id']}")
print(f"Status: {result['status']}")
```

### Get Positions

```python
positions = broker.get_positions()
for pos in positions:
    print(f"{pos['symbol']}: {pos['quantity']} @ ${pos['average_price']}")
```

### Get Account Info

```python
account = broker.get_account_info()
print(f"Buying Power: ${account['buying_power']:,.2f}")
print(f"Cash: ${account['cash']:,.2f}")
print(f"Equity: ${account['equity']:,.2f}")
```

### Cancel Order

```python
success = broker.cancel_order(order_id='12345')
```

### Get Order Status

```python
status = broker.get_order_status(order_id='12345')
print(f"Status: {status['status']}")
print(f"Filled: {status['filled_quantity']}")
```

---

## Order Types Supported

- ✅ **MARKET** - Market order
- ✅ **LIMIT** - Limit order (requires price)
- ✅ **STOP** - Stop order (requires stop_price)
- ✅ **STOP_LIMIT** - Stop-limit order (requires stop_price and price)

---

## Time in Force Options

- **DAY** - Day order (default)
- **GTC** - Good Till Cancel
- **IOC** - Immediate or Cancel
- **FOK** - Fill or Kill

---

## Troubleshooting

### Issue: "Failed to connect to IBKR TWS/Gateway"

**Solutions:**
1. **Check TWS/Gateway is running:**
   ```bash
   # On macOS/Linux
   ps aux | grep -i "tws\|ibgateway"
   ```

2. **Verify API is enabled:**
   - TWS: **Configure → API → Settings**
   - Check: **Enable ActiveX and Socket Clients**
   - Verify port matches configuration (7497 for paper)

3. **Check firewall:**
   - Ensure localhost connections are allowed
   - Port 7497 (paper) or 7496 (live) is not blocked

4. **Verify port:**
   ```bash
   # Check if port is listening
   lsof -i :7497  # Paper trading
   lsof -i :7496  # Live trading
   ```

### Issue: "ib_insync not installed"

**Solution:**
```bash
source venv/bin/activate
pip install ib-insync
```

### Issue: "Invalid contract for symbol"

**Solutions:**
1. **Check symbol format:**
   - Use standard ticker symbols (e.g., 'AAPL', 'MSFT')
   - For options/futures, use IBKR contract format

2. **Verify market hours:**
   - Some symbols may not be available outside market hours
   - IBKR may require market data subscriptions for some symbols

### Issue: "Order not found"

**Solutions:**
1. **Check order ID format:**
   - IBKR order IDs are integers
   - Ensure you're using the correct order ID

2. **Verify order is still active:**
   - Filled or cancelled orders may not appear in open trades
   - Check order history in TWS

---

## Testing Connection

### Quick Test Script

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from oms.broker_ibkr import IBKRBroker

try:
    print("Connecting to IBKR...")
    broker = IBKRBroker()
    print("✅ Connected successfully!")
    
    print("\nAccount Info:")
    account = broker.get_account_info()
    for key, value in account.items():
        print(f"  {key}: ${value:,.2f}")
    
    print("\nPositions:")
    positions = broker.get_positions()
    if positions:
        for pos in positions:
            print(f"  {pos['symbol']}: {pos['quantity']} @ ${pos['average_price']:.2f}")
    else:
        print("  No open positions")
    
    broker.disconnect()
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nMake sure:")
    print("1. TWS or IB Gateway is running")
    print("2. API connections are enabled")
    print("3. Port matches configuration (7497 for paper)")
```

---

## Important Notes

### Paper Trading vs Live Trading

- **Paper Trading (Port 7497):**
  - Uses simulated account
  - No real money at risk
  - Perfect for testing

- **Live Trading (Port 7496):**
  - Real money, real trades
  - Use only after thorough testing
  - Ensure proper risk management

### Connection Management

- The broker maintains a persistent connection to TWS/Gateway
- Connection is automatically re-established if lost
- Always disconnect when done: `broker.disconnect()`

### Market Data Subscriptions

- Some features require market data subscriptions
- Check IBKR account for required subscriptions
- Paper trading may have limited market data

### Order Execution

- Orders are executed through IBKR's routing
- Execution quality depends on IBKR's routing
- Check TWS for order status and fills

---

## Comparison: Alpaca vs IBKR

| Feature | Alpaca | IBKR |
|---------|--------|------|
| **Setup** | API keys only | Requires TWS/Gateway |
| **Paper Trading** | ✅ Built-in | ✅ Available |
| **Order Types** | Market, Limit, Stop | Market, Limit, Stop, Stop-Limit |
| **Market Data** | Included | May require subscription |
| **Global Markets** | US only | ✅ Global |
| **Options Trading** | Limited | ✅ Full support |
| **Futures** | ❌ | ✅ |

---

## Summary

**IBKR Broker Integration:**
- ✅ Fully implemented
- ✅ Supports all order types
- ✅ Position and account management
- ✅ Requires TWS/IB Gateway running
- ✅ Works with paper and live trading

**Quick Start:**
1. Install: `pip install ib-insync`
2. Start TWS/IB Gateway
3. Enable API connections
4. Use `IBKRBroker()` in your code

---

**Need Help?**
- IBKR API Documentation: https://interactivebrokers.github.io/tws-api/
- ib_insync Documentation: https://ib-insync.readthedocs.io/
- IBKR Support: https://www.interactivebrokers.com/
