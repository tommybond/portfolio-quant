#!/usr/bin/env python3
"""Test Indian stock order retrieval from IBKR with updated code."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oms.broker_ibkr import IBKRBroker
import time

def main():
    print("🔍 Testing Indian Stock (SBIN.NS) visibility in IBKR\n")
    print("="*70)
    
    try:
        broker = IBKRBroker()
        
        print("🔌 Connecting to IBKR...")
        if not broker.connect():
            print("❌ Failed to connect to IBKR")
            print("   Make sure TWS/IB Gateway is running")
            return
        
        print("✅ Connected to IBKR\n")
        time.sleep(2)
        
        # Test 1: Get all orders
        print("="*70)
        print("📋 TEST 1: Getting all orders...")
        print("-"*70)
        
        orders = broker.get_orders()
        print(f"✅ Retrieved {len(orders)} order(s)\n")
        
        if orders:
            for idx, order in enumerate(orders, 1):
                print(f"Order #{idx}:")
                print(f"  Symbol: {order['symbol']}")
                print(f"  Order ID: {order['order_id']}")
                print(f"  Side: {order['side']}")
                print(f"  Quantity: {order['quantity']}")
                print(f"  Status: {order['status']}")
                print()
                
                if order['symbol'] == 'SBIN.NS':
                    print("  ✅ FOUND SBIN.NS ORDER!")
                    print()
        else:
            print("⚠️ No active orders found")
        
        # Test 2: Get all positions
        print("="*70)
        print("📊 TEST 2: Getting all positions...")
        print("-"*70)
        
        positions = broker.get_positions()
        print(f"✅ Retrieved {len(positions)} position(s)\n")
        
        if positions:
            for idx, pos in enumerate(positions, 1):
                print(f"Position #{idx}:")
                print(f"  Symbol: {pos['symbol']}")
                print(f"  Quantity: {pos['quantity']}")
                print(f"  Avg Price: {pos['average_price']:.2f}")
                print(f"  Current Price: {pos['current_price']:.2f}")
                print()
                
                if pos['symbol'] == 'SBIN.NS':
                    print("  ✅ FOUND SBIN.NS POSITION!")
                    print()
        else:
            print("⚠️ No positions found")
        
        # Test 3: Check specific order status
        print("="*70)
        print("🔍 TEST 3: Checking Order #256 status...")
        print("-"*70)
        
        order_status = broker.get_order_status('256')
        if order_status and order_status.get('status') != 'NOT_FOUND':
            print(f"✅ Order #256 found:")
            print(f"  Status: {order_status.get('status')}")
            print(f"  Filled: {order_status.get('filled_quantity', 0)}")
            print(f"  Remaining: {order_status.get('remaining_quantity', 0)}")
            if order_status.get('average_fill_price'):
                print(f"  Avg Fill Price: ₹{order_status.get('average_fill_price'):.2f}")
        else:
            print("⚠️ Order #256 not found in active orders")
            print("   This could mean:")
            print("   - Order was filled and is now a position")
            print("   - Order was cancelled")
            print("   - Order is queued for Monday market open")
        
        print("\n" + "="*70)
        print("✅ Tests completed!")
        
        broker.disconnect()
        print("✅ Disconnected from IBKR")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
