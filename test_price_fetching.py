#!/usr/bin/env python3
"""
Test price fetching for different symbols
"""

import sys

print("=" * 70)
print("PRICE FETCHING TEST")
print("=" * 70)

# Test symbols
symbols = ['AAPL', 'GOOGL', 'MSFT', 'SBIN.NS']

print("\nTesting yfinance price fetching...")
print()

try:
    import yfinance as yf
    print("✅ yfinance installed")
    print()
    
    for symbol in symbols:
        print(f"Testing {symbol}:")
        try:
            ticker = yf.Ticker(symbol)
            
            # Method 1: 1-minute data
            hist_1m = ticker.history(period='1d', interval='1m')
            if not hist_1m.empty:
                price = float(hist_1m['Close'].iloc[-1])
                print(f"  ✅ 1-minute data: ${price:.2f}")
            else:
                print(f"  ⚠️  No 1-minute data")
                
                # Method 2: Daily data
                hist_daily = ticker.history(period='1d')
                if not hist_daily.empty:
                    price = float(hist_daily['Close'].iloc[-1])
                    print(f"  ✅ Daily data: ${price:.2f}")
                else:
                    print(f"  ⚠️  No daily data")
                    
                    # Method 3: Info
                    info = ticker.info
                    if 'currentPrice' in info and info['currentPrice']:
                        price = float(info['currentPrice'])
                        print(f"  ✅ Info currentPrice: ${price:.2f}")
                    elif 'regularMarketPrice' in info and info['regularMarketPrice']:
                        price = float(info['regularMarketPrice'])
                        print(f"  ✅ Info regularMarketPrice: ${price:.2f}")
                    else:
                        print(f"  ❌ No price data available")
                        print(f"     Available info keys: {list(info.keys())[:10]}")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")
        
        print()

except ImportError:
    print("❌ yfinance not installed")
    print("   Install with: pip install yfinance")
    sys.exit(1)

print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)
