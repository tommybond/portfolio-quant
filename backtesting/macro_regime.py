"""
Macro Regime Detection for Position Sizing
Implements macro-based regime multipliers for the 5-Trench position sizing model
Supports real macro indicators: VIX, yield curves, economic data
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
import warnings

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    warnings.warn("yfinance not available. Macro indicators will use price-based proxies.")


class MacroRegimeDetector:
    """
    Detect macroeconomic regimes and provide position sizing multipliers
    
    Regimes:
    - Risk-On: Favorable conditions (multiplier: 1.2x - 1.5x)
    - Neutral: Normal conditions (multiplier: 1.0x)
    - Risk-Off: Unfavorable conditions (multiplier: 0.3x - 0.7x)
    
    Supports:
    - Real VIX data (fear index)
    - Yield curve data (10Y-2Y spread)
    - Price-based proxies (volatility, trend, drawdown)
    """
    
    def __init__(self, lookback_days: int = 60, use_real_macro: bool = True):
        """
        Initialize macro regime detector
        
        Args:
            lookback_days: Days to look back for regime detection
            use_real_macro: Whether to fetch real macro indicators (VIX, yield curves)
        """
        self.lookback_days = lookback_days
        self.use_real_macro = use_real_macro and YFINANCE_AVAILABLE
        self.regime_history = []
        self.macro_data_cache = {}  # Cache macro data to avoid repeated fetches
    
    def _fetch_vix(self, start_date: datetime, end_date: datetime) -> Optional[pd.Series]:
        """Fetch VIX data from yfinance"""
        if not self.use_real_macro:
            return None
        
        try:
            cache_key = f"VIX_{start_date.date()}_{end_date.date()}"
            if cache_key in self.macro_data_cache:
                return self.macro_data_cache[cache_key]
            
            vix_ticker = yf.Ticker("^VIX")
            vix_data = vix_ticker.history(start=start_date, end=end_date)
            
            if not vix_data.empty and 'Close' in vix_data.columns:
                vix_series = vix_data['Close']
                self.macro_data_cache[cache_key] = vix_series
                return vix_series
        except Exception as e:
            warnings.warn(f"Could not fetch VIX data: {e}")
        
        return None
    
    def _fetch_yield_curve(self, start_date: datetime, end_date: datetime) -> Optional[Dict[str, pd.Series]]:
        """Fetch yield curve data (10Y-2Y Treasury spread)"""
        if not self.use_real_macro:
            return None
        
        try:
            cache_key = f"YIELD_{start_date.date()}_{end_date.date()}"
            if cache_key in self.macro_data_cache:
                return self.macro_data_cache[cache_key]
            
            # Fetch 10-year and 2-year Treasury yields
            # Note: These tickers may vary; using common ones
            tickers = {
                '10Y': '^TNX',  # 10-Year Treasury Note
                '2Y': '^IRX'    # 13-Week Treasury Bill (proxy for short-term rates)
            }
            
            yields = {}
            for name, ticker_symbol in tickers.items():
                try:
                    ticker = yf.Ticker(ticker_symbol)
                    hist = ticker.history(start=start_date, end=end_date)
                    if not hist.empty and 'Close' in hist.columns:
                        yields[name] = hist['Close']
                except:
                    pass
            
            if yields:
                self.macro_data_cache[cache_key] = yields
                return yields
        except Exception as e:
            warnings.warn(f"Could not fetch yield curve data: {e}")
        
        return None
    
    def detect_regime_from_price(self, data: pd.DataFrame, current_date: Optional[datetime] = None) -> Tuple[str, float]:
        """
        Detect macro regime from price data (simplified proxy)
        
        Uses:
        - Volatility (VIX proxy via realized vol)
        - Trend strength
        - Drawdown severity
        
        Args:
            data: Price data with OHLCV
            current_date: Current date (if None, uses last date in data)
            
        Returns:
            Tuple of (regime_name, multiplier)
            - regime_name: 'risk_on', 'neutral', 'risk_off'
            - multiplier: 0.3 to 1.5
        """
        if len(data) < self.lookback_days:
            return 'neutral', 1.0
        
        # Use last date if not specified
        if current_date is None:
            current_date = data.index[-1] if hasattr(data.index, '__getitem__') else None
        
        # Get recent data window up to current_date
        # If current_date is specified, filter data to that date first
        if current_date is not None:
            # Filter data to only include dates up to current_date
            if isinstance(data.index, pd.DatetimeIndex):
                data = data[data.index <= current_date].copy()
        
        if len(data) < 30:
            import warnings
            warnings.warn(f"Insufficient data for regime detection: {len(data)} rows (need 30+), current_date={current_date}")
            return 'neutral', 1.0
        
        # Get recent data window (last lookback_days from the filtered data)
        end_idx = len(data) - 1
        start_idx = max(0, end_idx - self.lookback_days)
        recent_data = data.iloc[start_idx:end_idx+1]
        
        if len(recent_data) < 30:
            import warnings
            warnings.warn(f"Insufficient recent data for regime detection: {len(recent_data)} rows (need 30+), "
                        f"lookback_days={self.lookback_days}, data_length={len(data)}")
            return 'neutral', 1.0
        
        if len(recent_data) < 30:
            return 'neutral', 1.0
        
        # Handle both 'close' and 'Close' column names
        close_col = 'close' if 'close' in recent_data.columns else 'Close'
        
        # Calculate indicators
        returns = recent_data[close_col].pct_change().dropna()
        
        # 1. Volatility (VIX proxy)
        volatility = returns.std() * np.sqrt(252)  # Annualized
        
        # 2. Trend strength
        price_change = (recent_data[close_col].iloc[-1] / recent_data[close_col].iloc[0] - 1) * (252 / len(recent_data))
        
        # 3. Drawdown severity
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative / running_max - 1).min()
        
        # 4. Volatility regime (low vol = risk-on, high vol = risk-off)
        vol_percentile = (volatility - returns.std() * np.sqrt(252)) / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
        
        # Regime classification (incorporating macro indicators)
        # Risk-Off signals:
        # - High volatility (VIX > 30 or realized vol > 30%)
        # - Inverted yield curve (if available)
        # - Severe drawdown
        # - Negative trend
        
        risk_off_signals = 0
        risk_on_signals = 0
        
        # Try to get yield curve signal (may not be available)
        yield_curve_signal = None
        try:
            yield_data = self._fetch_yield_curve()
            if yield_data is not None and len(yield_data) > 0:
                # Use most recent yield curve data
                yield_curve_signal = yield_data.iloc[-1] if hasattr(yield_data, 'iloc') else yield_data[-1]
        except:
            pass
        
        # Count risk-off signals (more sensitive thresholds)
        if volatility > 0.25:  # High volatility (lowered from 0.30)
            risk_off_signals += 1
        if yield_curve_signal is not None and yield_curve_signal < -0.2:  # Inverted yield curve (less strict)
            risk_off_signals += 1
        if drawdown < -0.12:  # Severe drawdown (less strict from -0.15)
            risk_off_signals += 1
        if price_change < -0.08:  # Negative trend (less strict from -0.10)
            risk_off_signals += 1
        
        # Count risk-on signals (more sensitive thresholds)
        if volatility < 0.25:  # Low volatility (raised from 0.20 to catch more cases)
            risk_on_signals += 1
        if yield_curve_signal is not None and yield_curve_signal > 0.1:  # Steep yield curve (more strict)
            risk_on_signals += 1
        if price_change > 0.08:  # Positive trend (less strict from 0.10)
            risk_on_signals += 1
        if drawdown > -0.08:  # Low drawdown (less strict from -0.05)
            risk_on_signals += 1
        
        # Classify regime based on signal strength
        # Made more sensitive to detect regimes more frequently
        if risk_off_signals >= 2 or (volatility > 0.30 or drawdown < -0.15):
            regime = 'risk_off'
            # Multiplier: 0.3x to 0.7x based on severity
            if volatility > 0.35 or drawdown < -0.20 or (yield_curve_signal is not None and yield_curve_signal < -0.3):
                multiplier = 0.3  # Severe risk-off
            elif volatility > 0.30 or drawdown < -0.15:
                multiplier = 0.5  # Moderate risk-off
            else:
                multiplier = 0.7  # Mild risk-off
        
        elif risk_on_signals >= 2 and volatility < 0.30 and price_change > 0.05:
            regime = 'risk_on'
            # Multiplier: 1.2x to 1.5x based on strength
            if volatility < 0.18 and price_change > 0.12 and (yield_curve_signal is not None and yield_curve_signal > 0.1):
                multiplier = 1.5  # Strong risk-on
            elif volatility < 0.25 and price_change > 0.08:
                multiplier = 1.3  # Moderate risk-on
            else:
                multiplier = 1.2  # Mild risk-on
        
        # Neutral: Everything else
        else:
            regime = 'neutral'
            multiplier = 1.0
        
        return regime, multiplier
    
    def get_regime_multiplier(self, data: pd.DataFrame, current_date: Optional[datetime] = None) -> float:
        """
        Get position sizing multiplier based on macro regime
        
        Args:
            data: Price data
            current_date: Current date
            
        Returns:
            Multiplier (0.3 to 1.5)
        """
        regime, multiplier = self.detect_regime_from_price(data, current_date)
        
        # Track regime history
        if current_date:
            self.regime_history.append({
                'date': current_date,
                'regime': regime,
                'multiplier': multiplier
            })
        
        return multiplier
    
    def get_regime_summary(self) -> Dict:
        """Get summary of regime history"""
        if not self.regime_history:
            return {}
        
        regimes = [r['regime'] for r in self.regime_history]
        multipliers = [r['multiplier'] for r in self.regime_history]
        
        regime_counts = {}
        for regime in ['risk_on', 'neutral', 'risk_off']:
            count = regimes.count(regime)
            regime_counts[regime] = {
                'count': count,
                'percentage': (count / len(regimes)) * 100 if regimes else 0,
                'avg_multiplier': np.mean([m for r, m in zip(regimes, multipliers) if r == regime]) if any(r == regime for r in regimes) else 0
            }
        
        return {
            'total_periods': len(self.regime_history),
            'regimes': regime_counts,
            'avg_multiplier': np.mean(multipliers)
        }


class FiveTrenchPositionSizer:
    """
    Implements the 5-Trench position sizing model:
    Final Size = Base × Volatility × Regime × Classification × Persona
    """
    
    def __init__(self, 
                 base_pct: float = 0.04,
                 max_position_pct: float = 0.15,
                 macro_regime_detector: Optional[MacroRegimeDetector] = None):
        """
        Initialize 5-Trench position sizer
        
        Args:
            base_pct: Base position percentage (default: 4%)
            max_position_pct: Maximum position cap (default: 15%)
            macro_regime_detector: Macro regime detector instance
        """
        self.base_pct = base_pct
        self.max_position_pct = max_position_pct
        self.macro_detector = macro_regime_detector or MacroRegimeDetector()
    
    def calculate_position_size(self,
                                portfolio_value: float,
                                price: float,
                                data: pd.DataFrame,
                                volatility_multiplier: Optional[float] = None,
                                classification_multiplier: float = 1.0,  # CORE=1.2, SATELLITE=0.8
                                persona_multiplier: float = 1.0,  # Aggression: 0.7-1.2
                                current_date: Optional[datetime] = None) -> Tuple[int, Dict]:
        """
        Calculate position size using 5-Trench model
        
        Args:
            portfolio_value: Total portfolio value
            price: Current price
            data: Historical price data for regime detection
            volatility_multiplier: Volatility multiplier (0.5x-2.0x). If None, auto-calculated
            classification_multiplier: CORE vs SATELLITE (0.8x-1.2x)
            persona_multiplier: Aggression level (0.7x-1.2x)
            current_date: Current date for regime detection
            
        Returns:
            Tuple of (quantity, breakdown_dict)
        """
        # Trench 1: Base (4%)
        base_size = self.base_pct
        
        # Trench 2: Volatility (0.5x - 2.0x)
        if volatility_multiplier is None:
            # Auto-calculate from recent volatility
            if len(data) >= 60:
                # Handle both 'close' and 'Close' column names
                close_col = 'close' if 'close' in data.columns else 'Close'
                returns = data[close_col].pct_change().dropna()
                recent_vol = returns.tail(20).std() * np.sqrt(252)
                avg_vol = returns.std() * np.sqrt(252)
                
                if avg_vol > 0:
                    vol_ratio = recent_vol / avg_vol
                    # Higher vol = smaller multiplier (risk reduction)
                    # Lower vol = larger multiplier (opportunity)
                    if vol_ratio > 1.5:
                        volatility_multiplier = 0.5  # Very high vol
                    elif vol_ratio > 1.2:
                        volatility_multiplier = 0.7  # High vol
                    elif vol_ratio < 0.7:
                        volatility_multiplier = 1.5  # Low vol
                    elif vol_ratio < 0.9:
                        volatility_multiplier = 1.2  # Below avg vol
                    else:
                        volatility_multiplier = 1.0  # Normal vol
                else:
                    volatility_multiplier = 1.0
            else:
                volatility_multiplier = 1.0
        volatility_multiplier = max(0.5, min(2.0, volatility_multiplier))
        
        # Trench 3: Regime (Macro) (0.3x - 1.5x)
        regime_multiplier = self.macro_detector.get_regime_multiplier(data, current_date)
        
        # Trench 4: Classification (0.8x - 1.2x)
        classification_multiplier = max(0.8, min(1.2, classification_multiplier))
        
        # Trench 5: Persona (0.7x - 1.2x)
        persona_multiplier = max(0.7, min(1.2, persona_multiplier))
        
        # Calculate final position size
        final_pct = (base_size * 
                    volatility_multiplier * 
                    regime_multiplier * 
                    classification_multiplier * 
                    persona_multiplier)
        
        # Apply hard cap
        final_pct = min(final_pct, self.max_position_pct)
        
        # Calculate quantity
        position_value = portfolio_value * final_pct
        quantity = int(position_value / price) if price > 0 else 0
        
        # Build breakdown
        breakdown = {
            'base_pct': base_size,
            'volatility_multiplier': volatility_multiplier,
            'regime_multiplier': regime_multiplier,
            'classification_multiplier': classification_multiplier,
            'persona_multiplier': persona_multiplier,
            'final_pct': final_pct,
            'position_value': position_value,
            'quantity': quantity
        }
        
        return quantity, breakdown
