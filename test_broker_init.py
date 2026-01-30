#!/usr/bin/env python3
"""
Test the updated get_broker_instance function
"""

import sys
import asyncio

# Ensure event loop
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Add project to path
sys.path.insert(0, '/Users/naisha/nashor-workspace/portfolio-quant')

print("="*60)
print("TESTING UPDATED BROKER INITIALIZATION")
print("="*60)
print()

try:
    from oms.broker_ibkr import IBKRBroker
    
    print("1. Testing IBKRBroker with auto_connect=False...")
    broker = IBKRBroker(client_id=12345, auto_connect=False)
    print(f"   Created broker instance")
    print(f"   Connected: {broker.ib.isConnected()}")
    print()
    
    print("2. Manually calling connect()...")
    try:
        broker.connect(timeout=3.0)
        print(f"   ✅ Connection successful!")
        print(f"   Connected: {broker.ib.isConnected()}")
        print(f"   Host: {broker.host}")
        print(f"   Port: {broker.port}")
        
        # Get accounts
        try:
            accounts = broker.ib.managedAccounts()
            print(f"   Accounts: {accounts}")
        except Exception as e:
            print(f"   Accounts error: {e}")
        
        broker.disconnect()
        print(f"   Disconnected: {not broker.ib.isConnected()}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    
    print()
    print("="*60)
    print("TEST COMPLETE")
    print("="*60)
    print()
    print("The updated app.py should now:")
    print("1. Create IBKRBroker instance")
    print("2. Automatically attempt to connect")
    print("3. Show connection status in the UI")
    print("4. Provide a 'Connect' button to retry connection")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
