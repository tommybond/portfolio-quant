#!/bin/bash

# Portfolio Quant Installation Script for macOS
# This script automates the installation process

set -e  # Exit on error

echo "🚀 Portfolio Quant Installation Script"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ This script is designed for macOS only${NC}"
    exit 1
fi

# Step 1: Check Prerequisites
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"

# Check Python
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo -e "${GREEN}✅ Python 3.11 found${NC}"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ $(echo "$PYTHON_VERSION >= 3.11" | bc -l) -eq 1 ]]; then
        PYTHON_CMD="python3"
        echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"
    else
        echo -e "${RED}❌ Python 3.11+ required. Found: $PYTHON_VERSION${NC}"
        echo "Install with: brew install python@3.11"
        exit 1
    fi
else
    echo -e "${RED}❌ Python 3.11+ not found${NC}"
    echo "Install with: brew install python@3.11"
    exit 1
fi

# Check Git
if command -v git &> /dev/null; then
    echo -e "${GREEN}✅ Git found${NC}"
else
    echo -e "${RED}❌ Git not found${NC}"
    echo "Install with: brew install git"
    exit 1
fi

# Check if we're in the project directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ Please run this script from the portfolio-quant directory${NC}"
    exit 1
fi

# Step 2: Create Virtual Environment
echo ""
echo -e "${YELLOW}Step 2: Creating virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment already exists. Skipping...${NC}"
else
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Step 3: Activate Virtual Environment
echo ""
echo -e "${YELLOW}Step 3: Activating virtual environment...${NC}"
source venv/bin/activate

# Verify activation
if [ "$VIRTUAL_ENV" != "" ]; then
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
    echo "   Python: $(python --version)"
else
    echo -e "${RED}❌ Failed to activate virtual environment${NC}"
    exit 1
fi

# Step 4: Upgrade pip
echo ""
echo -e "${YELLOW}Step 4: Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel --quiet
echo -e "${GREEN}✅ pip upgraded${NC}"

# Step 5: Install Dependencies
echo ""
echo -e "${YELLOW}Step 5: Installing dependencies (this may take a few minutes)...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

# Step 6: Verify Critical Packages
echo ""
echo -e "${YELLOW}Step 6: Verifying critical packages...${NC}"
python -c "import streamlit; print('✅ Streamlit:', streamlit.__version__)" 2>/dev/null || echo -e "${RED}❌ Streamlit not installed${NC}"
python -c "import pandas; print('✅ Pandas:', pandas.__version__)" 2>/dev/null || echo -e "${RED}❌ Pandas not installed${NC}"
python -c "import numpy; print('✅ NumPy:', numpy.__version__)" 2>/dev/null || echo -e "${RED}❌ NumPy not installed${NC}"
python -c "import yfinance; print('✅ yfinance:', yfinance.__version__)" 2>/dev/null || echo -e "${RED}❌ yfinance not installed${NC}"

# Step 7: Check .env file
echo ""
echo -e "${YELLOW}Step 7: Checking environment configuration...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"
    if grep -q "ALPACA_API_KEY=" .env && grep -q "ALPACA_SECRET_KEY=" .env; then
        if grep -q "ALPACA_API_KEY=$" .env || grep -q "ALPACA_API_KEY=your_" .env; then
            echo -e "${YELLOW}⚠️  Please update ALPACA_API_KEY and ALPACA_SECRET_KEY in .env file${NC}"
        else
            echo -e "${GREEN}✅ API keys configured${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  API keys not found in .env file${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  .env file not found. Creating template...${NC}"
    cat > .env << 'EOF'
# Database Configuration (Optional)
DATABASE_URL=postgresql://portfolio_quant:portfolio_quant_password@localhost:5434/portfolio_quant
TIMESCALEDB_URL=postgresql://portfolio_quant:portfolio_quant_password@localhost:5434/portfolio_quant
RELATIONAL_DB_URL=postgresql://portfolio_quant:portfolio_quant_password@localhost:5435/portfolio_quant_relational

# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379

# Headless Login
HEADLESS_LOGIN=true

# API Keys (REQUIRED)
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Polygon API (Optional)
POLYGON_API_KEY=

# Security Keys (Generate new ones)
JWT_SECRET_KEY=
ENCRYPTION_KEY=

# Application Environment
ENVIRONMENT=development
EOF
    echo -e "${GREEN}✅ .env template created. Please update with your API keys${NC}"
fi

# Step 8: Generate Security Keys (if needed)
echo ""
echo -e "${YELLOW}Step 8: Checking security keys...${NC}"
if grep -q "JWT_SECRET_KEY=$" .env || grep -q "ENCRYPTION_KEY=$" .env; then
    echo -e "${YELLOW}⚠️  Generating security keys...${NC}"
    JWT_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    ENCRYPTION_KEY=$(python3 -c "import secrets; import base64; print(base64.b64encode(secrets.token_bytes(32)).decode())")
    
    # Update .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_KEY|" .env
        sed -i '' "s|ENCRYPTION_KEY=.*|ENCRYPTION_KEY=$ENCRYPTION_KEY|" .env
    else
        sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_KEY|" .env
        sed -i "s|ENCRYPTION_KEY=.*|ENCRYPTION_KEY=$ENCRYPTION_KEY|" .env
    fi
    echo -e "${GREEN}✅ Security keys generated${NC}"
else
    echo -e "${GREEN}✅ Security keys already configured${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}======================================"
echo "✅ Installation Complete!"
echo "======================================${NC}"
echo ""
echo "Next steps:"
echo "1. Update .env file with your Alpaca API keys"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the app: streamlit run app.py"
echo ""
echo "To activate virtual environment in the future:"
echo "  source venv/bin/activate"
echo ""
echo "To run the application:"
echo "  streamlit run app.py"
echo ""
