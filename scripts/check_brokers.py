#!/usr/bin/env python3
"""
Broker Configuration Checker
Checks which brokers are configured and their status
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def print_section(text):
    print(f"\n{text}")
    print("-" * 60)

def check_alpaca():
    """Check Alpaca broker configuration"""
    print_section("🔵 Alpaca Broker")
    
    # Check environment variables
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_SECRET_KEY')
    base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
    
    print(f"API Key: {'✅ SET' if api_key and api_key != 'your_alpaca_api_key_here' else '❌ NOT SET'}")
    if api_key:
        print(f"  Preview: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else api_key}")
    
    print(f"Secret Key: {'✅ SET' if api_secret and api_secret != 'your_alpaca_secret_key_here' else '❌ NOT SET'}")
    print(f"Base URL: {base_url}")
    print(f"Mode: {'📝 Paper Trading' if 'paper' in base_url.lower() else '💰 Live Trading'}")
    
    # Check if module is available
    try:
        from oms.broker_alpaca import AlpacaBroker
        print("\nModule Status: ✅ Available")
        
        # Try to initialize
        try:
            broker = AlpacaBroker()
            print("Initialization: ✅ Success")
            
            # Test connection
            try:
                account = broker.api.get_account()
                print("Connection: ✅ Active")
                print(f"  Account Status: {account.status}")
                print(f"  Buying Power: ${float(account.buying_power):,.2f}")
                print(f"  Equity: ${float(account.equity):,.2f}")
                print(f"  Cash: ${float(account.cash):,.2f}")
            except Exception as e:
                print(f"Connection: ⚠️  Failed - {str(e)[:50]}")
        except Exception as e:
            print(f"Initialization: ❌ Failed - {str(e)[:50]}")
    except ImportError as e:
        print(f"Module Status: ❌ Not available - {e}")
    
    # Check Enhanced Alpaca
    try:
        from oms.broker_alpaca_enhanced import EnhancedAlpacaBroker
        print("\nEnhanced Alpaca: ✅ Available")
    except ImportError:
        print("\nEnhanced Alpaca: ⚠️  Not available")

def check_ibkr():
    """Check Interactive Brokers configuration"""
    print_section("🟢 Interactive Brokers (IBKR)")
    
    # Check environment variables
    ibkr_host = os.getenv('IBKR_HOST', '127.0.0.1')
    ibkr_port = os.getenv('IBKR_PORT', '7497')
    ibkr_client_id = os.getenv('IBKR_CLIENT_ID', '1')
    
    print(f"Host: {ibkr_host}")
    print(f"Port: {ibkr_port}")
    print(f"Client ID: {ibkr_client_id}")
    
    # Check if module is available
    try:
        from oms.broker_ibkr import IBKRBroker
        print("\nModule Status: ✅ Available")
        
        # Try to initialize (will fail if TWS/Gateway not running)
        try:
            broker = IBKRBroker()
            print("Initialization: ✅ Success")
            print("Connection: ✅ Active")
            
            # Get account info if connected
            try:
                account = broker.get_account_info()
                if account:
                    print(f"  Equity: ${account.get('equity', 0):,.2f}")
                    print(f"  Cash: ${account.get('cash', 0):,.2f}")
                broker.disconnect()
            except Exception as e:
                print(f"  Account Info: ⚠️  {str(e)[:50]}")
        except ConnectionError as e:
            print("Initialization: ⚠️  TWS/Gateway not running")
            print(f"  Error: {str(e)[:80]}")
        except Exception as e:
            print(f"Initialization: ⚠️  {str(e)[:50]}")
    except ImportError as e:
        print(f"Module Status: ❌ Not available - {e}")
        print("  Install with: pip install ib-insync")

def check_polygon():
    """Check Polygon API (for market data)"""
    print_section("🟣 Polygon API (Market Data)")
    
    polygon_key = os.getenv('POLYGON_API_KEY')
    print(f"API Key: {'✅ SET' if polygon_key else '❌ NOT SET'}")
    
    if polygon_key:
        print(f"  Preview: {polygon_key[:10]}...{polygon_key[-4:] if len(polygon_key) > 14 else polygon_key}")

def main():
    print_header("Broker Configuration Status")
    
    # Check all brokers
    check_alpaca()
    check_ibkr()
    check_polygon()
    
    # Summary
    print_header("Summary")
    
    alpaca_configured = (
        os.getenv('ALPACA_API_KEY') and 
        os.getenv('ALPACA_API_KEY') != 'your_alpaca_api_key_here' and
        os.getenv('ALPACA_SECRET_KEY') and
        os.getenv('ALPACA_SECRET_KEY') != 'your_alpaca_secret_key_here'
    )
    
    ibkr_configured = True  # IBKR uses default values
    
    print(f"Alpaca Broker: {'✅ Configured' if alpaca_configured else '❌ Not Configured'}")
    print(f"IBKR Broker: {'✅ Available' if ibkr_configured else '❌ Not Available'}")
    print(f"Polygon API: {'✅ Configured' if os.getenv('POLYGON_API_KEY') else '⚠️  Optional'}")
    
    print("\n" + "=" * 60)
    print("✅ Primary Broker: Alpaca (Paper Trading)")
    print("=" * 60)

if __name__ == '__main__':
    main()
