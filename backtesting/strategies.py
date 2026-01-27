"""
Concrete Strategy Implementations
Example strategies for backtesting
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from .strategy_base import StrategyBase, Signal


class MovingAverageCrossoverStrategy(StrategyBase):
    """Simple Moving Average Crossover Strategy"""
    
    def __init__(self, short_window: int = 20, long_window: int = 50):
        """
        Initialize MA Crossover strategy
        
        Args:
            short_window: Short MA period
            long_window: Long MA period
        """
        self.short_window = short_window
        self.long_window = long_window
        self.name = f"MA Crossover ({short_window}/{long_window})"
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate trading signals based on MA crossover"""
        signals = []
        
        # Get symbol from data if available
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # Calculate moving averages
        data['short_ma'] = data['close'].rolling(window=self.short_window).mean()
        data['long_ma'] = data['close'].rolling(window=self.long_window).mean()
        
        # Generate signals
        position = 0  # 0 = no position, 1 = long, -1 = short
        
        for i in range(self.long_window, len(data)):
            current_price = data['close'].iloc[i]
            short_ma = data['short_ma'].iloc[i]
            long_ma = data['long_ma'].iloc[i]
            prev_short_ma = data['short_ma'].iloc[i-1]
            prev_long_ma = data['long_ma'].iloc[i-1]
            
            # Golden cross: short MA crosses above long MA
            if prev_short_ma <= prev_long_ma and short_ma > long_ma:
                if position != 1:
                    signals.append(Signal(
                        symbol=symbol,
                        action='BUY',
                        price=current_price,
                        quantity=1,  # Will be normalized by position sizing
                        strength=0.7,
                        reason=f"Golden cross: {self.short_window} MA crossed above {self.long_window} MA"
                    ))
                    position = 1
            
            # Death cross: short MA crosses below long MA
            elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
                if position != -1:
                    signals.append(Signal(
                        symbol=symbol,
                        action='SELL',
                        price=current_price,
                        quantity=1,
                        strength=0.7,
                        reason=f"Death cross: {self.short_window} MA crossed below {self.long_window} MA"
                    ))
                    position = -1
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        """Calculate position size based on risk per trade"""
        if signal.price <= 0:
            return 0
        risk_amount = portfolio_value * risk_per_trade
        position_size = int(risk_amount / signal.price)
        return max(1, position_size)  # Minimum 1 share


class MomentumStrategy(StrategyBase):
    """Momentum-based strategy"""
    
    def __init__(self, lookback_period: int = 20, threshold: float = 0.02):
        """
        Initialize momentum strategy
        
        Args:
            lookback_period: Period for momentum calculation
            threshold: Minimum momentum threshold (2% default)
        """
        self.lookback_period = lookback_period
        self.threshold = threshold
        self.name = f"Momentum ({lookback_period}d, {threshold*100}%)"
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on momentum"""
        signals = []
        
        # Get symbol from data if available
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # Calculate momentum
        data['momentum'] = data['close'].pct_change(periods=self.lookback_period)
        
        position = 0
        
        for i in range(self.lookback_period, len(data)):
            momentum = data['momentum'].iloc[i]
            current_price = data['close'].iloc[i]
            
            # Buy on strong positive momentum
            if momentum > self.threshold and position != 1:
                signals.append(Signal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=1,
                    strength=min(abs(momentum) / self.threshold, 1.0),
                    reason=f"Strong positive momentum: {momentum:.2%}"
                ))
                position = 1
            
            # Sell on strong negative momentum
            elif momentum < -self.threshold and position != -1:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=min(abs(momentum) / self.threshold, 1.0),
                    reason=f"Strong negative momentum: {momentum:.2%}"
                ))
                position = -1
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        """Calculate position size based on risk per trade"""
        if signal.price <= 0:
            return 0
        risk_amount = portfolio_value * risk_per_trade
        position_size = int(risk_amount / signal.price)
        return max(1, position_size)  # Minimum 1 share


class MeanReversionStrategy(StrategyBase):
    """Mean reversion strategy using Bollinger Bands"""
    
    def __init__(self, window: int = 20, num_std: float = 2.0):
        """
        Initialize mean reversion strategy
        
        Args:
            window: Rolling window for mean/std calculation
            num_std: Number of standard deviations for bands
        """
        self.window = window
        self.num_std = num_std
        self.name = f"Mean Reversion (BB {window}d, {num_std}σ)"
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on mean reversion"""
        signals = []
        
        # Get symbol from data if available
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # Calculate Bollinger Bands
        data['mean'] = data['close'].rolling(window=self.window).mean()
        data['std'] = data['close'].rolling(window=self.window).std()
        data['upper_band'] = data['mean'] + (self.num_std * data['std'])
        data['lower_band'] = data['mean'] - (self.num_std * data['std'])
        
        position = 0
        
        for i in range(self.window, len(data)):
            current_price = data['close'].iloc[i]
            upper_band = data['upper_band'].iloc[i]
            lower_band = data['lower_band'].iloc[i]
            mean = data['mean'].iloc[i]
            
            # Buy when price touches lower band (oversold)
            if current_price <= lower_band and position != 1:
                signals.append(Signal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=1,
                    strength=0.6,
                    reason=f"Price touched lower Bollinger Band ({self.num_std}σ below mean)"
                ))
                position = 1
            
            # Sell when price touches upper band (overbought)
            elif current_price >= upper_band and position != -1:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=0.6,
                    reason=f"Price touched upper Bollinger Band ({self.num_std}σ above mean)"
                ))
                position = -1
            
            # Exit when price returns to mean
            elif position == 1 and current_price >= mean:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=0.5,
                    reason="Price returned to mean (exit signal)"
                ))
                position = 0
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        """Calculate position size based on risk per trade"""
        if signal.price <= 0:
            return 0
        risk_amount = portfolio_value * risk_per_trade
        position_size = int(risk_amount / signal.price)
        return max(1, position_size)  # Minimum 1 share


class RSIStrategy(StrategyBase):
    """RSI-based strategy"""
    
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        """
        Initialize RSI strategy
        
        Args:
            period: RSI calculation period
            oversold: RSI oversold threshold
            overbought: RSI overbought threshold
        """
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.name = f"RSI ({period}d, {oversold}/{overbought})"
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on RSI"""
        signals = []
        
        # Get symbol from data if available
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # Calculate RSI
        data['rsi'] = self._calculate_rsi(data['close'], self.period)
        
        position = 0
        
        for i in range(self.period, len(data)):
            rsi = data['rsi'].iloc[i]
            current_price = data['close'].iloc[i]
            
            # Buy when RSI crosses above oversold
            if rsi < self.oversold and position != 1:
                signals.append(Signal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=1,
                    strength=0.65,
                    reason=f"RSI oversold ({rsi:.1f} < {self.oversold})"
                ))
                position = 1
            
            # Sell when RSI crosses below overbought
            elif rsi > self.overbought and position != -1:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=0.65,
                    reason=f"RSI overbought ({rsi:.1f} > {self.overbought})"
                ))
                position = -1
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        """Calculate position size based on risk per trade"""
        if signal.price <= 0:
            return 0
        risk_amount = portfolio_value * risk_per_trade
        position_size = int(risk_amount / signal.price)
        return max(1, position_size)  # Minimum 1 share
