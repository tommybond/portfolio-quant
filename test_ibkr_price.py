#!/usr/bin/env python
"""
Test script to verify IBKR price fetching works correctly
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oms.broker_ibkr import IBKRBroker

def test_price_fetching():
    print("=" * 60)
    print("IBKR PRICE FETCHING TEST")
    print("=" * 60)
    print()
    
    # Connect to IBKR
    print("Connecting to IBKR...")
    broker = IBKRBroker(
        host='127.0.0.1',
        port=4002,
        client_id=99998,  # Different from main app
        auto_connect=True
    )
    
    if not broker.connected:
        print("❌ Failed to connect to IBKR")
        return False
    
    print(f"✅ Connected to IBKR")
    print()
    
    # Test symbols
    test_symbols = ['AAPL', 'GOOGL', 'MSFT']
    
    for symbol in test_symbols:
        print(f"Testing {symbol}...")
        price_data = broker.get_current_price(symbol)
        
        if price_data:
            print(f"  ✅ Price fetched successfully!")
            print(f"     Price: ${price_data.get('price', 'N/A'):.2f}")
            if 'bid' in price_data:
                print(f"     Bid: ${price_data['bid']:.2f}")
            if 'ask' in price_data:
                print(f"     Ask: ${price_data['ask']:.2f}")
            if 'last' in price_data:
                print(f"     Last: ${price_data['last']:.2f}")
            
            # Check for NaN
            if price_data['price'] and price_data['price'] > 0:
                print(f"     ✅ Valid price (not NaN)")
            else:
                print(f"     ❌ Invalid price or NaN!")
        else:
            print(f"  ❌ Failed to fetch price")
        print()
    
    # Disconnect
    broker.disconnect()
    print("✅ Test complete!")
    return True

if __name__ == '__main__':
    try:
        success = test_price_fetching()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
