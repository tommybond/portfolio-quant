# Installation Guide: Portfolio Quant on macOS

Complete step-by-step guide to install and run Portfolio Quant on a new MacBook.

---

## Prerequisites

### 1. System Requirements
- **macOS** (10.15+ recommended)
- **Python 3.11+** (required)
- **Git** (for cloning repository)
- **Homebrew** (recommended for package management)

### 2. Check Current Versions
```bash
# Check Python version
python3 --version
# Should show: Python 3.11.x or higher

# Check Git version
git --version

# Check if Homebrew is installed
brew --version
```

---

## Step 1: Install Prerequisites

### Install Homebrew (if not installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Install Python 3.11+ via Homebrew
```bash
# Install Python 3.11
brew install python@3.11

# Verify installation
python3.11 --version

# Add to PATH (add to ~/.zshrc or ~/.bash_profile)
echo 'export PATH="/opt/homebrew/opt/python@3.11/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Install Git (if not installed)
```bash
brew install git
```

---

## Step 2: Clone the Repository

### Option A: Clone via HTTPS (requires GitHub token)
```bash
# Navigate to desired directory
cd ~/Documents  # or your preferred location

# Clone the repository
git clone https://github.com/tommybond/portfolio-quant.git

# Navigate into project
cd portfolio-quant
```

### Option B: Clone via SSH (if SSH keys are set up)
```bash
git clone git@github.com:tommybond/portfolio-quant.git
cd portfolio-quant
```

### Option C: Download ZIP (if Git is not available)
1. Go to: https://github.com/tommybond/portfolio-quant
2. Click "Code" → "Download ZIP"
3. Extract and navigate to folder

---

## Step 3: Set Up Python Virtual Environment

### Create Virtual Environment
```bash
cd ~/Documents/portfolio-quant

# Create virtual environment with Python 3.11
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify Python version in venv
python --version
# Should show: Python 3.11.x
```

### Upgrade pip and setuptools
```bash
pip install --upgrade pip setuptools wheel
```

---

## Step 4: Install Dependencies

### Install from requirements.txt
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# This may take 5-10 minutes depending on internet speed
```

### Verify Critical Packages
```bash
python -c "import streamlit; print('✅ Streamlit:', streamlit.__version__)"
python -c "import pandas; print('✅ Pandas:', pandas.__version__)"
python -c "import numpy; print('✅ NumPy:', numpy.__version__)"
python -c "import yfinance; print('✅ yfinance:', yfinance.__version__)"
python -c "import alpaca_trade_api; print('✅ Alpaca API installed')"
```

---

## Step 5: Configure Environment Variables

### Create .env File
```bash
cd ~/Documents/portfolio-quant

# Copy example if exists, or create new
touch .env
```

### Edit .env File
Open `.env` in your text editor and add:

```bash
# Database Configuration (Optional - only if using PostgreSQL)
DATABASE_URL=postgresql://portfolio_quant:portfolio_quant_password@localhost:5434/portfolio_quant
TIMESCALEDB_URL=postgresql://portfolio_quant:portfolio_quant_password@localhost:5434/portfolio_quant
RELATIONAL_DB_URL=postgresql://portfolio_quant:portfolio_quant_password@localhost:5435/portfolio_quant_relational

# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379

# Headless Login (skip login page, auto-login as admin)
HEADLESS_LOGIN=true

# API Keys (REQUIRED for live trading)
# Get from: https://alpaca.markets/
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Use paper trading for testing

# Polygon API (Optional - for additional market data)
POLYGON_API_KEY=your_polygon_api_key_here

# Security Keys (Generate new ones for production)
JWT_SECRET_KEY=generate_random_32_bytes_hex
ENCRYPTION_KEY=generate_random_base64_key

# Application Environment
ENVIRONMENT=development
```

