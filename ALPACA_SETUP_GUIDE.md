# How to Set Alpaca API Keys and Secrets

Complete guide for configuring Alpaca API credentials for Portfolio Quant.

---

## Step 1: Get Your Alpaca API Keys

### Create/Login to Alpaca Account
1. Go to: **https://alpaca.markets/**
2. Click **"Sign Up"** or **"Log In"**
3. Complete registration/login process

### Get API Keys
1. After logging in, go to: **https://app.alpaca.markets/**
2. Navigate to **"Your API Keys"** or **"Paper Trading"** section
3. You'll see:
   - **API Key ID** (starts with `PK...` for paper trading)
   - **Secret Key** (long alphanumeric string)
   - **Base URL**: 
     - Paper Trading: `https://paper-api.alpaca.markets`
     - Live Trading: `https://api.alpaca.markets`

### Paper Trading vs Live Trading
- **Paper Trading** (Recommended for testing):
  - Base URL: `https://paper-api.alpaca.markets`
  - API Key starts with `PK...`
  - Free, uses virtual money
  - Perfect for testing and development

- **Live Trading** (Production):
  - Base URL: `https://api.alpaca.markets`
  - Real money, real trades
  - Use only after thorough testing

---

## Step 2: Set Keys in .env File

### Method 1: Edit .env File Directly

```bash
# Navigate to project directory
cd ~/Documents/portfolio-quant

# Open .env file in your editor
nano .env
# or
code .env
# or
open -a TextEdit .env
```

### Method 2: Use Command Line

```bash
cd ~/Documents/portfolio-quant

# Edit the .env file
nano .env
```

### Update These Lines in .env:

```bash
# API Keys
ALPACA_API_KEY=PK7ZAC2NTY6KPMRFIRSZT4PH6N
ALPACA_SECRET_KEY=ERfRcbYQmZ1ZMpTkj2ATskGLHBcAbDJZ183AmeBHtWsq
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

**Replace with your actual keys:**
- `ALPACA_API_KEY` = Your API Key ID from Alpaca dashboard
- `ALPACA_SECRET_KEY` = Your Secret Key from Alpaca dashboard
- `ALPACA_BASE_URL` = Use `https://paper-api.alpaca.markets` for paper trading

---

## Step 3: Complete .env File Template

Your `.env` file should look like this:

```bash
# Database Configuration (Optional)
DATABASE_URL=postgresql://portfolio_quant:portfolio_quant_password@localhost:5434/portfolio_quant
TIMESCALEDB_URL=postgresql://portfolio_quant:portfolio_quant_password@localhost:5434/portfolio_quant
RELATIONAL_DB_URL=postgresql://portfolio_quant:portfolio_quant_password@localhost:5435/portfolio_quant_relational

# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379

# Headless Login (skip login page, auto-login as admin)
HEADLESS_LOGIN=true

# API Keys (REQUIRED)
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Polygon API (Optional - for additional market data)
POLYGON_API_KEY=

# Security Keys (Auto-generated if empty)
JWT_SECRET_KEY=78345a8f2fb0f038bb2fe20719064445ddeb385bcc4f1eab068b32ac409eb219
ENCRYPTION_KEY=YmydAu2gVpDCYXeXKGW8nTH_dyXOCYEzutJtJ2mTuwQ=

# Application Environment
ENVIRONMENT=development
```

---

## Step 4: Verify Keys Are Set

### Check Environment Variables

```bash
# Activate virtual environment
source venv/bin/activate

# Check if keys are loaded
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', os.getenv('ALPACA_API_KEY')[:10] + '...' if os.getenv('ALPACA_API_KEY') else 'NOT SET'); print('Secret Key:', 'SET' if os.getenv('ALPACA_SECRET_KEY') else 'NOT SET')"
```

### Test Alpaca Connection

```bash
# Test connection
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
    print('✅ Alpaca connection successful!')
    print(f'Account Status: {account.status}')
    print(f'Buying Power: ${float(account.buying_power):,.2f}')
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

---

## Step 5: Run the Application

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run Streamlit app
streamlit run app.py
```

The app will automatically load your Alpaca keys from the `.env` file.

---

## Troubleshooting

### Issue: "ALPACA_API_KEY and ALPACA_SECRET_KEY must be set"

**Solution:**
1. Check that `.env` file exists in project root
2. Verify keys are set (no `your_api_key_here` placeholders)
3. Make sure `python-dotenv` is installed: `pip install python-dotenv`
4. Restart the application

### Issue: "Authentication failed" or "Invalid API key"

**Solution:**
1. Double-check API keys in Alpaca dashboard
2. Ensure you're using the correct base URL:
   - Paper: `https://paper-api.alpaca.markets`
   - Live: `https://api.alpaca.markets`
3. Verify keys don't have extra spaces or quotes
4. Regenerate keys in Alpaca dashboard if needed

### Issue: Keys not loading

**Solution:**
```bash
# Check .env file location
ls -la .env

# Verify file format (no spaces around =)
cat .env | grep ALPACA

# Reload environment
source venv/bin/activate
```

---

## Security Best Practices

### ⚠️ Important Security Notes:

1. **Never commit .env file to Git**
   - `.env` is already in `.gitignore`
   - Contains sensitive credentials
   - Keep it local only

2. **Use Paper Trading for Development**
   - Always test with paper trading first
   - Use live trading only in production

3. **Rotate Keys Periodically**
   - Regenerate keys every 90 days
   - Revoke old keys when generating new ones

4. **Don't Share Keys**
   - Never share API keys publicly
   - Use environment variables, not hardcoded values

5. **Use Different Keys for Different Environments**
   - Separate keys for development/staging/production
   - Use paper trading keys for development

---

## Quick Reference

### Environment Variables Used:
- `ALPACA_API_KEY` - Your Alpaca API Key ID
- `ALPACA_SECRET_KEY` - Your Alpaca Secret Key
- `ALPACA_BASE_URL` - API endpoint URL
  - Paper: `https://paper-api.alpaca.markets`
  - Live: `https://api.alpaca.markets`

### Where Keys Are Used:
- `oms/broker_alpaca.py` - Order submission
- `data/realtime_data.py` - Live price data
- `app.py` - Institutional Deployment tab

### File Location:
- `.env` file in project root: `/Users/bk774n/Documents/portfolio-quant/.env`

---

## Example: Setting Keys on New MacBook

```bash
# 1. Navigate to project
cd ~/Documents/portfolio-quant

# 2. Create/Edit .env file
nano .env

# 3. Add your keys:
ALPACA_API_KEY=PK7ZAC2NTY6KPMRFIRSZT4PH6N
ALPACA_SECRET_KEY=ERfRcbYQmZ1ZMpTkj2ATskGLHBcAbDJZ183AmeBHtWsq
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# 4. Save and exit (Ctrl+X, then Y, then Enter)

# 5. Test connection
source venv/bin/activate
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Keys loaded:', bool(os.getenv('ALPACA_API_KEY')))"

# 6. Run app
streamlit run app.py
```

---

**Need Help?**
- Alpaca Documentation: https://alpaca.markets/docs/
- Alpaca Dashboard: https://app.alpaca.markets/
- Support: Check Alpaca support or GitHub issues
