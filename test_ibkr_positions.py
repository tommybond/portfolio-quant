#!/usr/bin/env python
"""
Test script to check IBKR positions
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oms.broker_ibkr import IBKRBroker

def test_positions():
    print("=" * 60)
    print("IBKR POSITIONS TEST")
    print("=" * 60)
    print()
    
    # Connect to IBKR
    print("Connecting to IBKR...")
    broker = IBKRBroker(
        host='127.0.0.1',
        port=4002,
        client_id=99997,
        auto_connect=True
    )
    
    if not broker.connected:
        print("❌ Failed to connect to IBKR")
        return False
    
    print(f"✅ Connected to IBKR")
    print()
    
    # Get account info
    print("Getting account info...")
    account_info = broker.get_account_info()
    if account_info:
        print(f"  Account: {account_info.get('account', 'N/A')}")
        print(f"  Buying Power: ${account_info.get('buying_power', 0):,.2f}")
        print(f"  Cash: ${account_info.get('cash', 0):,.2f}")
        print(f"  Equity: ${account_info.get('equity', 0):,.2f}")
    print()
    
    # Get positions
    print("Getting positions...")
    positions = broker.get_positions()
    
    if not positions:
        print("  ⚠️ No open positions found")
        print()
        print("  This is normal if you haven't placed any orders yet.")
        print("  The test order (AAPL x1) was cancelled, so it won't show as a position.")
        print()
        print("  To see positions, you need to:")
        print("  1. Go to Streamlit app")
        print("  2. Enter a ticker and prepare orders")
        print("  3. Click 'EXECUTE BUY' to place real orders")
        print("  4. Don't cancel them - let them fill")
    else:
        print(f"  ✅ Found {len(positions)} position(s):")
        for pos in positions:
            print(f"    • {pos['symbol']}: {pos['quantity']} shares @ ${pos['average_price']:.2f}")
            print(f"      Current Price: ${pos['current_price']:.2f}")
            print(f"      Market Value: ${pos['market_value']:.2f}")
            print(f"      P&L: ${pos['unrealized_pnl']:.2f}")
            print()
    
    # Disconnect
    broker.disconnect()
    print("✅ Test complete!")
    return True

if __name__ == '__main__':
    try:
        success = test_positions()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
