#!/usr/bin/env python3
"""
Test IBKR Broker Connection
Tests connection to TWS/IB Gateway and basic functionality
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def test_ibkr_connection():
    """Test IBKR broker connection and basic operations"""
    print("=" * 60)
    print("IBKR Broker Connection Test")
    print("=" * 60)
    print()
    
    # Check if ib_insync is installed
    try:
        import ib_insync
        print("✅ ib_insync library installed")
        print(f"   Version: {ib_insync.__version__ if hasattr(ib_insync, '__version__') else 'Unknown'}")
    except ImportError:
        print("❌ ib_insync not installed")
        print("   Install with: pip install ib-insync")
        return False
    
    print()
    
    # Check configuration
    host = os.getenv('IBKR_HOST', '127.0.0.1')
    port = int(os.getenv('IBKR_PORT', '7497'))
    client_id = int(os.getenv('IBKR_CLIENT_ID', '1'))
    
    print("Configuration:")
    print(f"  Host: {host}")
    print(f"  Port: {port} ({'Paper Trading' if port == 7497 else 'Live Trading'})")
    print(f"  Client ID: {client_id}")
    print()
    
    # Try to connect
    try:
        from oms.broker_ibkr import IBKRBroker
        
        print("Connecting to TWS/IB Gateway...")
        broker = IBKRBroker(host=host, port=port, client_id=client_id)
        print("✅ Connected successfully!")
        print()
        
        # Test account info
        print("Testing Account Info...")
        try:
            account = broker.get_account_info()
            if account:
                print("✅ Account info retrieved:")
                for key, value in account.items():
                    if isinstance(value, float):
                        print(f"  {key}: ${value:,.2f}")
                    else:
                        print(f"  {key}: {value}")
            else:
                print("⚠️  No account info returned")
        except Exception as e:
            print(f"⚠️  Account info error: {e}")
        
        print()
        
        # Test positions
        print("Testing Positions...")
        try:
            positions = broker.get_positions()
            if positions:
                print(f"✅ Found {len(positions)} position(s):")
                for pos in positions:
                    print(f"  {pos['symbol']}: {pos['quantity']} @ ${pos['average_price']:.2f}")
            else:
                print("✅ No open positions")
        except Exception as e:
            print(f"⚠️  Positions error: {e}")
        
        print()
        
        # Disconnect
        broker.disconnect()
        print("✅ Disconnected successfully")
        print()
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return True
        
    except ConnectionError as e:
        print("❌ Connection failed!")
        print()
        print("Error:", str(e))
        print()
        print("Troubleshooting:")
        print("1. Make sure TWS or IB Gateway is running")
        print("2. Check API connections are enabled:")
        print("   - TWS: Configure → API → Settings")
        print("   - Check: Enable ActiveX and Socket Clients")
        print(f"   - Verify port: {port}")
        print("3. Check firewall allows localhost connections")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_ibkr_connection()
    sys.exit(0 if success else 1)
