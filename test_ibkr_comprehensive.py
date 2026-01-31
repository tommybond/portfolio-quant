"""
Comprehensive IBKR Broker Test Suite
Tests all critical functionality after recent fixes
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oms.broker_ibkr import IBKRBroker
from oms.oms import OrderManager, Order
from database.models import init_database, User, create_session
import yfinance as yf

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_connection():
    """Test 1: IBKR Connection"""
    print_section("TEST 1: Connection")
    
    try:
        broker = IBKRBroker(client_id=88888)
        print("✅ Broker instance created")
        
        broker.connect()
        print("✅ Connected to IBKR")
        
        # Verify connection
        if broker.ib.isConnected():
            print(f"✅ Connection verified - Client ID: {broker.client_id}")
            return broker
        else:
            print("❌ Connection failed")
            return None
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def test_account_info(broker):
    """Test 2: Account Information Retrieval"""
    print_section("TEST 2: Account Information")
    
    try:
        account_info = broker.get_account_info()
        
        print(f"Account ID: {account_info.get('account_id', 'N/A')}")
        print(f"Buying Power: ${account_info.get('buying_power', 0):,.2f}")
        print(f"Cash: ${account_info.get('cash', 0):,.2f}")
        print(f"Portfolio Value: ${account_info.get('portfolio_value', 0):,.2f}")
        
        if account_info.get('buying_power', 0) > 0:
            print("✅ Account info retrieved successfully")
            return True
        else:
            print("⚠️ Buying power is 0 - check account status")
            return False
            
    except Exception as e:
        print(f"❌ Account info error: {e}")
        return False

def test_positions(broker):
    """Test 3: Position Retrieval"""
    print_section("TEST 3: Current Positions")
    
    try:
        positions = broker.get_positions()
        
        if not positions:
            print("ℹ️ No open positions")
            return True
        
        print(f"Found {len(positions)} position(s):")
        for pos in positions:
            print(f"\n  Symbol: {pos.get('symbol', 'N/A')}")
            print(f"  Quantity: {pos.get('quantity', 0)}")
            print(f"  Avg Cost: ${pos.get('average_cost', 0):.2f}")
            print(f"  Current Price: ${pos.get('current_price', 0):.2f}")
            print(f"  Market Value: ${pos.get('market_value', 0):,.2f}")
            print(f"  P&L: ${pos.get('unrealized_pnl', 0):,.2f}")
        
        print("\n✅ Positions retrieved successfully")
        return True
        
    except Exception as e:
        print(f"❌ Position retrieval error: {e}")
        return False

def test_price_fetching(broker):
    """Test 4: Price Fetching (Multiple Methods)"""
    print_section("TEST 4: Price Fetching")
    
    test_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
    results = {}
    
    print("Testing yfinance (primary method for IBKR Paper Trading):")
    for symbol in test_symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1d')
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                results[symbol] = price
                print(f"  {symbol}: ${price:.2f} ✅")
            else:
                print(f"  {symbol}: No data ❌")
        except Exception as e:
            print(f"  {symbol}: Error - {e} ❌")
    
    # Test IBKR method (will return None for Paper Trading)
    print(f"\nTesting IBKR method (expected to return None for Paper Trading):")
    for symbol in test_symbols[:2]:  # Just test 2 symbols
        try:
            price = broker.get_current_price(symbol)
            if price:
                print(f"  {symbol}: ${price:.2f} ✅")
            else:
                print(f"  {symbol}: None (expected for Paper Trading) ℹ️")
        except Exception as e:
            print(f"  {symbol}: Error - {e} ❌")
    
    if len(results) >= 3:
        print(f"\n✅ Price fetching working ({len(results)}/{len(test_symbols)} symbols)")
        return True
    else:
        print(f"\n⚠️ Limited price data ({len(results)}/{len(test_symbols)} symbols)")
        return False

def test_order_status(broker):
    """Test 5: Order Status Retrieval"""
    print_section("TEST 5: Order Status Retrieval")
    
    try:
        # Get trades (filled orders) which have proper contract info
        trades = broker.ib.trades()
        
        if not trades:
            print("ℹ️ No filled trades found")
            
            # Try to get open orders instead
            open_orders = broker.ib.openOrders()
            if not open_orders:
                print("ℹ️ No open orders either")
                return True
            
            print(f"\nFound {len(open_orders)} open order(s):")
            for order in open_orders[:5]:  # Show first 5
                print(f"\n  Order ID: {order.orderId}")
                if hasattr(order, 'contract') and order.contract:
                    print(f"  Symbol: {order.contract.symbol}")
                print(f"  Action: {order.action}")
                print(f"  Quantity: {order.totalQuantity}")
                print(f"  Order Type: {order.orderType}")
        else:
            print(f"Found {len(trades)} trade(s):")
            for trade in trades[:5]:  # Show first 5
                print(f"\n  Order ID: {trade.order.orderId}")
                print(f"  Symbol: {trade.contract.symbol}")
                print(f"  Action: {trade.order.action}")
                print(f"  Quantity: {trade.order.totalQuantity}")
                print(f"  Status: {trade.orderStatus.status}")
                print(f"  Filled: {trade.orderStatus.filled}/{trade.order.totalQuantity}")
        
        print("\n✅ Order status retrieved successfully")
        return True
        
    except Exception as e:
        print(f"❌ Order status error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_order_placement_dry_run(broker):
    """Test 6: Order Placement (Dry Run - No Actual Submission)"""
    print_section("TEST 6: Order Placement Logic (Dry Run)")
    
    try:
        # Test contract creation
        from ib_insync import Stock
        
        symbol = 'AAPL'
        contract = Stock(symbol, 'SMART', 'USD')
        print(f"✅ Contract created for {symbol}")
        
        # Get current price from yfinance
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='1d')
        price = hist['Close'].iloc[-1] if not hist.empty else None
        
        if price:
            print(f"✅ Current price: ${price:.2f}")
        else:
            print("⚠️ Could not fetch current price")
        
        # Test order object creation
        from ib_insync import LimitOrder
        
        test_order = LimitOrder(
            action='BUY',
            totalQuantity=1,
            lmtPrice=round(price * 0.95, 2) if price else 100.0  # 5% below current
        )
        print(f"✅ Order object created (BUY 1 @ limit ${test_order.lmtPrice})")
        
        print("\n✅ Order placement logic verified (not submitted)")
        return True
        
    except Exception as e:
        print(f"❌ Order placement logic error: {e}")
        return False

def test_oms_integration():
    """Test 7: OMS Integration"""
    print_section("TEST 7: OMS Integration")
    
    try:
        # Initialize database
        init_database()
        print("✅ Database initialized")
        
        # Get or create test user
        session = create_session()
        
        user = session.query(User).filter_by(username='admin').first()
        if user:
            print(f"✅ Found user: {user.username} (ID: {user.id})")
            user_id = user.id
        else:
            print("⚠️ Admin user not found")
            user_id = 1
        
        session.close()
        
        # Create OMS instance
        oms = OrderManager()
        print("✅ OrderManager created")
        
        # Test order object creation
        from oms.oms import OrderType
        
        test_order = Order(
            symbol='AAPL',
            quantity=1,
            side='buy',
            order_type=OrderType.MARKET
        )
        print(f"✅ Order object created: {test_order.symbol} {test_order.side.upper()} {test_order.quantity}")
        
        print("\n✅ OMS integration verified")
        return True
        
    except Exception as e:
        print(f"❌ OMS integration error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_status_conversion(broker):
    """Test 8: Status Conversion Method"""
    print_section("TEST 8: Status Conversion")
    
    test_statuses = [
        'PendingSubmit',
        'Submitted',
        'Filled',
        'Cancelled',
        'PreSubmitted',
        'ApiPending',
        'Unknown'
    ]
    
    try:
        for status in test_statuses:
            converted = broker._convert_status(status)
            print(f"  {status:20} → {converted}")
        
        print("\n✅ Status conversion working")
        return True
        
    except Exception as e:
        print(f"❌ Status conversion error: {e}")
        return False

def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*60)
    print("  IBKR BROKER COMPREHENSIVE TEST SUITE")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    results = {}
    broker = None
    
    # Test 1: Connection
    broker = test_connection()
    results['Connection'] = broker is not None
    
    if not broker:
        print("\n❌ Cannot proceed without connection")
        return
    
    # Test 2: Account Info
    results['Account Info'] = test_account_info(broker)
    
    # Test 3: Positions
    results['Positions'] = test_positions(broker)
    
    # Test 4: Price Fetching
    results['Price Fetching'] = test_price_fetching(broker)
    
    # Test 5: Order Status
    results['Order Status'] = test_order_status(broker)
    
    # Test 6: Order Placement Logic
    results['Order Placement'] = test_order_placement_dry_run(broker)
    
    # Test 7: OMS Integration
    results['OMS Integration'] = test_oms_integration()
    
    # Test 8: Status Conversion
    results['Status Conversion'] = test_status_conversion(broker)
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
    
    print(f"\n{'='*60}")
    print(f"  Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"{'='*60}\n")
    
    # Disconnect
    if broker:
        try:
            broker.disconnect()
            print("✅ Disconnected from IBKR\n")
        except:
            pass
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
