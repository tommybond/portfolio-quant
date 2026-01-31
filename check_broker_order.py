#!/usr/bin/env python3
"""Check SBIN.NS order status directly from IBKR broker."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oms.broker_ibkr import IBKRBroker
import time

def main():
    print("🔍 Checking SBIN.NS Order #256 status from IBKR broker...\n")
    print("="*70)
    
    try:
        # Connect to IBKR
        broker = IBKRBroker()
        
        print("🔌 Connecting to IBKR...")
        if not broker.connect():
            print("❌ Failed to connect to IBKR")
            print("   Make sure TWS/IB Gateway is running and IBKR_HOST/IBKR_PORT are set")
            return
        
        print("✅ Connected to IBKR successfully\n")
        time.sleep(2)  # Give connection time to stabilize
        
        # Get all orders
        print("📋 Fetching all orders from IBKR...")
        orders = broker.get_orders()
        
        print(f"✅ Retrieved {len(orders)} order(s)\n")
        print("="*70)
        
        # Find SBIN.NS orders
        sbin_orders = [o for o in orders if o.get('symbol') == 'SBIN.NS']
        
        if sbin_orders:
            print(f"📊 FOUND {len(sbin_orders)} SBIN.NS ORDER(S):\n")
            
            for idx, order in enumerate(sbin_orders, 1):
                print(f"Order #{idx}:")
                print("-"*70)
                print(f"  Order ID: {order.get('order_id', 'N/A')}")
                print(f"  Symbol: {order.get('symbol', 'N/A')}")
                print(f"  Side: {order.get('side', 'N/A')}")
                print(f"  Quantity: {order.get('quantity', 0)} shares")
                print(f"  Order Type: {order.get('order_type', 'N/A')}")
                print(f"  Status: {order.get('status', 'UNKNOWN')}")
                print(f"  Filled Quantity: {order.get('filled_quantity', 0)} shares")
                print(f"  Remaining: {order.get('remaining_quantity', 0)} shares")
                
                if order.get('average_fill_price'):
                    print(f"  Avg Fill Price: ₹{order.get('average_fill_price'):.2f}")
                
                if order.get('submitted_at'):
                    print(f"  Submitted At: {order.get('submitted_at')}")
                
                print()
                
                # Check if this is order #256
                if str(order.get('order_id')) == '256':
                    print("  ✅ This is the order we're tracking (ID: 256)\n")
        else:
            print("⚠️ No SBIN.NS orders found in active orders list\n")
            print("This could mean:")
            print("  1. Order was filled and is now a position")
            print("  2. Order was cancelled")
            print("  3. Order is in a different state\n")
        
        # Check positions
        print("="*70)
        print("📊 Checking SBIN.NS positions...")
        positions = broker.get_positions()
        
        sbin_positions = [p for p in positions if p['symbol'] == 'SBIN.NS']
        
        if sbin_positions:
            print(f"✅ FOUND {len(sbin_positions)} SBIN.NS POSITION(S):\n")
            
            for idx, pos in enumerate(sbin_positions, 1):
                print(f"Position #{idx}:")
                print("-"*70)
                print(f"  Symbol: {pos['symbol']}")
                print(f"  Quantity: {pos['quantity']} shares")
                print(f"  Average Price: ₹{pos['average_price']:.2f}")
                print(f"  Current Price: ₹{pos['current_price']:.2f}")
                print(f"  Market Value: ₹{pos['market_value']:,.2f}")
                print(f"  Unrealized P&L: ₹{pos['unrealized_pnl']:+,.2f}")
                print()
                
                if pos['quantity'] == 28:
                    print("  ✅ This appears to be from our order (28 shares)\n")
        else:
            print("⚠️ No SBIN.NS positions found\n")
        
        # Get account info
        print("="*70)
        print("💰 Account Information:")
        print("-"*70)
        
        account = broker.get_account_info()
        if account:
            print(f"  Account ID: {account.get('account_id', 'N/A')}")
            print(f"  Buying Power: ${account.get('buying_power', 0):,.2f}")
            print(f"  Cash: ${account.get('cash', 0):,.2f}")
            print(f"  Portfolio Value: ${account.get('portfolio_value', 0):,.2f}")
        
        print("\n" + "="*70)
        print("✅ Broker check completed")
        
        # Disconnect
        broker.disconnect()
        print("✅ Disconnected from IBKR")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
