"""
Advanced Strategy Implementations
Institutional-grade trading strategies for backtesting
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from .strategy_base import StrategyBase, Signal


# ========== INVENTORY-AWARE TRENCH STRATEGY (INSTITUTIONAL) ==========

class InventoryAwareTrenchStrategy(StrategyBase):
    """Inventory-aware trench execution strategy (Institutional)"""
    
    def __init__(self, atr_period: int = 14, trench_levels: int = 3, 
                 risk_limit: float = 0.25, base_position_pct: float = 0.3,
                 max_position_pct: float = 0.15):
        """
        Initialize inventory-aware trench strategy
        
        Args:
            atr_period: Period for ATR calculation
            trench_levels: Number of trench levels
            risk_limit: Maximum risk per position
            base_position_pct: Base position as % of target
            max_position_pct: Maximum position size per instrument (default: 15%)
        """
        self.atr_period = atr_period
        self.trench_levels = trench_levels
        self.risk_limit = risk_limit
        self.base_position_pct = base_position_pct
        self.max_position_pct = max_position_pct  # Hard cap: 15% per instrument
        self.name = f"Inventory-Aware Trench Strategy (Institutional)"
        self.inventory = {}  # Track inventory per symbol
        
    def _calculate_atr(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.atr_period).mean()
        return atr
    
    def generate_signals(self, data: pd.DataFrame, portfolio_value: float = None) -> List[Signal]:
        """
        Generate signals based on inventory-aware trench strategy
        
        Args:
            data: Historical price data
            portfolio_value: Current portfolio value (for position sizing calculations)
        """
        signals = []
        
        # Get symbol from data
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # Need at least ATR period + some data for moving averages
        if len(data) < max(self.atr_period + 1, 50):
            return signals
        
        # Calculate ATR
        atr = self._calculate_atr(data)
        
        # Initialize inventory tracking
        if symbol not in self.inventory:
            self.inventory[symbol] = {
                'position': 0,  # Current position level (0 to trench_levels)
                'avg_price': 0.0,
                'target_position': 0,
                'deployed_trenches': [],  # Track which trench levels have been deployed
                'current_position_value': 0.0,  # Current position value in dollars
                'current_position_pct': 0.0  # Current position as % of portfolio
            }
        
        inv = self.inventory[symbol]
        
        # Only process the most recent data point to avoid multiple signals per day
        # The backtesting engine calls this once per day with all historical data
        i = len(data) - 1
        
        if i < self.atr_period:
            return signals
        
        current_price = data['close'].iloc[i]
        current_atr = atr.iloc[i]
        
        if pd.isna(current_atr) or current_atr == 0:
            return signals
        
        # Determine trend status
        sma_20 = data['close'].rolling(20).mean().iloc[i] if i >= 20 else current_price
        sma_50 = data['close'].rolling(50).mean().iloc[i] if i >= 50 else sma_20
        
        # Check if trend is intact (bullish)
        trend_intact = current_price > sma_20 > sma_50
        trend_bearish = current_price < sma_20 < sma_50
        
        # Get current position percentage (updated by backtest engine before signal generation)
        current_position_pct = inv.get('current_position_pct', 0.0)
        
        # Check if target_position was already set by macro regime (from backtest engine)
        # If so, use that instead of recalculating based on trend strength
        macro_regime_set = inv.get('_macro_regime_target', False)
        macro_regime_target = inv.get('target_position')
        
        if macro_regime_set and macro_regime_target is not None and macro_regime_target > 0:
            # Macro regime has set target_position - use it, but ensure it's valid
            target_position = min(macro_regime_target, self.trench_levels)
            # Ensure we don't exceed capacity
            remaining_capacity_pct = self.max_position_pct - current_position_pct
            trench_size_pct = self.max_position_pct / self.trench_levels
            max_additional_trenches = int(remaining_capacity_pct / trench_size_pct) if trench_size_pct > 0 else 0
            current_position_count = inv.get('position', 0)
            max_possible_position = current_position_count + max_additional_trenches
            target_position = min(target_position, max_possible_position)
            # Keep the flag so we know macro regime is controlling this
        else:
            # No macro regime target - calculate based on trend strength (standard logic)
            if trend_intact:
                # Calculate trend strength
                price_above_sma20 = (current_price / sma_20 - 1) * 100 if sma_20 > 0 else 0
                sma20_above_sma50 = (sma_20 / sma_50 - 1) * 100 if sma_50 > 0 else 0
                
                # Calculate how many trenches we can deploy based on remaining capacity
                remaining_capacity_pct = self.max_position_pct - current_position_pct
                trench_size_pct = self.max_position_pct / self.trench_levels
                
                if remaining_capacity_pct > 0.01:  # At least 1% remaining
                    max_additional_trenches = int(remaining_capacity_pct / trench_size_pct) + 1
                    # Target based on trend strength, but limited by capacity
                    if price_above_sma20 > 5 and sma20_above_sma50 > 3:
                        target_position = min(self.trench_levels, inv.get('position', 0) + max_additional_trenches)
                    elif price_above_sma20 > 2 and sma20_above_sma50 > 1:
                        target_position = min(max(2, self.trench_levels - 1), inv.get('position', 0) + max_additional_trenches)
                    else:
                        target_position = min(1, inv.get('position', 0) + max_additional_trenches)
                else:
                    # Already at or near 15% cap
                    target_position = inv.get('position', 0)
            elif trend_bearish:
                target_position = -1
            else:
                # Neutral: maintain current position
                target_position = inv.get('position', 0)
        
        inv['target_position'] = target_position
        
        # Get current position level (0 = flat, 1-N = number of trenches deployed)
        position = inv['position']
        deployed_trenches = inv.get('deployed_trenches', [])
        
        # NEW LOGIC: Trench buying - Scale into position incrementally as trend continues
        # Deploy trenches until position reaches 15% of capital per instrument
        if trend_intact and current_position_pct < self.max_position_pct:
            # Get previous day's price if available (for price change detection)
            prev_price = None
            price_change_pct = 0.0
            if i > 0:
                prev_price = data['close'].iloc[i-1]
                price_change_pct = (current_price - prev_price) / prev_price if prev_price > 0 else 0
            
            # Calculate how much each trench should add (incremental sizing)
            # Use max_position_pct / trench_levels as default, but this may be overridden
            # by macro regime via calculate_position_size method
            trench_size_pct = self.max_position_pct / self.trench_levels  # Equal allocation per trench
            remaining_capacity_pct = self.max_position_pct - current_position_pct
            
            # CRITICAL: Ensure we never exceed max_position_pct cap
            # This check prevents deploying trenches that would exceed the 15% limit
            
            # Check each trench level (closest to farthest)
            for level in range(1, self.trench_levels + 1):
                # Skip if this trench level already deployed
                if level in deployed_trenches:
                    continue
                
                # Check if deploying this trench would exceed 15% cap
                next_position_pct = current_position_pct + trench_size_pct
                if next_position_pct > self.max_position_pct:
                    # Would exceed cap - don't deploy
                    continue
                
                # Trench price is BELOW current price (buy on dips)
                trench_price = current_price - (current_atr * level * 0.5)
                distance_to_trench = abs(current_price - trench_price) / current_price if current_price > 0 else 1.0
                
                # NEW LOGIC: Deploy trench if trend intact and below target
                should_deploy = False
                
                if position < target_position:
                    # Condition 1: No position yet - deploy first trench immediately when trend intact
                    # This ensures we enter positions when trend is detected
                    if position == 0:
                        should_deploy = True
                    
                    # Condition 2: Price dropped significantly (dip buying)
                    elif prev_price and ((price_change_pct < -0.01 and distance_to_trench <= 0.02) or current_price <= trench_price):
                        should_deploy = True
                    
                    # Condition 3: Trend continuation - deploy on small pullback (within 5% of trench)
                    elif distance_to_trench <= 0.05:
                        should_deploy = True
                    
                    # Condition 4: If we're significantly below target, deploy on any opportunity
                    elif target_position - position >= 2:
                        # Need 2+ more trenches - be more aggressive
                        should_deploy = True
                
                if should_deploy:
                    signals.append(Signal(
                        symbol=symbol,
                        action='BUY',
                        price=current_price,  # Execute at current price
                        quantity=1,
                        strength=0.7 / level,  # Stronger signal for closer trenches
                        reason=f"Trench {level}/{self.trench_levels}: Trend intact, scaling to {next_position_pct*100:.1f}% (cap: {self.max_position_pct*100:.0f}%)"
                    ))
                    inv['position'] = min(inv['position'] + 1, target_position)
                    deployed_trenches.append(level)
                    inv['deployed_trenches'] = deployed_trenches
                    break  # Only deploy one trench per signal
        
        # Trench selling logic: Institutional-style profit-taking
        # ONLY book profits when there's a STRUCTURAL/REGIME CHANGE, not just profit percentage
        # Institutional approach: Hold positions unless structural shift occurs
        if position > 0:
            # Check previous day's price to detect if we've hit a sell trench
            if i > 0:
                prev_price = data['close'].iloc[i-1]
                price_change_pct = (current_price - prev_price) / prev_price if prev_price > 0 else 0
                
                # Calculate average entry price for profit calculation
                avg_entry_price = inv.get('avg_entry_price', current_price)
                if avg_entry_price <= 0:
                    avg_entry_price = current_price
                
                # Calculate unrealized profit percentage
                profit_pct = ((current_price - avg_entry_price) / avg_entry_price) * 100 if avg_entry_price > 0 else 0
                
                # Detect structural/regime changes (institutional profit-taking trigger)
                structural_change_detected = False
                structural_change_type = ""
                
                # 1. Trend reversal (bullish -> bearish) - structural change
                if target_position < 0:
                    structural_change_detected = True
                    structural_change_type = "trend reversal (bullish->bearish)"
                
                # 2. Volatility regime shift (low vol -> high vol) - DRASTIC structural change only
                if i >= 60:  # Need enough history for reliable comparison
                    recent_volatility = data['close'].iloc[max(0, i-20):i+1].pct_change().std() * np.sqrt(252)
                    longer_volatility = data['close'].iloc[max(0, i-60):i+1].pct_change().std() * np.sqrt(252)
                    # DRASTIC volatility spike: recent vol > 2.0x longer-term vol AND > 40% (very high)
                    if recent_volatility > longer_volatility * 2.0 and recent_volatility > 0.40:
                        structural_change_detected = True
                        structural_change_type = f"drastic volatility regime shift (low->high: {recent_volatility:.1%})"
                
                # 3. Major drawdown (structural breakdown) - DRASTIC only
                if i >= 30:
                    recent_high = data['close'].iloc[max(0, i-30):i+1].max()
                    drawdown_pct = ((recent_high - current_price) / recent_high) * 100 if recent_high > 0 else 0
                    # DRASTIC drawdown: > 20% from recent high (not just 15%)
                    if drawdown_pct > 20.0:
                        structural_change_detected = True
                        structural_change_type = f"drastic drawdown ({drawdown_pct:.1f}% from high)"
                
                # 4. Trend momentum breakdown - DRASTIC only (confirmed breakdown, not just a dip)
                if i >= 50:
                    sma_20 = data['close'].rolling(20).mean().iloc[i]
                    sma_50 = data['close'].rolling(50).mean().iloc[i] if i >= 50 else sma_20
                    # Price breaks below both SMAs AND stays below for confirmation
                    if current_price < sma_20 < sma_50:
                        # Check if we were significantly above SMAs recently (not just touching)
                        if i >= 10:
                            prev_sma20 = data['close'].rolling(20).mean().iloc[i-10]
                            prev_price_10d = data['close'].iloc[i-10]
                            # Was significantly above (5%+), now below - confirmed breakdown
                            if prev_price_10d > prev_sma20 * 1.05:
                                structural_change_detected = True
                                structural_change_type = "drastic momentum breakdown (confirmed break below key SMAs)"
                
                # 5. Macro regime shift (if available via inventory) - DRASTIC only
                # Check if macro regime changed DRASTICALLY from risk-on to risk-off
                prev_regime = inv.get('prev_regime_multiplier', 1.0)
                current_regime = inv.get('regime_multiplier', 1.0)
                # DRASTIC shift: was clearly risk-on (>1.2x) and now clearly risk-off (<0.5x)
                if prev_regime > 1.2 and current_regime < 0.5:
                    structural_change_detected = True
                    structural_change_type = f"drastic macro regime shift (risk-on {prev_regime:.2f}x -> risk-off {current_regime:.2f}x)"
                
                # Store current regime for next comparison
                inv['prev_regime_multiplier'] = current_regime
                
                # Sell from highest trench level first (most profitable)
                # Reverse order: sell trench 3, then 2, then 1
                for level in reversed(range(1, min(position, self.trench_levels) + 1)):
                    if level not in deployed_trenches:
                        continue
                    
                    # Determine sell conditions based on structural changes
                    should_sell = False
                    sell_reason = ""
                    
                    if target_position < 0:
                        # Condition 1: Trend reversed (bearish) - sell immediately (structural change)
                        should_sell = True
                        sell_reason = f"Structural Change: Trend Reversal (Bearish) - Profit: {profit_pct:.1f}%"
                    elif structural_change_detected and profit_pct >= 20.0:
                        # Condition 2: Structural change detected AND profit >= 20% - institutional profit-taking
                        # This is the "20% one time profit" rule: only take profits when structural change occurs
                        should_sell = True
                        sell_reason = f"Structural Change: {structural_change_type} - Booking 20%+ Profit ({profit_pct:.1f}%)"
                    elif target_position == 0 and profit_pct >= 20.0:
                        # Condition 3: Trend neutral AND profit >= 20% - take profits (neutral is also a structural change)
                        should_sell = True
                        sell_reason = f"Structural Change: Trend Neutral - Booking 20%+ Profit ({profit_pct:.1f}%)"
                    elif trend_intact and target_position > 0:
                        # Condition 4: Trend intact - DO NOT take profits, let winners run!
                        # Institutional approach: Hold unless structural change occurs
                        should_sell = False  # Don't sell when trend is intact
                    
                    if should_sell:
                        signals.append(Signal(
                            symbol=symbol,
                            action='SELL',
                            price=current_price,  # Execute at current price
                            quantity=1,
                            strength=0.7 / level,
                            reason=f"Trench sell {level}/{position}: {sell_reason} - Price ${current_price:.2f} (Entry: ${avg_entry_price:.2f}, Profit: {profit_pct:.1f}%)"
                        ))
                        inv['position'] = max(inv['position'] - 1, 0)
                        if level in deployed_trenches:
                            deployed_trenches.remove(level)
                        inv['deployed_trenches'] = deployed_trenches
                        break  # Only sell one trench per signal
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        """
        Calculate position size for each trench incrementally
        Each trench adds equal amount until max 15% per instrument
        
        Args:
            signal: Trading signal
            portfolio_value: Current portfolio value
            risk_per_trade: Risk per trade (can be macro-regime adjusted)
        """
        if signal.price <= 0:
            return 0
        
        # Calculate position size per trench (incremental)
        # If risk_per_trade is significantly different from default (0.02), it's likely macro-regime adjusted
        # Use it to scale trench size, otherwise use standard calculation
        if risk_per_trade > 0.01 and risk_per_trade < 0.20:  # Reasonable range for macro-regime
            # Macro-regime adjusted: use risk_per_trade as target per trench
            trench_size_pct = risk_per_trade
        else:
            # Standard: Each trench adds: max_position_pct / trench_levels
            trench_size_pct = self.max_position_pct / self.trench_levels
        
        # Calculate how many trenches have been deployed
        symbol = signal.symbol
        if symbol in self.inventory:
            deployed_count = len(self.inventory[symbol].get('deployed_trenches', []))
        else:
            deployed_count = 0
        
        # This trench should add: trench_size_pct of portfolio
        trench_value = portfolio_value * trench_size_pct
        
        # CRITICAL: Ensure we don't exceed max_position_pct cap (15% per instrument)
        current_position_pct = self.inventory.get(symbol, {}).get('current_position_pct', 0.0)
        
        # Calculate what the next position would be after adding this trench
        next_position_pct = current_position_pct + trench_size_pct
        
        # If adding this trench would exceed cap, reduce trench size to fit within cap
        if next_position_pct > self.max_position_pct:
            # Adjust to not exceed cap - only deploy what fits
            remaining_capacity_pct = self.max_position_pct - current_position_pct
            if remaining_capacity_pct > 0.001:  # At least 0.1% remaining
                trench_value = portfolio_value * remaining_capacity_pct
            else:
                # Already at or over cap - don't deploy
                return 0
        
        position_size = int(trench_value / signal.price)
        return max(0, position_size)  # Return 0 if no capacity, not 1


# ========== TREND FOLLOWING STRATEGIES ==========

class BreakoutStrategy(StrategyBase):
    """Breakout strategy - buy on resistance breakouts"""
    
    def __init__(self, lookback_period: int = 20, breakout_threshold: float = 0.02):
        """
        Initialize breakout strategy
        
        Args:
            lookback_period: Period for calculating resistance levels
            breakout_threshold: Minimum breakout percentage (2% default)
        """
        self.lookback_period = lookback_period
        self.breakout_threshold = breakout_threshold
        self.name = f"Breakout ({lookback_period}d, {breakout_threshold*100}%)"
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on breakouts"""
        signals = []
        
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # Calculate resistance (rolling high)
        data['resistance'] = data['high'].rolling(window=self.lookback_period).max()
        data['support'] = data['low'].rolling(window=self.lookback_period).min()
        
        position = 0
        
        for i in range(self.lookback_period, len(data)):
            current_price = data['close'].iloc[i]
            resistance = data['resistance'].iloc[i-1]  # Previous period's resistance
            support = data['support'].iloc[i-1]
            
            # Breakout above resistance
            if current_price > resistance * (1 + self.breakout_threshold) and position != 1:
                signals.append(Signal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=1,
                    strength=min((current_price / resistance - 1) / self.breakout_threshold, 1.0),
                    reason=f"Breakout above resistance: {resistance:.2f}"
                ))
                position = 1
            
            # Breakdown below support
            elif current_price < support * (1 - self.breakout_threshold) and position != -1:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=min((1 - current_price / support) / self.breakout_threshold, 1.0),
                    reason=f"Breakdown below support: {support:.2f}"
                ))
                position = -1
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        if signal.price <= 0:
            return 0
        risk_amount = portfolio_value * risk_per_trade
        return max(1, int(risk_amount / signal.price))
    
    def get_regime_summary(self) -> Dict:
        """Get summary of regime selections"""
        if not self.regime_history:
            return {"current_regime": None, "regime_counts": {}, "strategy_counts": {}, "total_days": 0}
        
        regime_counts = {}
        strategy_counts = {}
        
        for date, regime, strategy_name in self.regime_history:
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
        
        return {
            "current_regime": self.current_regime,
            "current_strategy": self.strategy_mapping.get(self.current_regime, "Unknown"),
            "regime_counts": regime_counts,
            "strategy_counts": strategy_counts,
            "total_days": len(self.regime_history)
        }


