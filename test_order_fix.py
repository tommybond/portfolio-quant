#!/usr/bin/env python
"""
Test script to verify orders placed in UI are now reflected in IBKR
Tests the fix for: orders showing as submitted but not appearing in IBKR
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oms.broker_ibkr import IBKRBroker
from oms.oms import OrderManager, OrderType, Order

def test_order_submission():
    """Test that orders are properly submitted to IBKR"""
    print("=" * 80)
    print("IBKR ORDER SUBMISSION FIX TEST")
    print("=" * 80)
    print()
    
    # Step 1: Connect to IBKR
    print("Step 1: Connecting to IBKR...")
    broker = IBKRBroker(
        host='127.0.0.1',
        port=4002,
        client_id=88888,  # Using unique client ID
        auto_connect=True
    )
    
    if not broker.connected:
        print("❌ Failed to connect to IBKR")
        print("   Make sure TWS or IB Gateway is running on port 4002")
        return False
    
    print(f"✅ Connected to IBKR successfully")
    print()
    
    # Get account info
    account_info = broker.get_account_info()
    print(f"Account Information:")
    print(f"   Account: {account_info.get('account', 'N/A')}")
    print(f"   Buying Power: ${account_info.get('buying_power', 0):,.2f}")
    print()
    
    # Step 2: Create OrderManager
    print("Step 2: Initializing OrderManager with IBKR broker...")
    oms = OrderManager(broker=broker)
    print(f"✅ OrderManager initialized")
    print()
    
    # Step 3: Create and submit test order
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
    
    # Step 4: Submit order
    print("Step 4: Submitting order through OMS...")
    print("-" * 80)
    try:
        submitted_order = oms.create_order(order=order, user_id=1)
        print("-" * 80)
        print()
        
        print("✅ OMS.create_order completed!")
        print(f"   Order Status: {submitted_order.status.value}")
        print(f"   Broker Order ID: {submitted_order.broker_order_id}")
        
        if submitted_order.rejection_reason:
            print(f"   Rejection Reason: {submitted_order.rejection_reason}")
        print()
        
        # Step 5: Verify order in IBKR
        print("Step 5: Verifying order in IBKR system...")
        
        # Check open orders
        open_orders = broker.ib.openOrders()
        print(f"   Open Orders in IBKR: {len(open_orders)}")
        
        # Check all trades
        all_trades = broker.ib.trades()
        print(f"   Total Trades in IBKR: {len(all_trades)}")
        print()
        
        # Find our order
        found_order = False
        if submitted_order.broker_order_id:
            order_id_str = str(submitted_order.broker_order_id)
            print(f"   Looking for Order ID: {order_id_str}")
            
            for trade in all_trades:
                if str(trade.order.orderId) == order_id_str:
                    found_order = True
                    print(f"   ✅ FOUND ORDER IN IBKR!")
                    print(f"      Order ID: {trade.order.orderId}")
                    print(f"      Symbol: {trade.contract.symbol}")
                    print(f"      Action: {trade.order.action}")
                    print(f"      Quantity: {trade.order.totalQuantity}")
                    print(f"      Status: {trade.orderStatus.status}")
                    break
            
            if not found_order:
                print(f"   ⚠️  Order not found in IBKR trades list")
        else:
            print(f"   ⚠️  No broker order ID - order may not have been submitted")
        print()
        
        # Display all open orders for debugging
        if open_orders:
            print("   All Open Orders in IBKR:")
            for i, order in enumerate(open_orders, 1):
                print(f"      {i}. ID={order.orderId}, {order.contract.symbol}, "
                      f"{order.action} {order.totalQuantity}")
            print()
        
        # Step 6: Determine test result
        print("=" * 80)
        print("TEST RESULTS:")
        print("=" * 80)
        
        if submitted_order.status.value == 'REJECTED':
            print("❌ TEST FAILED: Order was rejected")
            print(f"   Rejection Reason: {submitted_order.rejection_reason}")
            success = False
        elif not submitted_order.broker_order_id:
            print("❌ TEST FAILED: No broker order ID assigned")
            success = False
        elif not found_order:
            print("⚠️  TEST INCOMPLETE: Order submitted but not found in IBKR")
            print("   This may be due to timing - order might be processing")
            success = False
        else:
            print("✅ TEST PASSED: Order successfully submitted and found in IBKR!")
            success = True
        
        print()
        
        # Step 7: Cancel test order
        if submitted_order.broker_order_id and found_order:
            print("Step 7: Cancelling test order...")
            try:
                cancel_result = oms.cancel_order(str(submitted_order.broker_order_id))
                if cancel_result:
                    print("✅ Test order cancelled successfully")
                else:
                    print("⚠️  Could not cancel order (may already be filled)")
            except Exception as e:
                print(f"⚠️  Cancel failed: {e}")
            print()
        
        return success
        
    except Exception as e:
        print(f"❌ TEST FAILED: Exception occurred")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Disconnect
        print("Disconnecting from IBKR...")
        broker.disconnect()
        print("✅ Disconnected")
        print()

if __name__ == "__main__":
    success = test_order_submission()
    sys.exit(0 if success else 1)
