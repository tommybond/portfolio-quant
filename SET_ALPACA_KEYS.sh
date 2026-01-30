#!/bin/bash
# Set Alpaca API Keys in Virtual Environment

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔑 Alpaca API Keys Setup"
echo "========================"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated${NC}"
    echo "Activating virtual environment..."
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
    else
        echo "❌ venv directory not found. Run: python3 -m venv venv"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Virtual environment active: $VIRTUAL_ENV${NC}"
fi

echo ""
echo "Choose an option:"
echo "1. Set keys in .env file (recommended)"
echo "2. Export as environment variables (current session only)"
echo "3. Add to virtual environment activation script (permanent for venv)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "Setting keys in .env file..."
        
        read -p "Enter ALPACA_API_KEY: " api_key
        read -sp "Enter ALPACA_SECRET_KEY: " api_secret
        echo ""
        read -p "Enter ALPACA_BASE_URL [https://paper-api.alpaca.markets]: " base_url
        base_url=${base_url:-https://paper-api.alpaca.markets}
        
        # Update .env file
        cd "$(dirname "$0")" || exit
        
        if [ -f ".env" ]; then
            # Update existing keys
            if grep -q "^ALPACA_API_KEY=" .env; then
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    sed -i '' "s|^ALPACA_API_KEY=.*|ALPACA_API_KEY=$api_key|" .env
                    sed -i '' "s|^ALPACA_SECRET_KEY=.*|ALPACA_SECRET_KEY=$api_secret|" .env
                    sed -i '' "s|^ALPACA_BASE_URL=.*|ALPACA_BASE_URL=$base_url|" .env
                else
                    sed -i "s|^ALPACA_API_KEY=.*|ALPACA_API_KEY=$api_key|" .env
                    sed -i "s|^ALPACA_SECRET_KEY=.*|ALPACA_SECRET_KEY=$api_secret|" .env
                    sed -i "s|^ALPACA_BASE_URL=.*|ALPACA_BASE_URL=$base_url|" .env
                fi
            else
                # Add new keys
                echo "" >> .env
                echo "# Alpaca API Keys" >> .env
                echo "ALPACA_API_KEY=$api_key" >> .env
                echo "ALPACA_SECRET_KEY=$api_secret" >> .env
                echo "ALPACA_BASE_URL=$base_url" >> .env
            fi
            echo -e "${GREEN}✅ Keys updated in .env file${NC}"
        else
            # Create .env file
            cat > .env << EOF
# Alpaca API Keys
ALPACA_API_KEY=$api_key
ALPACA_SECRET_KEY=$api_secret
ALPACA_BASE_URL=$base_url
EOF
            echo -e "${GREEN}✅ Created .env file with Alpaca keys${NC}"
        fi
        ;;
        
    2)
        echo ""
        read -p "Enter ALPACA_API_KEY: " api_key
        read -sp "Enter ALPACA_SECRET_KEY: " api_secret
        echo ""
        read -p "Enter ALPACA_BASE_URL [https://paper-api.alpaca.markets]: " base_url
        base_url=${base_url:-https://paper-api.alpaca.markets}
        
        export ALPACA_API_KEY="$api_key"
        export ALPACA_SECRET_KEY="$api_secret"
        export ALPACA_BASE_URL="$base_url"
        
        echo -e "${GREEN}✅ Environment variables set for current session${NC}"
        echo ""
        echo "To verify:"
        echo "  echo \$ALPACA_API_KEY"
        ;;
        
    3)
        echo ""
        read -p "Enter ALPACA_API_KEY: " api_key
        read -sp "Enter ALPACA_SECRET_KEY: " api_secret
        echo ""
        read -p "Enter ALPACA_BASE_URL [https://paper-api.alpaca.markets]: " base_url
        base_url=${base_url:-https://paper-api.alpaca.markets}
        
        # Add to venv/bin/activate
        if [ -f "venv/bin/activate" ]; then
            # Check if already exists
            if grep -q "ALPACA_API_KEY" venv/bin/activate; then
                echo "Updating existing keys in venv/bin/activate..."
                # Remove old lines
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    sed -i '' '/^export ALPACA_API_KEY=/d' venv/bin/activate
                    sed -i '' '/^export ALPACA_SECRET_KEY=/d' venv/bin/activate
                    sed -i '' '/^export ALPACA_BASE_URL=/d' venv/bin/activate
                else
                    sed -i '/^export ALPACA_API_KEY=/d' venv/bin/activate
                    sed -i '/^export ALPACA_SECRET_KEY=/d' venv/bin/activate
                    sed -i '/^export ALPACA_BASE_URL=/d' venv/bin/activate
                fi
            fi
            
            # Add new lines before deactivate function
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' '/^deactivate () {/i\
export ALPACA_API_KEY='"$api_key"'
export ALPACA_SECRET_KEY='"$api_secret"'
export ALPACA_BASE_URL='"$base_url"'
' venv/bin/activate
            else
                sed -i '/^deactivate () {/i export ALPACA_API_KEY='"$api_key"'\nexport ALPACA_SECRET_KEY='"$api_secret"'\nexport ALPACA_BASE_URL='"$base_url"'\n' venv/bin/activate
            fi
            
            echo -e "${GREEN}✅ Keys added to venv/bin/activate${NC}"
            echo "Keys will be automatically set when you activate the virtual environment"
        else
            echo "❌ venv/bin/activate not found"
        fi
        ;;
        
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Setup complete!"
echo ""
echo "To verify keys are loaded:"
echo "  python3 -c \"import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', os.getenv('ALPACA_API_KEY')[:10] + '...' if os.getenv('ALPACA_API_KEY') else 'NOT SET')\""