class TimeSeriesMomentumStrategy(StrategyBase):
    """Time-series momentum strategy"""
    
    def __init__(self, short_period: int = 12, long_period: int = 26):
        """
        Initialize time-series momentum strategy
        
        Args:
            short_period: Short momentum period
            long_period: Long momentum period
        """
        self.short_period = short_period
        self.long_period = long_period
        self.name = f"Time-Series Momentum ({short_period}/{long_period})"
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on time-series momentum"""
        signals = []
        
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # Calculate momentum (rate of change)
        data['momentum_short'] = data['close'].pct_change(periods=self.short_period)
        data['momentum_long'] = data['close'].pct_change(periods=self.long_period)
        
        position = 0
        
        for i in range(self.long_period, len(data)):
            mom_short = data['momentum_short'].iloc[i]
            mom_long = data['momentum_long'].iloc[i]
            current_price = data['close'].iloc[i]
            
            # Buy when short momentum crosses above long momentum
            if mom_short > mom_long and mom_short > 0 and position != 1:
                signals.append(Signal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=1,
                    strength=min(abs(mom_short), 1.0),
                    reason=f"Time-series momentum: short={mom_short:.2%}, long={mom_long:.2%}"
                ))
                position = 1
            
            # Sell when short momentum crosses below long momentum
            elif mom_short < mom_long and mom_short < 0 and position != -1:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=min(abs(mom_short), 1.0),
                    reason=f"Time-series momentum reversal: short={mom_short:.2%}, long={mom_long:.2%}"
                ))
                position = -1
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        if signal.price <= 0:
            return 0
        risk_amount = portfolio_value * risk_per_trade
        return max(1, int(risk_amount / signal.price))
    
    def get_regime_summary(self) -> Dict:
        """Get summary of regime selections"""
        if not self.regime_history:
            return {"current_regime": None, "regime_counts": {}, "strategy_counts": {}, "total_days": 0}
        
        regime_counts = {}
        strategy_counts = {}
        
        for date, regime, strategy_name in self.regime_history:
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
        
        return {
            "current_regime": self.current_regime,
            "current_strategy": self.strategy_mapping.get(self.current_regime, "Unknown"),
            "regime_counts": regime_counts,
            "strategy_counts": strategy_counts,
            "total_days": len(self.regime_history)
        }


# ========== MOMENTUM STRATEGIES ==========

class CrossSectionalMomentumStrategy(StrategyBase):
    """Cross-sectional momentum - rank assets by performance"""
    
    def __init__(self, lookback_period: int = 20, top_n: int = 5):
        """
        Initialize cross-sectional momentum strategy
        
        Args:
            lookback_period: Period for momentum calculation
            top_n: Number of top performers to select
        """
        self.lookback_period = lookback_period
        self.top_n = top_n
        self.name = f"Cross-Sectional Momentum ({lookback_period}d, top {top_n})"
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on cross-sectional momentum"""
        # Note: This strategy requires multiple symbols, so for single symbol, use regular momentum
        signals = []
        
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # For single symbol, fall back to regular momentum
        data['momentum'] = data['close'].pct_change(periods=self.lookback_period)
        
        position = 0
        
        for i in range(self.lookback_period, len(data)):
            momentum = data['momentum'].iloc[i]
            current_price = data['close'].iloc[i]
            
            # Buy if momentum is positive and strong
            if momentum > 0.05 and position != 1:  # Top 5% momentum
                signals.append(Signal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=1,
                    strength=min(momentum / 0.1, 1.0),
                    reason=f"Cross-sectional momentum rank: {momentum:.2%}"
                ))
                position = 1
            
            # Sell if momentum turns negative
            elif momentum < -0.05 and position != -1:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=min(abs(momentum) / 0.1, 1.0),
                    reason=f"Cross-sectional momentum rank: {momentum:.2%}"
                ))
                position = -1
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        if signal.price <= 0:
            return 0
        risk_amount = portfolio_value * risk_per_trade
        return max(1, int(risk_amount / signal.price))
    
    def get_regime_summary(self) -> Dict:
        """Get summary of regime selections"""
        if not self.regime_history:
            return {"current_regime": None, "regime_counts": {}, "strategy_counts": {}, "total_days": 0}
        
        regime_counts = {}
        strategy_counts = {}
        
        for date, regime, strategy_name in self.regime_history:
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
        
        return {
            "current_regime": self.current_regime,
            "current_strategy": self.strategy_mapping.get(self.current_regime, "Unknown"),
            "regime_counts": regime_counts,
            "strategy_counts": strategy_counts,
            "total_days": len(self.regime_history)
        }


