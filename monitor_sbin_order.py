#!/usr/bin/env python3
"""Real-time monitor for SBIN.NS order status."""

import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import init_database, create_session, Trade
from oms.broker_ibkr import IBKRBroker

def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name == 'posix' else 'cls')

def format_time(dt):
    """Format datetime for display."""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return "N/A"

def get_status_emoji(status):
    """Get emoji for status."""
    status_upper = str(status).upper()
    if status_upper in ['FILLED', 'COMPLETE', 'COMPLETED']:
        return "✅"
    elif status_upper in ['PENDING', 'PENDINGSUBMIT']:
        return "⏳"
    elif status_upper in ['SUBMITTED', 'PRESUBMITTED']:
        return "📤"
    elif status_upper in ['CANCELLED', 'CANCELED']:
        return "❌"
    elif status_upper in ['REJECTED']:
        return "🚫"
    else:
        return "🔵"

def monitor_order():
    """Monitor SBIN.NS order status in real-time."""
    
    print("🚀 Starting SBIN.NS Order Monitor")
    print("=" * 70)
    print("Press Ctrl+C to stop monitoring\n")
    
    # Initialize database
    init_database()
    
    # Connect to IBKR
    broker = None
    try:
        if os.getenv('IBKR_HOST') and os.getenv('IBKR_PORT'):
            broker = IBKRBroker()
            if broker.connect():
                print("✅ Connected to IBKR\n")
            else:
                print("⚠️ Could not connect to IBKR, will only show database status\n")
                broker = None
        else:
            print("⚠️ IBKR not configured, will only show database status\n")
    except Exception as e:
        print(f"⚠️ IBKR connection error: {str(e)}\n")
        broker = None
    
    iteration = 0
    last_db_status = None
    last_broker_status = None
    
    try:
        while True:
            iteration += 1
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Clear screen for clean display
            if iteration > 1:
                clear_screen()
            
            print(f"🔄 Monitoring SBIN.NS Order - Update #{iteration} at {current_time}")
            print("=" * 70)
            
            # Check database
            session = create_session()
            try:
                # Get most recent SBIN.NS trade
                trade = session.query(Trade).filter(
                    Trade.symbol == 'SBIN.NS'
                ).order_by(Trade.created_at.desc()).first()
                
                if trade:
                    print("\n📊 DATABASE STATUS:")
                    print("-" * 70)
                    status_emoji = get_status_emoji(trade.status)
                    print(f"  Status: {status_emoji} {trade.status}")
                    print(f"  Symbol: {trade.symbol}")
                    print(f"  Side: {trade.side}")
                    print(f"  Quantity: {trade.quantity} shares")
                    print(f"  Price: ₹{trade.price:.2f}")
                    print(f"  Order Type: {trade.order_type}")
                    print(f"  Broker Order ID: {trade.broker_order_id or 'N/A'}")
                    print(f"  Created: {format_time(trade.created_at)}")
                    print(f"  Execution Time: {format_time(trade.execution_time)}")
                    
                    # Detect status change
                    if last_db_status and last_db_status != trade.status:
                        print(f"\n  🔔 STATUS CHANGED: {last_db_status} → {trade.status}")
                    last_db_status = trade.status
                else:
                    print("\n❌ No SBIN.NS order found in database")
            finally:
                session.close()
            
            # Check broker status
            if broker:
                try:
                    # Get all orders from IBKR
                    orders = broker.get_orders()
                    sbin_orders = [o for o in orders if o.get('symbol') == 'SBIN.NS']
                    
                    if sbin_orders:
                        print("\n\n🔌 IBKR BROKER STATUS:")
                        print("-" * 70)
                        
                        for order in sbin_orders:
                            status_emoji = get_status_emoji(order.get('status', 'UNKNOWN'))
                            print(f"  Status: {status_emoji} {order.get('status', 'UNKNOWN')}")
                            print(f"  Order ID: {order.get('order_id', 'N/A')}")
                            print(f"  Symbol: {order.get('symbol', 'N/A')}")
                            print(f"  Side: {order.get('side', 'N/A')}")
                            print(f"  Quantity: {order.get('quantity', 0)} shares")
                            print(f"  Filled: {order.get('filled_quantity', 0)} shares")
                            print(f"  Remaining: {order.get('remaining_quantity', 0)} shares")
                            
                            if order.get('average_fill_price'):
                                print(f"  Avg Fill Price: ₹{order.get('average_fill_price'):.2f}")
                            
                            # Detect status change
                            broker_status = order.get('status', 'UNKNOWN')
                            if last_broker_status and last_broker_status != broker_status:
                                print(f"\n  🔔 BROKER STATUS CHANGED: {last_broker_status} → {broker_status}")
                            last_broker_status = broker_status
                    else:
                        # Check positions instead
                        positions = broker.get_positions()
                        sbin_positions = [p for p in positions if p['symbol'] == 'SBIN.NS']
                        
                        if sbin_positions:
                            print("\n\n✅ POSITION FOUND (Order Filled!):")
                            print("-" * 70)
                            for pos in sbin_positions:
                                print(f"  Symbol: {pos['symbol']}")
                                print(f"  Quantity: {pos['quantity']} shares")
                                print(f"  Average Price: ₹{pos['average_price']:.2f}")
                                print(f"  Current Price: ₹{pos['current_price']:.2f}")
                                print(f"  Market Value: ₹{pos['market_value']:,.2f}")
                                print(f"  Unrealized P&L: ₹{pos['unrealized_pnl']:+,.2f}")
                                
                                if last_broker_status and last_broker_status != 'FILLED':
                                    print(f"\n  🎉 ORDER FILLED! Position established.")
                                last_broker_status = 'FILLED'
                        else:
                            print("\n\n⏳ IBKR: No active orders or positions for SBIN.NS")
                            print("     Order may be queued or waiting for market to open")
                
                except Exception as e:
                    print(f"\n\n⚠️ Error checking IBKR: {str(e)}")
            
            # Trading hours info
            print("\n\n📅 NSE TRADING HOURS (IST):")
            print("-" * 70)
            print("  Pre-Open: 9:00 AM - 9:15 AM")
            print("  Normal Trading: 9:15 AM - 3:30 PM")
            print("  Market orders execute only during trading hours")
            
            # Next update info
            print("\n" + "=" * 70)
            print("Next update in 10 seconds... (Ctrl+C to stop)")
            
            # Wait 10 seconds
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped by user")
    finally:
        if broker:
            try:
                broker.disconnect()
                print("✅ Disconnected from IBKR")
            except:
                pass

if __name__ == "__main__":
    monitor_order()
