#!/usr/bin/env python3
"""Quick check of SBIN.NS order from database only."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import init_database, create_session, Trade
from datetime import datetime

def main():
    print("🔍 Checking SBIN.NS Order Status from Database\n")
    print("="*70)
    
    # Initialize database
    init_database()
    session = create_session()
    
    try:
        # Get SBIN.NS order
        trade = session.query(Trade).filter(
            Trade.symbol == 'SBIN.NS',
            Trade.broker_order_id == '256'
        ).first()
        
        if not trade:
            # Try without broker ID filter
            trade = session.query(Trade).filter(
                Trade.symbol == 'SBIN.NS'
            ).order_by(Trade.created_at.desc()).first()
        
        if trade:
            print("✅ SBIN.NS Order Found:\n")
            print(f"  📋 Trade ID: {trade.id}")
            print(f"  🏢 Symbol: {trade.symbol}")
            print(f"  📈 Side: {trade.side}")
            print(f"  📊 Quantity: {trade.quantity} shares")
            print(f"  💰 Price: ₹{trade.price:.2f}" if trade.price > 0 else f"  💰 Price: Market Order")
            print(f"  📝 Order Type: {trade.order_type}")
            print(f"  🔔 Status: {trade.status}")
            print(f"  🆔 Broker Order ID: {trade.broker_order_id or 'N/A'}")
            print(f"  📅 Created: {trade.created_at}")
            print(f"  ⏰ Execution Time: {trade.execution_time or 'Pending'}")
            print(f"  👤 User ID: {trade.user_id}")
            
            print("\n" + "="*70)
            print("📊 Order Status Analysis:")
            print("-"*70)
            
            if trade.status.upper() in ['SUBMITTED', 'PENDING', 'PRESUBMITTED']:
                print("  ⏳ Status: Order is queued and waiting")
                print("  📍 Location: Submitted to IBKR")
                print("  🕐 Next Step: Will execute when NSE market opens")
                print("  ⏰ NSE Hours: 9:15 AM - 3:30 PM IST")
                print("  💡 Note: Market orders execute at best available price")
                
            elif trade.status.upper() in ['FILLED', 'COMPLETE', 'COMPLETED']:
                print("  ✅ Status: Order successfully filled")
                print(f"  💰 Fill Price: ₹{trade.price:.2f}")
                print(f"  ✓ Quantity: {trade.quantity} shares acquired")
                
            elif trade.status.upper() in ['CANCELLED', 'CANCELED']:
                print("  ❌ Status: Order was cancelled")
                
            elif trade.status.upper() == 'REJECTED':
                print("  🚫 Status: Order was rejected")
                
            else:
                print(f"  🔵 Status: {trade.status}")
            
            # Check if market is open
            print("\n" + "="*70)
            print("🌍 Market Status Check:")
            print("-"*70)
            
            from datetime import datetime
            import pytz
            
            # Get current time in IST
            ist = pytz.timezone('Asia/Kolkata')
            now_ist = datetime.now(ist)
            current_hour = now_ist.hour
            current_minute = now_ist.minute
            
            print(f"  🕐 Current IST Time: {now_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            # Check if within trading hours (9:15 AM to 3:30 PM)
            market_start = 9 * 60 + 15  # 9:15 AM in minutes
            market_end = 15 * 60 + 30   # 3:30 PM in minutes
            current_minutes = current_hour * 60 + current_minute
            
            # Check if it's a weekday
            is_weekday = now_ist.weekday() < 5  # Monday=0, Friday=4
            
            if is_weekday and market_start <= current_minutes <= market_end:
                print("  🟢 NSE Market: OPEN")
                print("  💡 Orders should execute now")
            elif is_weekday and current_minutes < market_start:
                time_to_open = market_start - current_minutes
                print("  🟡 NSE Market: CLOSED (Pre-Market)")
                print(f"  ⏰ Opens in: {time_to_open // 60}h {time_to_open % 60}m")
            elif is_weekday:
                print("  🔴 NSE Market: CLOSED (After Hours)")
                print("  📅 Opens tomorrow at 9:15 AM IST")
            else:
                print("  🔴 NSE Market: CLOSED (Weekend)")
                print("  📅 Opens Monday at 9:15 AM IST")
            
        else:
            print("❌ No SBIN.NS order found in database")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        session.close()

if __name__ == "__main__":
    main()
