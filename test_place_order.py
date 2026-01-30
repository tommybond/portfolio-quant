#!/usr/bin/env python3
"""
Test script to place an actual order to IBKR and verify it works
CAUTION: This will place a REAL order to IBKR Paper Trading account
"""

import os
import sys
import time

print("=" * 70)
print("IBKR ORDER PLACEMENT TEST")
print("=" * 70)
print()
print("⚠️  WARNING: This script will place a REAL order to IBKR")
print("   Account: Paper Trading (DUO515022)")
print("   Symbol: AAPL")
print("   Quantity: 1 share")
print("   Type: MARKET order")
print()
response = input("Continue? (yes/no): ")
if response.lower() != 'yes':
    print("❌ Aborted by user")
    sys.exit(0)

print("\n" + "=" * 70)
print("STEP 1: Initialize IBKR Broker")
print("=" * 70)

try:
    from oms.broker_ibkr import IBKRBroker
    
    broker = IBKRBroker(
        host='127.0.0.1',
        port=4002,
        client_id=99999,  # Use high client ID to avoid conflicts
        auto_connect=True
    )
    
    if not broker.connected:
        print("❌ Failed to connect to IBKR")
        print(f"   Error: {broker._last_connect_error}")
        sys.exit(1)
    
    print(f"✅ Connected to IBKR")
    print(f"   Host: {broker.host}:{broker.port}")
    print(f"   Client ID: {broker.client_id}")
    
    # Get account info
    account_info = broker.get_account_info()
    if account_info:
        print(f"✅ Account: {account_info.get('account')}")
        print(f"   Buying Power: ${account_info.get('buying_power', 0):,.2f}")
    
except Exception as e:
    print(f"❌ Error initializing broker: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("STEP 2: Create Order via OMS")
print("=" * 70)

try:
    from oms.oms import OrderManager, Order, OrderType, OrderStatus
    
    # Create a small market order for testing
    test_order = Order(
        symbol='AAPL',
        side='BUY',
        quantity=1,  # Just 1 share for testing
        order_type=OrderType.MARKET,
        time_in_force='DAY'
    )
    
    print(f"✅ Order created:")
    print(f"   Symbol: {test_order.symbol}")
    print(f"   Side: {test_order.side}")
    print(f"   Quantity: {test_order.quantity}")
    print(f"   Type: {test_order.order_type.value}")
    print(f"   Status: {test_order.status.value}")
    
except Exception as e:
    print(f"❌ Error creating order: {e}")
    broker.disconnect()
    sys.exit(1)

print("\n" + "=" * 70)
print("STEP 3: Submit Order to IBKR via OMS")
print("=" * 70)

try:
    # Create OMS with broker
    oms = OrderManager(broker=broker)
    user_id = 1  # Test user ID
    
    print("📤 Submitting order to OMS...")
    submitted_order = oms.create_order(test_order, user_id)
    
    print(f"\n✅ Order submitted!")
    print(f"   Status: {submitted_order.status.value}")
    print(f"   Broker Order ID: {submitted_order.broker_order_id or 'PENDING'}")
    
    if submitted_order.rejection_reason:
        print(f"   ⚠️  Rejection Reason: {submitted_order.rejection_reason}")
    
    # Check if order was accepted
    if submitted_order.status == OrderStatus.REJECTED:
        print(f"\n❌ Order was REJECTED by broker")
        print(f"   Reason: {submitted_order.rejection_reason}")
        broker.disconnect()
        sys.exit(1)
    elif submitted_order.status in [OrderStatus.SUBMITTED, OrderStatus.PENDING]:
        print(f"\n✅ Order ACCEPTED by broker!")
        order_id = submitted_order.broker_order_id
    else:
        print(f"\n⚠️  Unexpected status: {submitted_order.status.value}")
        order_id = submitted_order.broker_order_id
    
except Exception as e:
    print(f"\n❌ Error submitting order: {e}")
    import traceback
    traceback.print_exc()
    broker.disconnect()
    sys.exit(1)

print("\n" + "=" * 70)
print("STEP 4: Check Order Status")
print("=" * 70)

if order_id:
    try:
        print(f"Checking status for order ID: {order_id}")
        time.sleep(1)  # Wait a bit for order to be processed
        
        order_status = oms.get_order_status(order_id)
        if order_status:
            print(f"✅ Order Status Retrieved:")
            print(f"   Status: {order_status.status.value}")
            print(f"   Filled Quantity: {order_status.filled_quantity}")
            if order_status.average_fill_price:
                print(f"   Avg Fill Price: ${order_status.average_fill_price:.2f}")
        else:
            print(f"⚠️  Could not retrieve order status")
        
    except Exception as e:
        print(f"⚠️  Error checking order status: {e}")
else:
    print("⚠️  No order ID available to check status")

print("\n" + "=" * 70)
print("STEP 5: Cancel Order (Safety)")
print("=" * 70)

if order_id:
    print(f"Attempting to cancel order {order_id}...")
    try:
        cancelled = oms.cancel_order(order_id)
        if cancelled:
            print(f"✅ Order cancelled successfully")
        else:
            print(f"⚠️  Order could not be cancelled (may already be filled)")
    except Exception as e:
        print(f"⚠️  Error cancelling order: {e}")
else:
    print("⚠️  No order ID to cancel")

print("\n" + "=" * 70)
print("STEP 6: View Open Trades")
print("=" * 70)

try:
    print("Checking for open trades...")
    open_trades = broker.ib.openTrades()
    
    if open_trades:
        print(f"📊 Found {len(open_trades)} open trade(s):")
        for i, trade in enumerate(open_trades, 1):
            print(f"\n   Trade {i}:")
            print(f"   Order ID: {trade.order.orderId}")
            print(f"   Symbol: {trade.contract.symbol}")
            print(f"   Action: {trade.order.action}")
            print(f"   Quantity: {trade.order.totalQuantity}")
            print(f"   Status: {trade.orderStatus.status}")
    else:
        print("✅ No open trades (order was cancelled or filled)")
        
except Exception as e:
    print(f"⚠️  Error checking open trades: {e}")

print("\n" + "=" * 70)
print("STEP 7: Cleanup & Summary")
print("=" * 70)

broker.disconnect()
print("✅ Disconnected from IBKR")

print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)

if submitted_order.status in [OrderStatus.SUBMITTED, OrderStatus.PENDING, OrderStatus.CANCELLED]:
    print("✅ ✅ ✅ ORDER PLACEMENT TEST PASSED! ✅ ✅ ✅")
    print()
    print("Results:")
    print(f"  - Connection: ✅ SUCCESS")
    print(f"  - Order Creation: ✅ SUCCESS")
    print(f"  - Order Submission: ✅ SUCCESS")
    print(f"  - Broker Accepted: ✅ YES")
    print(f"  - Order ID: {order_id}")
    print(f"  - Final Status: {submitted_order.status.value}")
    print()
    print("🎉 The order placement flow is working correctly!")
    print("   You can now use the Streamlit UI to place orders.")
else:
    print("⚠️  TEST COMPLETED WITH WARNINGS")
    print(f"   Final Status: {submitted_order.status.value}")
    if submitted_order.rejection_reason:
        print(f"   Reason: {submitted_order.rejection_reason}")

print()
print("=" * 70)
