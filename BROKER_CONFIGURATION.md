# Broker Configuration Guide

Complete guide to broker configuration and status checking.

---

## Available Brokers

### 1. 🔵 Alpaca Broker (Primary)

**Status**: ✅ Configured and Active

**Configuration:**
- **API Key**: Set in `.env` file
- **Secret Key**: Set in `.env` file
- **Base URL**: `https://paper-api.alpaca.markets` (Paper Trading)
- **Mode**: Paper Trading (for testing)

**Features:**
- Order submission (BUY/SELL)
- Position management
- Account information
- Real-time market data

**Files:**
- `oms/broker_alpaca.py` - Standard Alpaca integration
- `oms/broker_alpaca_enhanced.py` - Enhanced features (advanced orders, multi-account)

---

### 2. 🟢 Interactive Brokers (IBKR)

**Status**: ⚠️ Module Available (Requires TWS/IB Gateway)

**Configuration:**
- **Host**: `127.0.0.1` (default)
- **Port**: `7497` (default, paper trading)
- **Client ID**: `1` (default)

**Requirements:**
- Interactive Brokers TWS (Trader Workstation) or IB Gateway must be running
- TWS/IB Gateway must be configured to accept API connections

**Files:**
- `oms/broker_ibkr.py` - IBKR integration

**Note**: Not actively used in current implementation. Requires TWS/IB Gateway setup.

---

### 3. 🟣 Polygon API (Market Data)

**Status**: ⚠️ Optional (for enhanced market data)

**Configuration:**
- **API Key**: Set in `.env` file (optional)
- Used for: Real-time market data, Level 2 data, options data

**Files:**
- `data/realtime_data.py` - Uses Polygon if available
- Falls back to Alpaca or yfinance if not configured

---

## Check Broker Status

### Quick Check Command:
```bash
cd ~/Documents/portfolio-quant
source venv/bin/activate
python3 scripts/check_brokers.py
```

### Manual Check:
```bash
# Check Alpaca configuration
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Alpaca API Key:', 'SET' if os.getenv('ALPACA_API_KEY') else 'NOT SET')
print('Alpaca Secret:', 'SET' if os.getenv('ALPACA_SECRET_KEY') else 'NOT SET')
print('Base URL:', os.getenv('ALPACA_BASE_URL', 'NOT SET'))
"
```

---

## Current Configuration

### Alpaca Broker (Active)
```bash
ALPACA_API_KEY=PK7ZAC2NTY6KPMRFIRSZT4PH6N
ALPACA_SECRET_KEY=ERfRcbYQmZ1ZMpTkj2ATskGLHBcAbDJZ183AmeBHtWsq
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

**Status**: ✅ Configured and Working

---

## Broker Usage in App

### Where Brokers Are Used:

1. **Institutional Deployment Tab**
   - Uses `AlpacaBroker()` for:
     - Fetching current positions
     - Getting live prices
     - Submitting orders (BUY/SELL)

2. **Institutional Strategy Tab**
   - Uses `AlpacaBroker()` for:
     - Loading positions from broker
     - Getting live prices for analysis

3. **Order Management System (OMS)**
   - Routes orders through configured broker
   - Handles order submission and tracking

---

## Testing Broker Connection

### Test Alpaca Connection:
```bash
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
import alpaca_trade_api as tradeapi

api_key = os.getenv('ALPACA_API_KEY')
api_secret = os.getenv('ALPACA_SECRET_KEY')
base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

try:
    api = tradeapi.REST(api_key, api_secret, base_url, api_version='v2')
    account = api.get_account()
    print('✅ Connection successful!')
    print(f'Account Status: {account.status}')
    print(f'Buying Power: ${float(account.buying_power):,.2f}')
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

---

## Troubleshooting

### Issue: "ALPACA_API_KEY and ALPACA_SECRET_KEY must be set"

**Solution:**
1. Check `.env` file exists
2. Verify keys are set (not placeholders)
3. Restart the app

### Issue: "Connection refused" or "Authentication failed"

**Solution:**
1. Verify API keys in Alpaca dashboard
2. Check base URL (use `https://paper-api.alpaca.markets` for paper trading)
3. Ensure keys don't have extra spaces

### Issue: Broker not connecting

**Solution:**
```bash
# Run broker check script
python3 scripts/check_brokers.py

# Test connection manually
python3 -c "
from oms.broker_alpaca import AlpacaBroker
try:
    broker = AlpacaBroker()
    print('✅ Broker initialized')
    account = broker.api.get_account()
    print(f'✅ Connected: {account.status}')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

---

## Summary

**Primary Broker**: 🔵 Alpaca (Paper Trading)
- ✅ Configured
- ✅ Active
- ✅ Ready for trading

**Secondary Options**:
- 🟢 IBKR - Available but requires TWS setup
- 🟣 Polygon - Optional for enhanced data

**Check Status**: Run `python3 scripts/check_brokers.py`
