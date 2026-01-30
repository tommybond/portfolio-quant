# How to Pass Alpaca API Keys Inside Virtual Environment

Complete guide for setting Alpaca API keys in your virtual environment.

---

## Method 1: Using .env File (Recommended) ✅

The app automatically loads keys from `.env` file using `python-dotenv`.

### Setup:
```bash
# Activate virtual environment
source venv/bin/activate

# Edit .env file
nano .env
```

### Add/Update these lines in .env:
```bash
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

### Verify:
```bash
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('API Key:', os.getenv('ALPACA_API_KEY')[:10] + '...' if os.getenv('ALPACA_API_KEY') else 'NOT SET')
print('Secret Key:', 'SET' if os.getenv('ALPACA_SECRET_KEY') else 'NOT SET')
"
```

**✅ This is the recommended method** - Keys are loaded automatically when app starts.

---

## Method 2: Export Environment Variables (Current Session Only)

### Set in current shell session:
```bash
# Activate virtual environment first
source venv/bin/activate

# Export keys
export ALPACA_API_KEY="your_api_key_here"
export ALPACA_SECRET_KEY="your_secret_key_here"
export ALPACA_BASE_URL="https://paper-api.alpaca.markets"

# Verify
echo $ALPACA_API_KEY
echo $ALPACA_SECRET_KEY
```

**Note:** These are only available in the current terminal session. They will be lost when you close the terminal.

---

## Method 3: Add to Virtual Environment Activation Script (Permanent for venv)

### Edit venv/bin/activate:
```bash
# Activate venv first
source venv/bin/activate

# Edit activation script
nano venv/bin/activate
```

### Add these lines before the `deactivate ()` function:
```bash
# Alpaca API Keys
export ALPACA_API_KEY="your_api_key_here"
export ALPACA_SECRET_KEY="your_secret_key_here"
export ALPACA_BASE_URL="https://paper-api.alpaca.markets"
```

### Now keys will be set automatically:
```bash
source venv/bin/activate
echo $ALPACA_API_KEY  # Should show your key
```

**Note:** Keys are stored in plain text in `venv/bin/activate`. If you delete and recreate venv, you'll need to add them again.

---

## Method 4: Use Helper Script (Automated)

### Run the setup script:
```bash
cd ~/Documents/portfolio-quant
source venv/bin/activate
./SET_ALPACA_KEYS.sh
```

This script will:
1. Check if venv is activated
2. Ask you to choose a method
3. Prompt for your API keys
4. Set them up automatically

---

## Method 5: Set in Python Script

### Create a setup script:
```bash
# Create activate_keys.py
cat > activate_keys.py << 'EOF'
import os
os.environ['ALPACA_API_KEY'] = 'your_api_key_here'
os.environ['ALPACA_SECRET_KEY'] = 'your_secret_key_here'
os.environ['ALPACA_BASE_URL'] = 'https://paper-api.alpaca.markets'
EOF

# Use it before running app
python3 activate_keys.py
streamlit run app.py
```

---

## Quick Setup Commands

### Option A: Edit .env file (Best)
```bash
source venv/bin/activate
nano .env
# Add/update ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL
```

### Option B: Export in current session
```bash
source venv/bin/activate
export ALPACA_API_KEY="your_key"
export ALPACA_SECRET_KEY="your_secret"
export ALPACA_BASE_URL="https://paper-api.alpaca.markets"
```

### Option C: Use helper script
```bash
source venv/bin/activate
./SET_ALPACA_KEYS.sh
```

---

## Verify Keys Are Loaded

### Test 1: Check environment variables
```bash
source venv/bin/activate
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('API Key:', os.getenv('ALPACA_API_KEY')[:10] + '...' if os.getenv('ALPACA_API_KEY') else 'NOT SET')
print('Secret:', 'SET' if os.getenv('ALPACA_SECRET_KEY') else 'NOT SET')
print('Base URL:', os.getenv('ALPACA_BASE_URL', 'NOT SET'))
"
```

### Test 2: Test Alpaca connection
```bash
source venv/bin/activate
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
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

---

## Recommended Workflow

### For Development:
1. **Use .env file** (Method 1) - Most convenient
2. Keys are automatically loaded by `python-dotenv`
3. `.env` is in `.gitignore` (safe, won't be committed)

### For Production:
1. Use environment variables from your hosting platform
2. Or use `.env` file (keep it secure)
3. Never commit `.env` to git

---

## Troubleshooting

### Issue: Keys not loading

**Check:**
```bash
# 1. Verify .env file exists
ls -la .env

# 2. Check if python-dotenv is installed
pip list | grep dotenv

# 3. Verify keys in .env
cat .env | grep ALPACA

# 4. Test loading
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('ALPACA_API_KEY'))"
```

**Solution:**
```bash
# Install python-dotenv if missing
pip install python-dotenv

# Or set environment variables directly
export ALPACA_API_KEY="your_key"
export ALPACA_SECRET_KEY="your_secret"
```

### Issue: Keys work in terminal but not in app

**Solution:**
- Make sure `.env` file is in the project root (same directory as `app.py`)
- Restart the Streamlit app after updating `.env`
- Check that `load_dotenv()` is called in `app.py` (it is, at the top)

---

## Summary

**Best Practice:** Use `.env` file (Method 1)
- ✅ Automatic loading
- ✅ Not committed to git
- ✅ Works across sessions
- ✅ Easy to update

**Quick Setup:**
```bash
source venv/bin/activate
nano .env
# Add your keys
streamlit run app.py
```

Keys will be automatically loaded! 🎉