class VolatilityAdjustedMomentumStrategy(StrategyBase):
    """Volatility-adjusted momentum strategy"""
    
    def __init__(self, lookback_period: int = 20, vol_period: int = 20):
        """
        Initialize volatility-adjusted momentum strategy
        
        Args:
            lookback_period: Period for momentum calculation
            vol_period: Period for volatility calculation
        """
        self.lookback_period = lookback_period
        self.vol_period = vol_period
        self.name = f"Volatility-Adjusted Momentum ({lookback_period}d)"
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on volatility-adjusted momentum"""
        signals = []
        
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # Calculate momentum
        data['momentum'] = data['close'].pct_change(periods=self.lookback_period)
        
        # Calculate volatility (rolling std of returns)
        data['returns'] = data['close'].pct_change()
        data['volatility'] = data['returns'].rolling(window=self.vol_period).std()
        
        # Volatility-adjusted momentum (Sharpe-like)
        data['adj_momentum'] = data['momentum'] / (data['volatility'] + 1e-8)
        
        position = 0
        
        for i in range(max(self.lookback_period, self.vol_period), len(data)):
            adj_momentum = data['adj_momentum'].iloc[i]
            current_price = data['close'].iloc[i]
            volatility = data['volatility'].iloc[i]
            
            # Buy on high risk-adjusted momentum
            threshold = 0.5 / (volatility + 0.01)  # Adjust threshold by volatility
            if adj_momentum > threshold and position != 1:
                signals.append(Signal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=1,
                    strength=min(adj_momentum / (threshold * 2), 1.0),
                    reason=f"Volatility-adjusted momentum: {adj_momentum:.2f} (vol={volatility:.2%})"
                ))
                position = 1
            
            # Sell on negative risk-adjusted momentum
            elif adj_momentum < -threshold and position != -1:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=min(abs(adj_momentum) / (threshold * 2), 1.0),
                    reason=f"Volatility-adjusted momentum: {adj_momentum:.2f} (vol={volatility:.2%})"
                ))
                position = -1
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        if signal.price <= 0:
            return 0
        risk_amount = portfolio_value * risk_per_trade
        return max(1, int(risk_amount / signal.price))
    
    def get_regime_summary(self) -> Dict:
        """Get summary of regime selections"""
        if not self.regime_history:
            return {"current_regime": None, "regime_counts": {}, "strategy_counts": {}, "total_days": 0}
        
        regime_counts = {}
        strategy_counts = {}
        
        for date, regime, strategy_name in self.regime_history:
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
        
        return {
            "current_regime": self.current_regime,
            "current_strategy": self.strategy_mapping.get(self.current_regime, "Unknown"),
            "regime_counts": regime_counts,
            "strategy_counts": strategy_counts,
            "total_days": len(self.regime_history)
        }


# ========== MEAN REVERSION STRATEGIES ==========

class StatisticalMeanReversionStrategy(StrategyBase):
    """Statistical mean reversion using z-scores"""
    
    def __init__(self, window: int = 20, zscore_threshold: float = 2.0):
        """
        Initialize statistical mean reversion strategy
        
        Args:
            window: Rolling window for mean/std calculation
            zscore_threshold: Z-score threshold for signals
        """
        self.window = window
        self.zscore_threshold = zscore_threshold
        self.name = f"Statistical Mean Reversion ({window}d, {zscore_threshold}σ)"
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on statistical mean reversion"""
        signals = []
        
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # Calculate z-score
        data['mean'] = data['close'].rolling(window=self.window).mean()
        data['std'] = data['close'].rolling(window=self.window).std()
        data['zscore'] = (data['close'] - data['mean']) / (data['std'] + 1e-8)
        
        position = 0
        
        for i in range(self.window, len(data)):
            zscore = data['zscore'].iloc[i]
            current_price = data['close'].iloc[i]
            
            # Buy when z-score is very negative (oversold)
            if zscore < -self.zscore_threshold and position != 1:
                signals.append(Signal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=1,
                    strength=min(abs(zscore) / (self.zscore_threshold * 2), 1.0),
                    reason=f"Statistical oversold: z-score={zscore:.2f}"
                ))
                position = 1
            
            # Sell when z-score is very positive (overbought)
            elif zscore > self.zscore_threshold and position != -1:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=min(zscore / (self.zscore_threshold * 2), 1.0),
                    reason=f"Statistical overbought: z-score={zscore:.2f}"
                ))
                position = -1
            
            # Exit when z-score returns to mean
            elif position == 1 and zscore >= 0:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=0.5,
                    reason="Z-score returned to mean"
                ))
                position = 0
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        if signal.price <= 0:
            return 0
        risk_amount = portfolio_value * risk_per_trade
        return max(1, int(risk_amount / signal.price))
    
    def get_regime_summary(self) -> Dict:
        """Get summary of regime selections"""
        if not self.regime_history:
            return {"current_regime": None, "regime_counts": {}, "strategy_counts": {}, "total_days": 0}
        
        regime_counts = {}
        strategy_counts = {}
        
        for date, regime, strategy_name in self.regime_history:
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
        
        return {
            "current_regime": self.current_regime,
            "current_strategy": self.strategy_mapping.get(self.current_regime, "Unknown"),
            "regime_counts": regime_counts,
            "strategy_counts": strategy_counts,
            "total_days": len(self.regime_history)
        }


