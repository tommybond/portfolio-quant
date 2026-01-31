#!/usr/bin/env python3
"""Check SBIN.NS order status in database and broker."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import init_database, create_session, Trade
from datetime import datetime, timedelta

def main():
    print("🔍 Checking SBIN.NS order status...\n")
    
    # Initialize database
    init_database()
    session = create_session()
    
    try:
        # Query for SBIN.NS trades (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        trades = session.query(Trade).filter(
            Trade.symbol == 'SBIN.NS',
            Trade.created_at >= seven_days_ago
        ).order_by(Trade.created_at.desc()).all()
        
        if trades:
            print(f"✅ Found {len(trades)} SBIN.NS trade(s):\n")
            for trade in trades:
                print(f"{'='*60}")
                print(f"Trade ID: {trade.id}")
                print(f"Symbol: {trade.symbol}")
                print(f"Side: {trade.side}")
                print(f"Quantity: {trade.quantity}")
                print(f"Price: ₹{trade.price:.2f}")
                print(f"Order Type: {trade.order_type}")
                print(f"Status: {trade.status}")
                print(f"Broker Order ID: {trade.broker_order_id or 'N/A'}")
                print(f"Created At: {trade.created_at}")
                print(f"Execution Time: {trade.execution_time or 'N/A'}")
                print(f"User ID: {trade.user_id}")
                print()
        else:
            print("❌ No SBIN.NS orders found in the last 7 days")
            print("\n💡 Checking if there are ANY trades in the database...")
            
            all_trades = session.query(Trade).order_by(Trade.created_at.desc()).limit(10).all()
            if all_trades:
                print(f"\n✅ Found {len(all_trades)} recent trade(s) (all symbols):\n")
                for trade in all_trades:
                    print(f"- {trade.symbol}: {trade.side} {trade.quantity} @ ${trade.price:.2f} [{trade.status}] - {trade.created_at}")
            else:
                print("❌ No trades found in database at all")
        
        # Now check broker connection
        print("\n" + "="*60)
        print("🔌 Checking broker for SBIN.NS positions...")
        print("="*60 + "\n")
        
        try:
            # Try IBKR first (since SBIN.NS is Indian stock)
            from oms.broker_ibkr import BrokerIBKR
            
            # Check if IBKR credentials exist
            if os.getenv('IBKR_HOST') and os.getenv('IBKR_PORT'):
                print("✅ IBKR credentials found, connecting...")
                broker = BrokerIBKR()
                
                if broker.connect():
                    print("✅ Connected to IBKR\n")
                    
                    # Get positions
                    positions = broker.get_positions()
                    sbin_positions = [p for p in positions if p['symbol'] == 'SBIN.NS']
                    
                    if sbin_positions:
                        print(f"✅ Found SBIN.NS position in IBKR:\n")
                        for pos in sbin_positions:
                            print(f"Symbol: {pos['symbol']}")
                            print(f"Quantity: {pos['quantity']}")
                            print(f"Average Price: ₹{pos['average_price']:.2f}")
                            print(f"Current Price: ₹{pos['current_price']:.2f}")
                            print(f"Market Value: ₹{pos['market_value']:.2f}")
                            print(f"Unrealized P&L: ₹{pos['unrealized_pnl']:+,.2f}")
                    else:
                        print("❌ No SBIN.NS position found in IBKR")
                        
                        if positions:
                            print(f"\n💡 But found {len(positions)} other position(s):")
                            for pos in positions:
                                print(f"  - {pos['symbol']}: {pos['quantity']} shares")
                    
                    broker.disconnect()
                else:
                    print("❌ Could not connect to IBKR")
            else:
                print("⚠️ IBKR credentials not configured")
        except Exception as e:
            print(f"⚠️ Error checking IBKR: {str(e)}")
        
        # Check Alpaca as fallback
        try:
            from oms.broker_alpaca import BrokerAlpaca
            
            if os.getenv('ALPACA_API_KEY') and os.getenv('ALPACA_SECRET_KEY'):
                print("\n✅ Alpaca credentials found, checking...")
                broker = BrokerAlpaca()
                
                if broker.connect():
                    print("✅ Connected to Alpaca\n")
                    
                    positions = broker.api.list_positions()
                    sbin_positions = [p for p in positions if p.symbol == 'SBIN.NS']
                    
                    if sbin_positions:
                        print(f"✅ Found SBIN.NS position in Alpaca:\n")
                        for pos in sbin_positions:
                            print(f"Symbol: {pos.symbol}")
                            print(f"Quantity: {pos.qty}")
                            print(f"Average Entry: ₹{float(pos.avg_entry_price):.2f}")
                            print(f"Current Price: ₹{float(pos.current_price):.2f}")
                            print(f"Market Value: ₹{float(pos.market_value):.2f}")
                            print(f"Unrealized P&L: ₹{float(pos.unrealized_pl):+,.2f}")
                    else:
                        print("❌ No SBIN.NS position found in Alpaca")
                else:
                    print("❌ Could not connect to Alpaca")
        except Exception as e:
            print(f"⚠️ Error checking Alpaca: {str(e)}")
            
    finally:
        session.close()

if __name__ == "__main__":
    main()