### Generate Security Keys (if needed)
```bash
# Generate JWT_SECRET_KEY (32 bytes hex)
python3 -c "import secrets; print(secrets.token_hex(32))"

# Generate ENCRYPTION_KEY (base64)
python3 -c "import secrets; import base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

---

## Step 6: Configure Settings

### Check config/settings.yaml
The file should exist with default settings:
```yaml
approval_mode: AUTO
kill_switch: true
market: US
max_daily_dd: 0.03
max_total_dd: 0.12

# Institutional patch settings
max_var: -0.05
enable_trench_execution: true
enable_portfolio_allocator: true
enable_compliance_logging: true
```

Edit if needed:
```bash
nano config/settings.yaml
# or use your preferred editor
```

---

## Step 7: Set Up Git Credentials (Optional)

### Configure Git User
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Set Up GitHub Personal Access Token
1. Go to: https://github.com/settings/tokens
2. Generate new token (classic) with `repo` scope
3. Use token as password when Git prompts for credentials

---

## Step 8: Run the Application

### Start Streamlit App
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the application
streamlit run app.py

# The app will open in your browser at: http://localhost:8501
```

### First Launch
- If `HEADLESS_LOGIN=true`, you'll be automatically logged in as 'admin'
- If not, you'll see a login page (default credentials may be in auth/auth.py)

---

## Step 9: Verify Installation

### Test Basic Functionality
1. **Dashboard Tab**: Should load without errors
2. **Institutional Deployment Tab**: Should show price fetching
3. **Institutional Strategy Tab**: Should load positions (if Alpaca connected)

### Test Alpaca Connection
1. Go to "🏛️ Institutional Deployment" tab
2. Enter a ticker (e.g., "AAPL")
3. Click "Fetch Price"
4. Should show current price (if API keys are correct)

---

## Troubleshooting

### Issue: Python Version Mismatch
**Error**: `Python 3.x required but 3.y found`

**Solution**:
```bash
# Use specific Python version
python3.11 -m venv venv
source venv/bin/activate
python --version  # Verify it's 3.11+
```

### Issue: Module Not Found
**Error**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### Issue: Alpaca API Connection Failed
**Error**: `Alpaca connection failed`

**Solution**:
1. Verify API keys in `.env` file
2. Check `ALPACA_BASE_URL` (use `https://paper-api.alpaca.markets` for paper trading)
3. Ensure API keys are active in Alpaca dashboard

### Issue: Port Already in Use
**Error**: `Port 8501 is already in use`

**Solution**:
```bash
# Use different port
streamlit run app.py --server.port 8502

# Or kill existing process
lsof -ti:8501 | xargs kill -9
```

### Issue: Permission Denied
**Error**: `Permission denied` when running commands

**Solution**:
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Or use sudo (not recommended)
sudo pip install ...
```

---

## Optional: Database Setup (PostgreSQL + TimescaleDB)

### Install PostgreSQL via Docker
```bash
# Install Docker Desktop for Mac
# Download from: https://www.docker.com/products/docker-desktop

# Start Docker
docker-compose up -d

# Verify containers are running
docker ps
```

### Initialize Database
```bash
source venv/bin/activate
python scripts/init_database.py
```

---

## Quick Start Commands Summary

```bash
# 1. Clone repository
cd ~/Documents
git clone https://github.com/tommybond/portfolio-quant.git
cd portfolio-quant

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env  # If exists, or create manually
nano .env  # Add API keys

# 5. Run application
streamlit run app.py
```

---

## Next Steps

1. **Configure API Keys**: Add your Alpaca API keys to `.env`
2. **Test Connection**: Verify Alpaca connection in the app
3. **Review Settings**: Check `config/settings.yaml` for your preferences
4. **Read Documentation**: Check other `.md` files for feature guides

---

## Support

- **Repository**: https://github.com/tommybond/portfolio-quant
- **Issues**: Check GitHub Issues for known problems
- **Documentation**: See other `.md` files in the project

---

## Security Notes

⚠️ **Important**:
- Never commit `.env` file to Git (it's in `.gitignore`)
- Use paper trading API keys for testing
- Generate new security keys for production
- Keep API keys secure and rotate periodically

---

**Installation Complete!** 🎉

You should now be able to run Portfolio Quant on your MacBook.