class VWAPReversionStrategy(StrategyBase):
    """VWAP-based mean reversion strategy"""
    
    def __init__(self, vwap_period: int = 20, deviation_threshold: float = 0.02):
        """
        Initialize VWAP reversion strategy
        
        Args:
            vwap_period: Period for VWAP calculation
            deviation_threshold: Deviation threshold from VWAP (2% default)
        """
        self.vwap_period = vwap_period
        self.deviation_threshold = deviation_threshold
        self.name = f"VWAP Reversion ({vwap_period}d, {deviation_threshold*100}%)"
    
    def _calculate_vwap(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Volume Weighted Average Price"""
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        vwap = (typical_price * data['volume']).rolling(window=self.vwap_period).sum() / \
               data['volume'].rolling(window=self.vwap_period).sum()
        return vwap
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on VWAP reversion"""
        signals = []
        
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # Calculate VWAP
        data['vwap'] = self._calculate_vwap(data)
        data['vwap_deviation'] = (data['close'] - data['vwap']) / data['vwap']
        
        position = 0
        
        for i in range(self.vwap_period, len(data)):
            deviation = data['vwap_deviation'].iloc[i]
            current_price = data['close'].iloc[i]
            vwap = data['vwap'].iloc[i]
            
            # Buy when price is significantly below VWAP
            if deviation < -self.deviation_threshold and position != 1:
                signals.append(Signal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=1,
                    strength=min(abs(deviation) / (self.deviation_threshold * 2), 1.0),
                    reason=f"Price {deviation:.2%} below VWAP ({vwap:.2f})"
                ))
                position = 1
            
            # Sell when price is significantly above VWAP
            elif deviation > self.deviation_threshold and position != -1:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=min(deviation / (self.deviation_threshold * 2), 1.0),
                    reason=f"Price {deviation:.2%} above VWAP ({vwap:.2f})"
                ))
                position = -1
            
            # Exit when price returns to VWAP
            elif position == 1 and deviation >= 0:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=0.5,
                    reason="Price returned to VWAP"
                ))
                position = 0
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        if signal.price <= 0:
            return 0
        risk_amount = portfolio_value * risk_per_trade
        return max(1, int(risk_amount / signal.price))
    
    def get_regime_summary(self) -> Dict:
        """Get summary of regime selections"""
        if not self.regime_history:
            return {"current_regime": None, "regime_counts": {}, "strategy_counts": {}, "total_days": 0}
        
        regime_counts = {}
        strategy_counts = {}
        
        for date, regime, strategy_name in self.regime_history:
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
        
        return {
            "current_regime": self.current_regime,
            "current_strategy": self.strategy_mapping.get(self.current_regime, "Unknown"),
            "regime_counts": regime_counts,
            "strategy_counts": strategy_counts,
            "total_days": len(self.regime_history)
        }


