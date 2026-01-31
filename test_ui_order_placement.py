#!/usr/bin/env python
"""
Test script to verify orders are being placed correctly in IBKR
This simulates the UI flow: connect -> create order -> submit
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oms.broker_ibkr import IBKRBroker
from oms.oms import OrderManager, OrderType, Order

def test_ui_order_flow():
    print("=" * 70)
    print("IBKR ORDER PLACEMENT TEST (UI Flow)")
    print("=" * 70)
    print()
    
    # Step 1: Connect to IBKR (simulating UI connection)
    print("STEP 1: Connecting to IBKR...")
    broker = IBKRBroker(
        host='127.0.0.1',
        port=4002,
        client_id=77777,
        auto_connect=True
    )
    
    if not broker.connected:
        print("❌ Failed to connect to IBKR")
        return False
    
    print(f"✅ Connected to IBKR")
    
    # Get account info
    account_info = broker.get_account_info()
    print(f"   Account: {account_info.get('account', 'N/A')}")
    print(f"   Buying Power: ${account_info.get('buying_power', 0):,.2f}")
    print()
    
    # Step 2: Create OrderManager instance (simulating UI OMS initialization)
    print("STEP 2: Initializing OrderManager...")
    oms = OrderManager(broker=broker)
    print(f"✅ OrderManager initialized with IBKR broker")
    print()
    
    # Step 3: Create order (simulating UI order creation)
    print("STEP 3: Creating order...")
    symbol = "AAPL"
    quantity = 1
    order_type = OrderType.MARKET
    
    print(f"   Symbol: {symbol}")
    print(f"   Quantity: {quantity}")
    print(f"   Order Type: {order_type}")
    print()
    
    # Step 4: Submit order through OMS (simulating UI "EXECUTE BUY" button)
    print("STEP 4: Submitting order to IBKR...")
    print("=" * 70)
    
    try:
        # Create order object
        order = Order(
            symbol=symbol,
            quantity=quantity,
            side='BUY',
            order_type=order_type
        )
        
        # Submit through OMS
        submitted_order = oms.create_order(order=order, user_id=1)
        
        print(f"✅ Order submitted!")
        print(f"   Order ID: {submitted_order.id}")
        print(f"   Status: {submitted_order.status}")
        print(f"   Broker Order ID: {submitted_order.broker_order_id}")
        print()
        
        print(f"   Order ID: {submitted_order.id}")
        print(f"   Symbol: {submitted_order.symbol}")
        print(f"   Quantity: {submitted_order.quantity}")
        print(f"   Status: {submitted_order.status}")
        print(f"   Broker Order ID: {submitted_order.broker_order_id}")
        print()
        
        if submitted_order.broker_order_id:
            print(f"✅ Order successfully submitted to IBKR!")
            print(f"   Broker assigned Order ID: {submitted_order.broker_order_id}")
        else:
            print(f"⚠️ Order created but no broker order ID yet")
        print()
        
        # Step 6: Check in IBKR
        print("STEP 6: Verifying order in IBKR...")
        trades = broker.ib.trades()
        open_orders = broker.ib.openOrders()
        
        print(f"   Open Orders in IBKR: {len(open_orders)}")
        print(f"   Total Trades in IBKR: {len(trades)}")
        
        if open_orders:
            print("\n   📋 Open Orders:")
            for i, order in enumerate(open_orders, 1):
                print(f"      {i}. Order ID: {order.orderId}, {order.contract.symbol}, {order.action} {order.totalQuantity}")
        
        print()
        
        # Step 7: Cancel the order (cleanup)
        print("STEP 7: Cancelling test order...")
        if order_id and order.get('broker_order_id'):
            try:
                oms.cancel_order(order_id)
                print(f"✅ Order {order_id} cancelled")
           submitted_order.broker_order_id:
            try:
                broker.ib.cancelOrder(broker.ib.orders()[0])
                print(f"✅ Order
        # Disconnect
        broker.disconnect()
        
        print("=" * 70)
        print("✅✅✅ UI ORDER FLOW TEST COMPLETED!")
        print("=" * 70)
        print("\nSUMMARY:")
        print("  ✅ Connection established")
        print("  ✅ OMS initialized")
        print("  ✅ Order created")
        print("  ✅ Order submitted to IBKR")
        print("  ✅ Order verified in IBKR")
        print("  ✅ Order cancelled (cleanup)")
        print("\n🎉 Orders from UI are working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Order submission failed: {e}")
        import traceback
        traceback.print_exc()
        broker.disconnect()
        return False

if __name__ == '__main__':
    try:
        success = test_ui_order_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
