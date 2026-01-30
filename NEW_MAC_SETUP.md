# Setup Portfolio Quant on New MacBook

Quick guide to set up Portfolio Quant on a new MacBook with login page disabled.

---

## Quick Setup Steps

### 1. Clone Repository
```bash
cd ~/Documents
git clone https://github.com/tommybond/portfolio-quant.git
cd portfolio-quant
```

### 2. Run Installation Script
```bash
./install.sh
```

This will:
- ✅ Check prerequisites
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Create `.env` file with `HEADLESS_LOGIN=true` (login disabled)

### 3. Configure Alpaca API Keys

Edit `.env` file:
```bash
nano .env
```

Update these lines with your Alpaca keys:
```bash
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

### 4. Run the App
```bash
source venv/bin/activate
streamlit run app.py
```

**The login page will be automatically disabled** because `HEADLESS_LOGIN=true` is set in `.env`.

---

## Manual Setup (If install.sh doesn't work)

### Step 1: Install Python 3.11+
```bash
brew install python@3.11
```

### Step 2: Create Virtual Environment
```bash
cd ~/Documents/portfolio-quant
python3.11 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Create .env File
```bash
cat > .env << 'EOF'
# Database Configuration (Optional)
DATABASE_URL=postgresql://portfolio_quant:portfolio_quant_password@localhost:5434/portfolio_quant
TIMESCALEDB_URL=postgresql://portfolio_quant:portfolio_quant_password@localhost:5434/portfolio_quant
RELATIONAL_DB_URL=postgresql://portfolio_quant:portfolio_quant_password@localhost:5435/portfolio_quant_relational

# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379

# Headless Login (skip login page, auto-login as admin)
HEADLESS_LOGIN=true

# API Keys (REQUIRED - Update with your keys)
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Polygon API (Optional)
POLYGON_API_KEY=

# Security Keys (Auto-generated if empty)
JWT_SECRET_KEY=
ENCRYPTION_KEY=

# Application Environment
ENVIRONMENT=development
EOF
```

### Step 5: Update Alpaca Keys
```bash
nano .env
# Edit ALPACA_API_KEY and ALPACA_SECRET_KEY
```

### Step 6: Initialize Database and Create Admin User
```bash
source venv/bin/activate
python3 scripts/reset_admin.py
```

### Step 7: Run the App
```bash
streamlit run app.py
```

---

## Verify Login is Disabled

After starting the app, you should:
- ✅ **NOT see a login page**
- ✅ **Be automatically logged in as admin**
- ✅ **See the main dashboard directly**

If you still see a login page:

1. **Check .env file**:
   ```bash
   cat .env | grep HEADLESS_LOGIN
   # Should show: HEADLESS_LOGIN=true
   ```

2. **If missing, add it**:
   ```bash
   echo "HEADLESS_LOGIN=true" >> .env
   ```

3. **Restart the app**:
   ```bash
   # Stop app (Ctrl+C)
   streamlit run app.py
   ```

---

## Troubleshooting

### Issue: Login page still appears

**Solution 1: Check .env file**
```bash
cd ~/Documents/portfolio-quant
cat .env | grep HEADLESS_LOGIN
```

If it shows `HEADLESS_LOGIN=false` or is missing:
```bash
# Edit .env
nano .env

# Add or change to:
HEADLESS_LOGIN=true
```

**Solution 2: Verify environment variable is loaded**
```bash
source venv/bin/activate
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('HEADLESS_LOGIN:', os.getenv('HEADLESS_LOGIN'))
"
# Should print: HEADLESS_LOGIN: true
```

**Solution 3: Restart app**
```bash
# Stop app completely (Ctrl+C)
# Restart
streamlit run app.py
```

### Issue: "Module not found" errors

**Solution:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Database errors

**Solution:**
```bash
source venv/bin/activate
python3 scripts/init_database.py
python3 scripts/reset_admin.py
```

---

## Quick Reference

### Files to Check:
- `.env` - Must have `HEADLESS_LOGIN=true`
- `venv/` - Virtual environment must be activated
- `portfolio_quant.db` - Database file (created automatically)

### Commands:
```bash
# Activate virtual environment
source venv/bin/activate

# Run app
streamlit run app.py

# Reset admin user
python3 scripts/reset_admin.py

# Check HEADLESS_LOGIN setting
cat .env | grep HEADLESS_LOGIN
```

---

## Summary

**To disable login page on new Mac:**

1. ✅ Clone repository
2. ✅ Run `./install.sh` (creates .env with HEADLESS_LOGIN=true)
3. ✅ Update Alpaca API keys in `.env`
4. ✅ Run `python3 scripts/reset_admin.py` (creates admin user)
5. ✅ Run `streamlit run app.py`

**Login page will be automatically disabled** because `HEADLESS_LOGIN=true` is set.

---

**Need Help?**
- Check `INSTALLATION_GUIDE.md` for detailed setup
- Check `ALPACA_SETUP_GUIDE.md` for API key setup
- Check `ADMIN_LOGIN_TROUBLESHOOTING.md` for login issues