# ========== VOLATILITY STRATEGIES ==========

class VolatilityBreakoutStrategy(StrategyBase):
    """Volatility breakout strategy"""
    
    def __init__(self, vol_period: int = 20, breakout_multiplier: float = 1.5):
        """
        Initialize volatility breakout strategy
        
        Args:
            vol_period: Period for volatility calculation
            breakout_multiplier: Multiplier for volatility breakout threshold
        """
        self.vol_period = vol_period
        self.breakout_multiplier = breakout_multiplier
        self.name = f"Volatility Breakout ({vol_period}d, {breakout_multiplier}x)"
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on volatility breakouts"""
        signals = []
        
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # Calculate volatility
        data['returns'] = data['close'].pct_change()
        data['volatility'] = data['returns'].rolling(window=self.vol_period).std()
        data['vol_threshold'] = data['volatility'] * self.breakout_multiplier
        
        # Calculate price change
        data['price_change'] = data['close'].pct_change()
        
        position = 0
        
        for i in range(self.vol_period, len(data)):
            price_change = abs(data['price_change'].iloc[i])
            vol_threshold = data['vol_threshold'].iloc[i]
            current_price = data['close'].iloc[i]
            returns = data['returns'].iloc[i]
            
            # Buy on positive volatility breakout
            if price_change > vol_threshold and returns > 0 and position != 1:
                signals.append(Signal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=1,
                    strength=min(price_change / (vol_threshold * 2), 1.0),
                    reason=f"Volatility breakout: {price_change:.2%} > {vol_threshold:.2%}"
                ))
                position = 1
            
            # Sell on negative volatility breakout
            elif price_change > vol_threshold and returns < 0 and position != -1:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=min(price_change / (vol_threshold * 2), 1.0),
                    reason=f"Volatility breakdown: {price_change:.2%} > {vol_threshold:.2%}"
                ))
                position = -1
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        if signal.price <= 0:
            return 0
        risk_amount = portfolio_value * risk_per_trade
        return max(1, int(risk_amount / signal.price))
    
    def get_regime_summary(self) -> Dict:
        """Get summary of regime selections"""
        if not self.regime_history:
            return {"current_regime": None, "regime_counts": {}, "strategy_counts": {}, "total_days": 0}
        
        regime_counts = {}
        strategy_counts = {}
        
        for date, regime, strategy_name in self.regime_history:
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
        
        return {
            "current_regime": self.current_regime,
            "current_strategy": self.strategy_mapping.get(self.current_regime, "Unknown"),
            "regime_counts": regime_counts,
            "strategy_counts": strategy_counts,
            "total_days": len(self.regime_history)
        }


class TrenchDeploymentStrategy(StrategyBase):
    """Trench deployment strategy - volatility-based scaling"""
    
    def __init__(self, atr_period: int = 14, trench_count: int = 3):
        """
        Initialize trench deployment strategy
        
        Args:
            atr_period: Period for ATR calculation
            trench_count: Number of trench levels
        """
        self.atr_period = atr_period
        self.trench_count = trench_count
        self.name = f"Trench Deployment ({atr_period}d ATR, {trench_count} levels)"
    
    def _calculate_atr(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.atr_period).mean()
        return atr
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on trench deployment"""
        signals = []
        
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # Calculate ATR
        atr = self._calculate_atr(data)
        
        position = 0
        
        for i in range(self.atr_period, len(data)):
            current_price = data['close'].iloc[i]
            current_atr = atr.iloc[i]
            
            if pd.isna(current_atr) or current_atr == 0:
                continue
            
            # Determine trend direction
            sma_20 = data['close'].rolling(20).mean().iloc[i] if i >= 20 else current_price
            trend_up = current_price > sma_20
            
            # Deploy trenches below price for uptrend
            if trend_up and position < self.trench_count:
                for level in range(1, self.trench_count + 1):
                    trench_price = current_price - (current_atr * level * 0.5)
                    if abs(current_price - trench_price) / current_price < 0.03:  # Within 3%
                        signals.append(Signal(
                            symbol=symbol,
                            action='BUY',
                            price=trench_price,
                            quantity=1,
                            strength=0.6 / level,
                            reason=f"Trench deployment level {level}: {trench_price:.2f}"
                        ))
                        position += 1
                        break
            
            # Deploy trenches above price for downtrend
            elif not trend_up and position > -self.trench_count:
                for level in range(1, self.trench_count + 1):
                    trench_price = current_price + (current_atr * level * 0.5)
                    if abs(trench_price - current_price) / current_price < 0.03:
                        signals.append(Signal(
                            symbol=symbol,
                            action='SELL',
                            price=trench_price,
                            quantity=1,
                            strength=0.6 / level,
                            reason=f"Trench deployment level {level}: {trench_price:.2f}"
                        ))
                        position -= 1
                        break
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        if signal.price <= 0:
            return 0
        # Smaller position sizes for trench entries
        risk_amount = portfolio_value * risk_per_trade * 0.5
        return max(1, int(risk_amount / signal.price))


