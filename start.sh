#!/bin/bash
# Start Portfolio Quant Application

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🚀 Starting Portfolio Quant Trading System"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "Please run: ./install.sh"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}❌ Failed to activate virtual environment${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "Creating default .env file..."
    cat > .env << 'EOF'
# Headless Login (skip login page, auto-login as admin)
HEADLESS_LOGIN=true

# API Keys (REQUIRED - Update with your keys)
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Application Environment
ENVIRONMENT=development
EOF
    echo -e "${YELLOW}⚠️  Please update ALPACA_API_KEY and ALPACA_SECRET_KEY in .env file${NC}"
    echo ""
fi

# Check if required packages are installed
echo -e "${YELLOW}Checking dependencies...${NC}"
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Streamlit not found. Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

echo -e "${GREEN}✅ Dependencies ready${NC}"
echo ""

# Check if admin user exists
echo -e "${YELLOW}Checking admin user...${NC}"
python3 -c "
import sys
import os
sys.path.insert(0, '.')
try:
    from database.models import create_session, User
    db = create_session()
    admin = db.query(User).filter(User.username == 'admin').first()
    if admin:
        print('✅ Admin user exists')
    else:
        print('⚠️  Admin user not found. Creating...')
        os.system('python3 scripts/reset_admin.py')
    db.close()
except Exception as e:
    print(f'⚠️  Database check: {e}')
" 2>/dev/null

echo ""
echo "=========================================="
echo -e "${GREEN}Starting Streamlit application...${NC}"
echo "=========================================="
echo ""
echo "🌐 App will open at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Streamlit
streamlit run app.py
