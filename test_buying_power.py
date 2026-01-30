#!/usr/bin/env python
"""
Test script to check IBKR account info and buying power
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oms.broker_ibkr import IBKRBroker

def test_buying_power():
    print("=" * 70)
    print("IBKR BUYING POWER CHECK")
    print("=" * 70)
    print()
    
    # Connect to IBKR with unique client ID
    print("Connecting to IBKR...")
    broker = IBKRBroker(
        host='127.0.0.1',
        port=4002,
        client_id=88888,  # Unique ID to avoid conflicts
        auto_connect=True
    )
    
    if not broker.connected:
        print("❌ Failed to connect to IBKR")
        return False
    
    print(f"✅ Connected to IBKR")
    print()
    
    # Get raw account values
    print("Getting account values from IBKR...")
    try:
        account_values = broker.ib.accountValues()
        
        print("\n📊 All Account Values:")
        print("-" * 70)
        relevant_keys = ['BuyingPower', 'NetLiquidation', 'CashBalance', 
                        'TotalCashValue', 'AvailableFunds', 'GrossPositionValue']
        
        for av in account_values:
            if av.tag in relevant_keys:
                print(f"  {av.tag:25s}: {av.value:>20s} {av.currency}")
        
        print("\n" + "=" * 70)
        
        # Get account info using broker method
        print("\n🔍 Using broker.get_account_info():")
        print("-" * 70)
        account_info = broker.get_account_info()
        for key, value in account_info.items():
            if isinstance(value, float):
                print(f"  {key:25s}: ${value:>20,.2f}")
            else:
                print(f"  {key:25s}: {value:>20}")
        
        print("\n" + "=" * 70)
        print("\n✅ Summary:")
        print(f"  • Buying Power: ${account_info.get('buying_power', 0):,.2f}")
        print(f"  • Cash Balance: ${account_info.get('cash', 0):,.2f}")
        print(f"  • Total Equity: ${account_info.get('equity', 0):,.2f}")
        print(f"  • Account: {account_info.get('account', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error getting account info: {e}")
        import traceback
        traceback.print_exc()
    
    # Disconnect
    broker.disconnect()
    print("\n✅ Test complete!")
    return True

if __name__ == '__main__':
    try:
        success = test_buying_power()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