# ========== MARKET NEUTRAL STRATEGIES ==========

class PairsTradingStrategy(StrategyBase):
    """Pairs trading strategy (requires two symbols)"""
    
    def __init__(self, lookback_period: int = 20, zscore_threshold: float = 2.0):
        """
        Initialize pairs trading strategy
        
        Args:
            lookback_period: Period for spread calculation
            zscore_threshold: Z-score threshold for entry
        """
        self.lookback_period = lookback_period
        self.zscore_threshold = zscore_threshold
        self.name = f"Pairs Trading ({lookback_period}d, {zscore_threshold}σ)"
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on pairs trading"""
        # Note: This requires two symbols, so for single symbol, use statistical mean reversion
        signals = []
        
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # For single symbol, fall back to mean reversion
        data['mean'] = data['close'].rolling(window=self.lookback_period).mean()
        data['std'] = data['close'].rolling(window=self.lookback_period).std()
        data['zscore'] = (data['close'] - data['mean']) / (data['std'] + 1e-8)
        
        position = 0
        
        for i in range(self.lookback_period, len(data)):
            zscore = data['zscore'].iloc[i]
            current_price = data['close'].iloc[i]
            
            # Buy when z-score is very negative
            if zscore < -self.zscore_threshold and position != 1:
                signals.append(Signal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=1,
                    strength=min(abs(zscore) / (self.zscore_threshold * 2), 1.0),
                    reason=f"Pairs spread z-score: {zscore:.2f}"
                ))
                position = 1
            
            # Sell when z-score is very positive
            elif zscore > self.zscore_threshold and position != -1:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=min(zscore / (self.zscore_threshold * 2), 1.0),
                    reason=f"Pairs spread z-score: {zscore:.2f}"
                ))
                position = -1
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        if signal.price <= 0:
            return 0
        risk_amount = portfolio_value * risk_per_trade
        return max(1, int(risk_amount / signal.price))
    
    def get_regime_summary(self) -> Dict:
        """Get summary of regime selections"""
        if not self.regime_history:
            return {"current_regime": None, "regime_counts": {}, "strategy_counts": {}, "total_days": 0}
        
        regime_counts = {}
        strategy_counts = {}
        
        for date, regime, strategy_name in self.regime_history:
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
        
        return {
            "current_regime": self.current_regime,
            "current_strategy": self.strategy_mapping.get(self.current_regime, "Unknown"),
            "regime_counts": regime_counts,
            "strategy_counts": strategy_counts,
            "total_days": len(self.regime_history)
        }


class BetaNeutralLSStrategy(StrategyBase):
    """Beta-neutral long/short strategy"""
    
    def __init__(self, beta_period: int = 60, beta_target: float = 0.0):
        """
        Initialize beta-neutral strategy
        
        Args:
            beta_period: Period for beta calculation
            beta_target: Target beta (0.0 for market neutral)
        """
        self.beta_period = beta_period
        self.beta_target = beta_target
        self.name = f"Beta-Neutral L/S ({beta_period}d, target={beta_target})"
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on beta-neutral approach"""
        signals = []
        
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # Calculate rolling beta (simplified - would need market returns in production)
        data['returns'] = data['close'].pct_change()
        data['rolling_beta'] = data['returns'].rolling(window=self.beta_period).std() / \
                               (data['returns'].rolling(window=self.beta_period).std() + 1e-8)
        
        # Use momentum with beta adjustment
        data['momentum'] = data['close'].pct_change(periods=20)
        
        position = 0
        
        for i in range(self.beta_period, len(data)):
            momentum = data['momentum'].iloc[i]
            current_price = data['close'].iloc[i]
            beta = data['rolling_beta'].iloc[i]
            
            # Adjust momentum by beta to make it market-neutral
            beta_adjusted_momentum = momentum - (beta * momentum)
            
            # Buy on positive beta-adjusted momentum
            if beta_adjusted_momentum > 0.02 and position != 1:
                signals.append(Signal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=1,
                    strength=min(beta_adjusted_momentum / 0.05, 1.0),
                    reason=f"Beta-adjusted momentum: {beta_adjusted_momentum:.2%} (beta={beta:.2f})"
                ))
                position = 1
            
            # Sell on negative beta-adjusted momentum
            elif beta_adjusted_momentum < -0.02 and position != -1:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=min(abs(beta_adjusted_momentum) / 0.05, 1.0),
                    reason=f"Beta-adjusted momentum: {beta_adjusted_momentum:.2%} (beta={beta:.2f})"
                ))
                position = -1
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        if signal.price <= 0:
            return 0
        risk_amount = portfolio_value * risk_per_trade
        return max(1, int(risk_amount / signal.price))
    
    def get_regime_summary(self) -> Dict:
        """Get summary of regime selections"""
        if not self.regime_history:
            return {"current_regime": None, "regime_counts": {}, "strategy_counts": {}, "total_days": 0}
        
        regime_counts = {}
        strategy_counts = {}
        
        for date, regime, strategy_name in self.regime_history:
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
        
        return {
            "current_regime": self.current_regime,
            "current_strategy": self.strategy_mapping.get(self.current_regime, "Unknown"),
            "regime_counts": regime_counts,
            "strategy_counts": strategy_counts,
            "total_days": len(self.regime_history)
        }


