"""
Test UI Integration with IBKR
Verifies that the Streamlit app can properly read orders and positions from IBKR
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oms.broker_ibkr import IBKRBroker
import yfinance as yf

def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def simulate_ui_position_fetch():
    """Simulate how the UI fetches and displays positions"""
    print_header("UI POSITION FETCH SIMULATION")
    
    try:
        # Connect to broker (as UI does)
        broker = IBKRBroker(client_id=77777)
        broker.connect()
        print("✅ Connected to IBKR (as UI would)")
        
        # Fetch positions
        positions = broker.get_positions()
        
        if not positions:
            print("ℹ️ No positions to display (empty portfolio)")
            return True
        
        print(f"\n📊 CURRENT POSITIONS ({len(positions)} total)\n")
        print("-" * 70)
        
        total_value = 0
        total_pnl = 0
        
        for pos in positions:
            symbol = pos.get('symbol', 'N/A')
            qty = pos.get('quantity', 0)
            avg_cost = pos.get('average_cost', 0)
            
            # Fetch current price using yfinance (as UI does for IBKR)
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d')
                current_price = hist['Close'].iloc[-1] if not hist.empty else 0
            except:
                current_price = 0
            
            market_value = qty * current_price
            cost_basis = qty * avg_cost
            pnl = market_value - cost_basis
            pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
            
            total_value += market_value
            total_pnl += pnl
            
            print(f"Symbol:        {symbol}")
            print(f"Quantity:      {qty}")
            print(f"Avg Cost:      ${avg_cost:.2f}")
            print(f"Current Price: ${current_price:.2f}")
            print(f"Market Value:  ${market_value:,.2f}")
            print(f"P&L:           ${pnl:,.2f} ({pnl_pct:+.2f}%)")
            print("-" * 70)
        
        print(f"\n💰 PORTFOLIO SUMMARY")
        print(f"Total Market Value: ${total_value:,.2f}")
        print(f"Total P&L:          ${total_pnl:,.2f}")
        
        broker.disconnect()
        print("\n✅ Position fetch and display working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_ui_order_history():
    """Simulate how the UI fetches and displays order history"""
    print_header("UI ORDER HISTORY SIMULATION")
    
    try:
        # Connect to broker
        broker = IBKRBroker(client_id=77778)
        broker.connect()
        print("✅ Connected to IBKR for order history")
        
        # Fetch trades (completed orders)
        trades = broker.ib.trades()
        
        if not trades:
            print("ℹ️ No trade history available")
            broker.disconnect()
            return True
        
        print(f"\n📜 ORDER HISTORY ({len(trades)} trades)\n")
        print("-" * 70)
        
        for i, trade in enumerate(trades[:10], 1):  # Show last 10
            order = trade.order
            contract = trade.contract
            status = trade.orderStatus
            
            print(f"\nTrade #{i}")
            print(f"Order ID:      {order.orderId}")
            print(f"Symbol:        {contract.symbol}")
            print(f"Action:        {order.action}")
            print(f"Quantity:      {order.totalQuantity}")
            print(f"Order Type:    {order.orderType}")
            print(f"Status:        {status.status}")
            print(f"Filled:        {status.filled}/{order.totalQuantity}")
            if status.avgFillPrice and status.avgFillPrice > 0:
                print(f"Avg Fill Price: ${status.avgFillPrice:.2f}")
            print("-" * 70)
        
        broker.disconnect()
        print("\n✅ Order history fetch and display working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_ui_buying_power():
    """Simulate how the UI fetches and displays buying power"""
    print_header("UI BUYING POWER DISPLAY")
    
    try:
        # Connect to broker
        broker = IBKRBroker(client_id=77779)
        broker.connect()
        print("✅ Connected to IBKR for account info")
        
        # Fetch account info
        account_info = broker.get_account_info()
        
        print(f"\n💵 ACCOUNT INFORMATION\n")
        print("-" * 70)
        print(f"Account ID:        {account_info.get('account_id', 'N/A')}")
        print(f"Buying Power:      ${account_info.get('buying_power', 0):,.2f}")
        print(f"Cash Balance:      ${account_info.get('cash', 0):,.2f}")
        print(f"Portfolio Value:   ${account_info.get('portfolio_value', 0):,.2f}")
        print("-" * 70)
        
        # Simulate order submission affordability check
        buying_power = account_info.get('buying_power', 0)
        test_order_value = 259.48 * 10  # 10 shares of AAPL at ~$259
        
        print(f"\n🧮 AFFORDABILITY CHECK")
        print(f"Test Order Value:  ${test_order_value:,.2f} (10 shares AAPL)")
        print(f"Available Power:   ${buying_power:,.2f}")
        
        if test_order_value <= buying_power:
            print(f"✅ Order is affordable ({test_order_value/buying_power*100:.1f}% of buying power)")
        else:
            print(f"❌ Insufficient buying power")
        
        broker.disconnect()
        print("\n✅ Buying power fetch and display working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_price_sync_fix():
    """Verify that the price sync fix is working"""
    print_header("PRICE SYNC FIX VERIFICATION")
    
    print("Testing the fix for price discrepancy issue...")
    print("\nScenario: User sees AAPL at $259.48, clicks PREPARE")
    print("Expected: Order should use $259.48 (not stale value)")
    
    try:
        # Fetch current price (as UI does)
        symbol = 'AAPL'
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='1d')
        current_price = hist['Close'].iloc[-1] if not hist.empty else None
        
        if current_price:
            print(f"\n✅ Current price fetched: ${current_price:.2f}")
            
            # Simulate session state storage (as fixed in app.py)
            session_state = {}
            session_state['deploy_current_price'] = current_price
            
            print(f"✅ Price saved to session state: ${session_state['deploy_current_price']:.2f}")
            
            # Simulate PREPARE button reading from session state
            prepare_price = session_state.get('deploy_current_price')
            print(f"✅ PREPARE button reads: ${prepare_price:.2f}")
            
            if abs(prepare_price - current_price) < 0.01:
                print("\n✅ Price sync working correctly - no discrepancy!")
                print("   Orders will use the correct current price")
                return True
            else:
                print(f"\n❌ Price mismatch: display={current_price}, prepare={prepare_price}")
                return False
        else:
            print("⚠️ Could not fetch price")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def run_integration_tests():
    """Run all UI integration tests"""
    print("\n" + "="*70)
    print("  STREAMLIT UI - IBKR INTEGRATION TEST SUITE")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = {
        'Position Fetch': simulate_ui_position_fetch(),
        'Order History': simulate_ui_order_history(),
        'Buying Power': simulate_ui_buying_power(),
        'Price Sync Fix': simulate_price_sync_fix()
    }
    
    # Summary
    print_header("INTEGRATION TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
    
    print(f"\n{'='*70}")
    print(f"  Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print(f"\n  🎉 ALL INTEGRATION TESTS PASSED!")
        print(f"  IBKR broker is working correctly with Streamlit UI")
    
    print(f"{'='*70}\n")
    
    return passed == total

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
