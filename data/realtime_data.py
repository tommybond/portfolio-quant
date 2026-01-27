"""
Real-time Market Data Integration
Supports multiple data providers: Polygon.io, Alpaca, yfinance fallback
"""

import os
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

try:
    from polygon import RESTClient as PolygonClient
    POLYGON_AVAILABLE = True
except ImportError:
    POLYGON_AVAILABLE = False

try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False


class RealTimeDataProvider:
    """Unified interface for real-time market data"""
    
    def __init__(self, provider: str = 'auto'):
        """
        Initialize data provider
        
        Args:
            provider: 'polygon', 'alpaca', 'yfinance', or 'auto' (auto-detect)
        """
        self.provider = provider
        self.polygon_client = None
        self.alpaca_api = None
        
        if provider == 'auto':
            self.provider = self._detect_best_provider()
        
        self._initialize_provider()
    
    def _detect_best_provider(self) -> str:
        """Auto-detect best available provider"""
        if POLYGON_AVAILABLE and os.getenv('POLYGON_API_KEY'):
            return 'polygon'
        elif ALPACA_AVAILABLE and os.getenv('ALPACA_API_KEY'):
            return 'alpaca'
        else:
            return 'yfinance'
    
    def _initialize_provider(self):
        """Initialize the selected provider"""
        if self.provider == 'polygon' and POLYGON_AVAILABLE:
            api_key = os.getenv('POLYGON_API_KEY')
            if api_key:
                self.polygon_client = PolygonClient(api_key)
        
        elif self.provider == 'alpaca' and ALPACA_AVAILABLE:
            api_key = os.getenv('ALPACA_API_KEY')
            api_secret = os.getenv('ALPACA_SECRET_KEY')
            base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
            
            if api_key and api_secret:
                self.alpaca_api = tradeapi.REST(api_key, api_secret, base_url, api_version='v2')
    
    def get_live_price(self, symbol: str) -> Optional[float]:
        """Get current/live price for a symbol"""
        try:
            if self.provider == 'polygon' and self.polygon_client:
                # Polygon.io real-time quote
                quote = self.polygon_client.get_last_quote(symbol)
                if quote:
                    return (quote.bid + quote.ask) / 2  # Mid price
            
            elif self.provider == 'alpaca' and self.alpaca_api:
                # Alpaca real-time quote
                quote = self.alpaca_api.get_latest_quote(symbol)
                if quote:
                    return (quote.bp + quote.ap) / 2  # Mid price
            
            # Fallback to yfinance (delayed)
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1d', interval='1m')
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
        
        except Exception as e:
            print(f"Error fetching live price for {symbol}: {e}")
            return None
        
        return None
    
    def get_historical_data(self, symbol: str, start_date: datetime, 
                           end_date: datetime, interval: str = '1d') -> pd.DataFrame:
        """Get historical data"""
        try:
            if self.provider == 'polygon' and self.polygon_client:
                # Convert interval to Polygon format
                multiplier, timespan = self._convert_interval(interval)
                
                # Polygon historical data
                aggs = self.polygon_client.get_aggs(
                    symbol,
                    multiplier=multiplier,
                    timespan=timespan,
                    from_=start_date.strftime('%Y-%m-%d'),
                    to=end_date.strftime('%Y-%m-%d')
                )
                
                if aggs:
                    data = []
                    for agg in aggs:
                        data.append({
                            'timestamp': datetime.fromtimestamp(agg.timestamp / 1000),
                            'open': agg.open,
                            'high': agg.high,
                            'low': agg.low,
                            'close': agg.close,
                            'volume': agg.volume
                        })
                    return pd.DataFrame(data).set_index('timestamp')
            
            # For Alpaca provider or any other case, use yfinance for historical data
            # Note: Alpaca API's get_bars method is not available in all versions
            # yfinance is more reliable for historical data anyway
            # Skip Alpaca entirely for historical data - use yfinance directly
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date, interval=interval)
            if not hist.empty:
                return hist
        
        except Exception as e:
            # Fallback to yfinance on any error (suppress Alpaca errors - expected behavior)
            # Only log if yfinance also fails
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date, end=end_date, interval=interval)
                if not hist.empty:
                    return hist
            except Exception as fallback_error:
                # Only print error if yfinance also fails (unexpected)
                print(f"Error fetching historical data for {symbol}: {fallback_error}")
        
        # If all else fails, return empty DataFrame
        return pd.DataFrame()
    
    def _convert_interval(self, interval: str) -> tuple:
        """Convert interval string to Polygon format"""
        mapping = {
            '1m': (1, 'minute'),
            '5m': (5, 'minute'),
            '15m': (15, 'minute'),
            '1h': (1, 'hour'),
            '1d': (1, 'day'),
            '1w': (1, 'week')
        }
        return mapping.get(interval, (1, 'day'))
    
    def get_market_status(self) -> Dict:
        """Get current market status (open/closed)"""
        try:
            if self.provider == 'alpaca' and self.alpaca_api:
                clock = self.alpaca_api.get_clock()
                return {
                    'is_open': clock.is_open,
                    'next_open': clock.next_open,
                    'next_close': clock.next_close
                }
            
            # Default: assume market is open (for yfinance)
            return {
                'is_open': True,
                'next_open': None,
                'next_close': None
            }
        except Exception as e:
            print(f"Error fetching market status: {e}")
            return {'is_open': True}


# Global instance
_data_provider = None


def get_data_provider(provider: str = 'auto') -> RealTimeDataProvider:
    """Get or create data provider instance"""
    global _data_provider
    if _data_provider is None:
        _data_provider = RealTimeDataProvider(provider)
    return _data_provider
