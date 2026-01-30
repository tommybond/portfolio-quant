#!/bin/bash
# Set HEADLESS_LOGIN environment variable

# Export for current session
export HEADLESS_LOGIN=true

# Also update .env file
cd "$(dirname "$0")" || exit
if [ -f ".env" ]; then
    # Check if HEADLESS_LOGIN exists in .env
    if grep -q "^HEADLESS_LOGIN=" .env; then
        # Update existing line
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' 's/^HEADLESS_LOGIN=.*/HEADLESS_LOGIN=true/' .env
        else
            sed -i 's/^HEADLESS_LOGIN=.*/HEADLESS_LOGIN=true/' .env
        fi
    else
        # Add new line
        echo "HEADLESS_LOGIN=true" >> .env
    fi
    echo "✅ Updated .env file: HEADLESS_LOGIN=true"
else
    echo "⚠️  .env file not found. Creating it..."
    echo "HEADLESS_LOGIN=true" > .env
    echo "✅ Created .env file with HEADLESS_LOGIN=true"
fi

echo "✅ HEADLESS_LOGIN=true is now set"
echo ""
echo "To use in current shell session:"
echo "  export HEADLESS_LOGIN=true"
echo ""
echo "To make permanent, add to ~/.zshrc or ~/.bash_profile:"
echo "  echo 'export HEADLESS_LOGIN=true' >> ~/.zshrc"
echo "  source ~/.zshrc"
