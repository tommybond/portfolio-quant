#!/usr/bin/env python3
"""Test IBKR broker connection"""

import sys
import os
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
print("IBKR CONNECTION TEST")
print("="*60)
print()

# Check if IB Gateway is running
import subprocess
result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
if 'IB Gateway' in result.stdout or 'TWS' in result.stdout:
    print("✓ IB Gateway/TWS process is running")
else:
    print("✗ IB Gateway/TWS process not found")
    print()
    print("Please start IB Gateway or TWS before running this test")
    sys.exit(1)

print()
print("Attempting connection to IBKR...")
print()

try:
    from oms.broker_ibkr import IBKRBroker
    print("✓ IBKRBroker class imported successfully")
    print()
    
    # Try different configurations
    configs = [
        {"host": "127.0.0.1", "port": 4002, "client_id": 12345, "name": "IB Gateway Paper (4002)"},
        {"host": "127.0.0.1", "port": 4001, "client_id": 12345, "name": "IB Gateway Live (4001)"},
        {"host": "127.0.0.1", "port": 7497, "client_id": 12345, "name": "TWS Paper (7497)"},
        {"host": "127.0.0.1", "port": 7496, "client_id": 12345, "name": "TWS Live (7496)"},
    ]
    
    connected = False
    for config in configs:
        print(f"Testing {config['name']}...")
        try:
            broker = IBKRBroker(
                host=config['host'],
                port=config['port'],
                client_id=config['client_id'],
                timeout=3.0,
                auto_connect=False
            )
            
            # Try to connect
            success = broker.connect(timeout=3.0)
            
            if success and broker.ib.isConnected():
                print(f"✅ SUCCESS! Connected to {config['name']}")
                print(f"   Host: {config['host']}")
                print(f"   Port: {config['port']}")
                print(f"   Client ID: {config['client_id']}")
                print()
                
                # Get account info
                try:
                    accounts = broker.ib.managedAccounts()
                    print(f"   Accounts: {accounts}")
                except Exception as e:
                    print(f"   Could not fetch accounts: {e}")
                
                broker.disconnect()
                connected = True
                break
            else:
                print(f"   ✗ Could not connect")
                
        except Exception as e:
            error_msg = str(e)
            if "Connection refused" in error_msg:
                print(f"   ✗ Connection refused - port not listening")
            elif "timeout" in error_msg.lower():
                print(f"   ✗ Connection timeout")
            else:
                print(f"   ✗ Error: {error_msg}")
        
        print()
    
    if not connected:
        print("="*60)
        print("❌ FAILED TO CONNECT")
        print("="*60)
        print()
        print("Troubleshooting steps:")
        print("1. Make sure IB Gateway or TWS is running")
        print("2. Check that API connections are enabled:")
        print("   - In IB Gateway/TWS: File > Global Configuration > API > Settings")
        print("   - Enable 'Enable ActiveX and Socket Clients'")
        print("   - Check the Socket port (usually 4002 for paper, 4001 for live)")
        print("3. Verify the client ID is not already in use")
        print("4. Check firewall settings")
        print()
    
except ImportError as e:
    print(f"✗ Failed to import IBKRBroker: {e}")
    print()
    print("Make sure ib_insync is installed:")
    print("  pip install ib_insync")

except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
