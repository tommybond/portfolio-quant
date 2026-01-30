#!/usr/bin/env python
"""
Quick test to place an order and verify it appears in IBKR
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oms.broker_ibkr import IBKRBroker
from oms.oms import OrderManager, OrderType, Order

print("=" * 80)
print("PLACING TEST ORDER TO IBKR")
print("=" * 80)
print()

# Connect to IBKR
print("Step 1: Connecting to IBKR...")
broker = IBKRBroker(
    host='127.0.0.1',
    port=4002,
    client_id=99999,  # Unique client ID
    auto_connect=True
)

if not broker.connected:
    print("❌ Failed to connect to IBKR")
    print("   Make sure TWS or IB Gateway is running on port 4002")
    sys.exit(1)

print(f"✅ Connected to IBKR")
print()

# Get account info
account_info = broker.get_account_info()
print(f"Account: {account_info.get('account', 'N/A')}")
print(f"Buying Power: ${account_info.get('buying_power', 0):,.2f}")
print()

# Create OrderManager
print("Step 2: Creating OrderManager...")
oms = OrderManager(broker=broker)
print(f"✅ OrderManager initialized")
print()

# Create test order (AAPL - 1 share)
print("Step 3: Creating test order (AAPL BUY 1 MARKET)...")
order = Order(
    symbol="AAPL",
    quantity=1,
    side='BUY',
    order_type=OrderType.MARKET,
    time_in_force='DAY'
)

print(f"   Symbol: {order.symbol}")
print(f"   Side: {order.side}")
print(f"   Quantity: {order.quantity}")
print(f"   Type: {order.order_type.value}")
print()

# Submit order
print("Step 4: Submitting order to IBKR...")
print("-" * 80)
try:
    submitted_order = oms.create_order(order=order, user_id=1)
    print("-" * 80)
    print()
    
    print("✅ Order submission completed!")
    print(f"   Status: {submitted_order.status.value}")
    print(f"   Broker Order ID: {submitted_order.broker_order_id}")
    
    if submitted_order.rejection_reason:
        print(f"   ⚠️ Rejection Reason: {submitted_order.rejection_reason}")
    print()
    
    # Verify in IBKR
    print("Step 5: Verifying order in IBKR...")
    import time
    time.sleep(2)  # Wait a bit for order to settle
    
    all_trades = broker.ib.trades()
    open_orders = broker.ib.openOrders()
    
    print(f"   Open Orders: {len(open_orders)}")
    print(f"   Total Trades: {len(all_trades)}")
    print()
    
    # Find our order
    if submitted_order.broker_order_id:
        order_id_str = str(submitted_order.broker_order_id)
        found = False
        
        for trade in all_trades:
            if str(trade.order.orderId) == order_id_str:
                found = True
                print(f"✅ ORDER FOUND IN IBKR!")
                print(f"   Order ID: {trade.order.orderId}")
                print(f"   Symbol: {trade.contract.symbol}")
                print(f"   Action: {trade.order.action}")
                print(f"   Quantity: {trade.order.totalQuantity}")
                print(f"   Status: {trade.orderStatus.status}")
                print()
                break
        
        if not found:
            print(f"⚠️ Order ID {order_id_str} not found in IBKR trades list")
            print("   This could be normal if order was immediately filled and cleared")
            print()
    
    # List all open orders
    if open_orders:
        print("All Open Orders in IBKR:")
        for i, order in enumerate(open_orders, 1):
            print(f"   {i}. ID={order.orderId}, {order.contract.symbol}, "
                  f"{order.action} {order.totalQuantity}, Status={order.orderStatus.status}")
    
    print()
    print("=" * 80)
    if submitted_order.status.value in ['SUBMITTED', 'PENDING', 'FILLED']:
        print("✅ SUCCESS: Order was accepted by IBKR!")
    else:
        print(f"❌ Order status: {submitted_order.status.value}")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    print()
    print("Disconnecting...")
    broker.disconnect()
    print("✅ Done")