# ========== ALLOCATION STRATEGIES ==========

class RiskParityStrategy(StrategyBase):
    """Risk parity allocation strategy"""
    
    def __init__(self, rebalance_period: int = 20, target_volatility: float = 0.15):
        """
        Initialize risk parity strategy
        
        Args:
            rebalance_period: Period for rebalancing
            target_volatility: Target portfolio volatility (15% default)
        """
        self.rebalance_period = rebalance_period
        self.target_volatility = target_volatility
        self.name = f"Risk Parity (rebalance {rebalance_period}d, vol={target_volatility*100}%)"
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on risk parity"""
        signals = []
        
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # Calculate volatility
        data['returns'] = data['close'].pct_change()
        data['volatility'] = data['returns'].rolling(window=self.rebalance_period).std() * np.sqrt(252)
        
        # Calculate inverse volatility weights (risk parity)
        data['inv_vol'] = 1.0 / (data['volatility'] + 1e-8)
        data['target_weight'] = data['inv_vol'] / data['inv_vol'].rolling(window=self.rebalance_period).sum()
        
        position = 0
        
        for i in range(self.rebalance_period, len(data)):
            current_price = data['close'].iloc[i]
            target_weight = data['target_weight'].iloc[i]
            volatility = data['volatility'].iloc[i]
            
            # Adjust position based on target weight
            target_position = 1 if target_weight > 0.5 else -1 if target_weight < 0.3 else 0
            
            if target_position == 1 and position != 1:
                signals.append(Signal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=1,
                    strength=target_weight,
                    reason=f"Risk parity allocation: weight={target_weight:.2%}, vol={volatility:.2%}"
                ))
                position = 1
            elif target_position == -1 and position != -1:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=1 - target_weight,
                    reason=f"Risk parity allocation: weight={target_weight:.2%}, vol={volatility:.2%}"
                ))
                position = -1
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        if signal.price <= 0:
            return 0
        # Risk parity uses volatility-adjusted sizing
        risk_amount = portfolio_value * risk_per_trade * signal.strength
        return max(1, int(risk_amount / signal.price))


class MeanVarianceStrategy(StrategyBase):
    """Mean-variance optimization strategy"""
    
    def __init__(self, lookback_period: int = 60, risk_aversion: float = 2.0):
        """
        Initialize mean-variance strategy
        
        Args:
            lookback_period: Period for return/volatility calculation
            risk_aversion: Risk aversion parameter
        """
        self.lookback_period = lookback_period
        self.risk_aversion = risk_aversion
        self.name = f"Mean-Variance ({lookback_period}d, λ={risk_aversion})"
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on mean-variance optimization"""
        signals = []
        
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # Calculate expected return and volatility
        data['returns'] = data['close'].pct_change()
        data['expected_return'] = data['returns'].rolling(window=self.lookback_period).mean() * 252
        data['volatility'] = data['returns'].rolling(window=self.lookback_period).std() * np.sqrt(252)
        
        # Calculate Sharpe ratio
        data['sharpe'] = data['expected_return'] / (data['volatility'] + 1e-8)
        
        # Mean-variance score
        data['mv_score'] = data['expected_return'] - (self.risk_aversion * data['volatility'] ** 2)
        
        position = 0
        
        for i in range(self.lookback_period, len(data)):
            mv_score = data['mv_score'].iloc[i]
            current_price = data['close'].iloc[i]
            sharpe = data['sharpe'].iloc[i]
            
            # Buy when mean-variance score is positive
            if mv_score > 0.05 and sharpe > 0.5 and position != 1:
                signals.append(Signal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=1,
                    strength=min(mv_score / 0.1, 1.0),
                    reason=f"Mean-variance score: {mv_score:.3f}, Sharpe: {sharpe:.2f}"
                ))
                position = 1
            
            # Sell when mean-variance score turns negative
            elif mv_score < -0.05 or sharpe < -0.5 and position != -1:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=min(abs(mv_score) / 0.1, 1.0),
                    reason=f"Mean-variance score: {mv_score:.3f}, Sharpe: {sharpe:.2f}"
                ))
                position = -1
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        if signal.price <= 0:
            return 0
        risk_amount = portfolio_value * risk_per_trade
        return max(1, int(risk_amount / signal.price))
    
    def get_regime_summary(self) -> Dict:
        """Get summary of regime selections"""
        if not self.regime_history:
            return {"current_regime": None, "regime_counts": {}, "strategy_counts": {}, "total_days": 0}
        
        regime_counts = {}
        strategy_counts = {}
        
        for date, regime, strategy_name in self.regime_history:
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
        
        return {
            "current_regime": self.current_regime,
            "current_strategy": self.strategy_mapping.get(self.current_regime, "Unknown"),
            "regime_counts": regime_counts,
            "strategy_counts": strategy_counts,
            "total_days": len(self.regime_history)
        }


# ========== REGIME ADAPTIVE STRATEGY ==========

class AutoStrategySelectorStrategy(StrategyBase):
    """Auto strategy selector - adapts to market regime"""
    
    def __init__(self, regime_window: int = 60):
        """
        Initialize auto strategy selector
        
        Args:
            regime_window: Window for regime detection
        """
        self.regime_window = regime_window
        self.name = f"Auto Strategy Selector (regime {regime_window}d)"
        self.current_regime = None
        self.regime_history = []  # Track regime selections: [(date, regime, strategy_name)]
        self.strategy_mapping = {
            "mean_reverting": "Mean Reversion (Bollinger Bands)",
            "trending": "Moving Average Crossover",
            "momentum": "Momentum"
        }
    
    def _detect_regime(self, data: pd.DataFrame, i: int) -> str:
        """Detect market regime"""
        if i < self.regime_window:
            return "trending"
        
        # Calculate volatility and trend
        returns = data['close'].pct_change()
        volatility = returns.iloc[i-self.regime_window:i].std() * np.sqrt(252)
        trend = (data['close'].iloc[i] / data['close'].iloc[i-self.regime_window] - 1) * (252 / self.regime_window)
        
        # High volatility + low trend = mean reverting
        if volatility > 0.25 and abs(trend) < 0.10:
            return "mean_reverting"
        # Low volatility + high trend = trending
        elif volatility < 0.15 and abs(trend) > 0.15:
            return "trending"
        # Medium volatility = momentum
        else:
            return "momentum"
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on detected regime"""
        signals = []
        
        symbol = data.get('symbol', 'UNKNOWN') if isinstance(data, dict) else 'UNKNOWN'
        if hasattr(data, 'attrs') and 'symbol' in data.attrs:
            symbol = data.attrs['symbol']
        
        # Only process the most recent data point to avoid multiple signals per day
        # The backtesting engine calls this once per day with all historical data
        if len(data) < self.regime_window:
            return signals
        
        # Use only the last row (most recent date) for signal generation
        i = len(data) - 1
        
        regime = self._detect_regime(data, i)
        self.current_regime = regime
        current_price = data['close'].iloc[i]
        
        # Get the date from data index
        try:
            current_date = data.index[i] if hasattr(data.index, '__getitem__') else None
        except:
            current_date = None
        
        # Track regime selection
        strategy_name = self.strategy_mapping.get(regime, "Unknown")
        if current_date is not None:
            self.regime_history.append((current_date, regime, strategy_name))
        
        if regime == "mean_reverting":
            # Use Bollinger Bands
            window = 20
            mean = data['close'].rolling(window).mean().iloc[i]
            std = data['close'].rolling(window).std().iloc[i]
            upper = mean + 2 * std
            lower = mean - 2 * std
            
            if current_price <= lower:
                signals.append(Signal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=1,
                    strength=0.7,
                    reason=f"[{strategy_name}] Mean-reverting regime: price below lower band"
                ))
            elif current_price >= upper:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=0.7,
                    reason=f"[{strategy_name}] Mean-reverting regime: price above upper band"
                ))
        
        elif regime == "trending":
            # Use moving average crossover
            sma_20 = data['close'].rolling(20).mean().iloc[i]
            sma_50 = data['close'].rolling(50).mean().iloc[i] if i >= 50 else sma_20
            
            if sma_20 > sma_50:
                signals.append(Signal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=1,
                    strength=0.8,
                    reason=f"[{strategy_name}] Trending regime: MA crossover bullish"
                ))
            elif sma_20 < sma_50:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=0.8,
                    reason=f"[{strategy_name}] Trending regime: MA crossover bearish"
                ))
        
        else:  # momentum
            # Use momentum
            momentum = data['close'].pct_change(20).iloc[i]
            
            if momentum > 0.05:
                signals.append(Signal(
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    quantity=1,
                    strength=0.75,
                    reason=f"[{strategy_name}] Momentum regime: positive momentum {momentum:.2%}"
                ))
            elif momentum < -0.05:
                signals.append(Signal(
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    quantity=1,
                    strength=0.75,
                    reason=f"[{strategy_name}] Momentum regime: negative momentum {momentum:.2%}"
                ))
        
        return signals
    
    def calculate_position_size(self, signal: Signal, portfolio_value: float, risk_per_trade: float = 0.02) -> int:
        if signal.price <= 0:
            return 0
        risk_amount = portfolio_value * risk_per_trade
        return max(1, int(risk_amount / signal.price))
    
    def get_regime_summary(self) -> Dict:
        """Get summary of regime selections"""
        if not self.regime_history:
            return {"current_regime": None, "regime_counts": {}, "strategy_counts": {}, "total_days": 0}
        
        regime_counts = {}
        strategy_counts = {}
        
        for date, regime, strategy_name in self.regime_history:
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
        
        return {
            "current_regime": self.current_regime,
            "current_strategy": self.strategy_mapping.get(self.current_regime, "Unknown"),
            "regime_counts": regime_counts,
            "strategy_counts": strategy_counts,
            "total_days": len(self.regime_history)
        }
