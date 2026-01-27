"""
Backtesting Engine
Historical strategy validation framework
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
from .strategy_base import StrategyBase, Signal


@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    initial_capital: float = 100000.0
    commission: float = 0.001  # 0.1% commission
    slippage: float = 0.0005  # 0.05% slippage
    risk_free_rate: float = 0.02  # 2% risk-free rate
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    portfolio_type: str = "Swing"  # Scalping, Intraday, Swing, Positional, Long-Term
    min_holding_period_days: Optional[int] = None  # Minimum days to hold position
    max_holding_period_days: Optional[int] = None  # Maximum days to hold position
    force_exit_at_end: bool = True  # Force exit all positions at end date
    risk_reward_ratio: Optional[float] = None  # Risk:Reward ratio (e.g., 2.0 means risk $1 to make $2)
    # Macro regime position sizing (5-Trench model)
    use_macro_regime: bool = False  # Enable macro-based position sizing
    macro_base_pct: float = 0.04  # Base position % (Trench 1)
    macro_max_pct: float = 0.15  # Maximum position cap
    macro_classification: float = 1.0  # CORE=1.2, SATELLITE=0.8 (Trench 4)
    macro_persona: float = 1.0  # Aggression level 0.7-1.2 (Trench 5)


@dataclass
class BacktestResult:
    """Backtesting results"""
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    average_win: float
    average_loss: float
    total_pnl: float  # Total Profit & Loss in dollars
    total_pnl_percent: float  # Total Profit & Loss as percentage of total capital
    total_pnl_percent_deployed: float  # Total P&L as percentage of deployed capital
    total_capital_deployed: float  # Total capital actually deployed in trades
    equity_curve: pd.Series
    drawdown_curve: pd.Series
    trades: List[Dict]


class BacktestEngine:
    """Backtesting engine for strategy validation"""
    
    def __init__(self, config: BacktestConfig = None):
        """
        Initialize backtesting engine
        
        Args:
            config: Backtesting configuration
        """
        self.config = config or BacktestConfig()
        self.positions = {}  # symbol -> quantity
        self.position_entry_dates = {}  # symbol -> entry date (for holding period tracking)
        self.position_entry_costs = {}  # symbol -> total cost basis (for average entry price calculation)
        self.cash = self.config.initial_capital
        self.equity_history = []
        self.trades = []
        self.position_sizing_breakdowns = []  # Track 5-Trench breakdowns
        self._historical_data = None  # Store historical data for macro regime detection
        
        # Initialize macro regime detector if enabled
        self.macro_regime_detector = None
        self.five_trench_sizer = None
        if self.config.use_macro_regime:
            try:
                from .macro_regime import MacroRegimeDetector, FiveTrenchPositionSizer
                self.macro_regime_detector = MacroRegimeDetector(use_real_macro=True)
                self.five_trench_sizer = FiveTrenchPositionSizer(
                    base_pct=self.config.macro_base_pct,
                    max_position_pct=self.config.macro_max_pct,
                    macro_regime_detector=self.macro_regime_detector
                )
            except ImportError:
                # Fallback if macro_regime module not available
                self.config.use_macro_regime = False
        
        # Apply portfolio type defaults if not explicitly set
        if self.config.min_holding_period_days is None or self.config.max_holding_period_days is None:
            portfolio_type_config = self._get_portfolio_type_config(self.config.portfolio_type)
            if self.config.min_holding_period_days is None:
                self.config.min_holding_period_days = portfolio_type_config.get('min_holding_days', 0)
            if self.config.max_holding_period_days is None:
                self.config.max_holding_period_days = portfolio_type_config.get('max_holding_days', None)
    
    @staticmethod
    def _get_portfolio_type_config(portfolio_type: str) -> Dict:
        """Get configuration for portfolio type with institutional risk:reward ratios"""
        # Normalize portfolio type name
        portfolio_type_normalized = portfolio_type.replace(" ", "-").replace("_", "-")
        if portfolio_type_normalized == "Long-term":
            portfolio_type_normalized = "Long-Term"
        
        configs = {
            "Scalping": {
                "min_holding_days": 0,  # Can exit immediately
                "max_holding_days": 1,  # Must exit same day
                "commission_multiplier": 1.5,  # Higher commission for frequent trading
                "slippage_multiplier": 2.0,  # Higher slippage for quick execution
                "description": "Very short-term trades (minutes to hours), high frequency",
                "time_horizon": "Seconds–Minutes",
                "typical_win_rate": (60, 80),  # Range: 60-80%
                "risk_reward_min": 0.3,  # Minimum risk:reward ratio
                "risk_reward_max": 0.8,  # Maximum risk:reward ratio
                "risk_reward_default": 0.5,  # Default risk:reward ratio
                "institutional_logic": "Micro-edge, high turnover"
            },
            "Intraday": {
                "min_holding_days": 0,
                "max_holding_days": 1,  # Must exit same day
                "commission_multiplier": 1.2,
                "slippage_multiplier": 1.5,
                "description": "Day trading, same-day entry and exit",
                "time_horizon": "Minutes–Hours",
                "typical_win_rate": (45, 60),  # Range: 45-60%
                "risk_reward_min": 0.8,
                "risk_reward_max": 1.5,
                "risk_reward_default": 1.0,
                "institutional_logic": "Volatility harvesting"
            },
            "Swing": {
                "min_holding_days": 1,
                "max_holding_days": 14,  # 2 weeks max
                "commission_multiplier": 1.0,
                "slippage_multiplier": 1.0,
                "description": "Days to weeks holding period",
                "time_horizon": "Days–Weeks",
                "typical_win_rate": (40, 55),  # Range: 40-55%
                "risk_reward_min": 1.5,
                "risk_reward_max": 3.0,
                "risk_reward_default": 2.0,
                "institutional_logic": "Core alpha engine"
            },
            "Positional": {
                "min_holding_days": 7,
                "max_holding_days": 90,  # 3 months max
                "commission_multiplier": 0.8,  # Lower commission for longer holds
                "slippage_multiplier": 0.8,
                "description": "Weeks to months holding period",
                "time_horizon": "Weeks–Months",
                "typical_win_rate": (30, 45),  # Range: 30-45%
                "risk_reward_min": 2.5,
                "risk_reward_max": 5.0,
                "risk_reward_default": 3.5,
                "institutional_logic": "Trend persistence"
            },
            "Long-Term": {
                "min_holding_days": 30,
                "max_holding_days": None,  # No max limit
                "commission_multiplier": 0.5,
                "slippage_multiplier": 0.5,
                "description": "Months to years holding period",
                "time_horizon": "Months–Years",
                "typical_win_rate": (20, 35),  # Range: 20-35%
                "risk_reward_min": 3.0,  # Updated: Lower minimum for better profit capture
                "risk_reward_max": 4.0,  # Updated: Lower maximum for more realistic targets
                "risk_reward_default": 3.5,  # Updated: More balanced default
                "institutional_logic": "Convex payoff, beta + alpha"
            },
            # Legacy support for "Long term" (without hyphen)
            "Long term": {
                "min_holding_days": 30,
                "max_holding_days": None,
                "commission_multiplier": 0.5,
                "slippage_multiplier": 0.5,
                "description": "Months to years holding period",
                "time_horizon": "Months–Years",
                "typical_win_rate": (20, 35),
                "risk_reward_min": 3.0,  # Updated: Lower minimum for better profit capture
                "risk_reward_max": 4.0,  # Updated: Lower maximum for more realistic targets
                "risk_reward_default": 3.5,  # Updated: More balanced default
                "institutional_logic": "Convex payoff, beta + alpha"
            }
        }
        return configs.get(portfolio_type_normalized, configs.get(portfolio_type, configs["Swing"]))
    
    @staticmethod
    def _normalize_datetime(dt):
        """Normalize datetime to timezone-naive pandas Timestamp"""
        try:
            ts = pd.Timestamp(dt)
            if hasattr(ts, 'tz') and ts.tz is not None:
                ts = ts.tz_localize(None)
            return ts.normalize()
        except Exception:
            try:
                return pd.Timestamp(dt).normalize()
            except:
                return pd.Timestamp(dt)
    
    def run(self, strategy: StrategyBase, data: Dict[str, pd.DataFrame]) -> BacktestResult:
        # Store historical data reference for ATR calculation
        self._historical_data = data
        """
        Run backtest on a strategy
        
        Args:
            strategy: Trading strategy instance
            data: Dictionary of symbol -> historical data (OHLCV)
            
        Returns:
            BacktestResult with performance metrics
        """
        # Store strategy for use in _process_signal
        self.strategy = strategy
        
        # Reset state
        self.positions = {}
        self.cash = self.config.initial_capital
        self.equity_history = []
        self.trades = []
        
        # Normalize all dates to timezone-naive pandas Timestamps for consistent comparison
        # First, normalize config dates to pandas Timestamps
        start_date = None
        end_date = None
        
        if self.config.start_date:
            start_date = BacktestEngine._normalize_datetime(self.config.start_date)
        
        if self.config.end_date:
            end_date = BacktestEngine._normalize_datetime(self.config.end_date)
        
        # Normalize DataFrame dates ONCE and collect all dates
        all_dates = set()
        for symbol, df in data.items():
            # Normalize DataFrame index to timezone-naive - do this once
            try:
                # Convert to DatetimeIndex if not already
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index)
                
                # Remove timezone if present
                if df.index.tz is not None:
                    df.index = df.index.tz_localize(None)
                
                # Normalize to midnight
                df.index = df.index.normalize()
                
            except (TypeError, AttributeError, ValueError) as e:
                # Fallback: try basic conversion
                try:
                    df.index = pd.to_datetime(df.index)
                    if isinstance(df.index, pd.DatetimeIndex):
                        if df.index.tz is not None:
                            df.index = df.index.tz_localize(None)
                        df.index = df.index.normalize()
                except Exception as e2:
                    # If all else fails, try to continue
                    pass
            
            # Collect normalized dates - ensure they're Timestamps
            for d in df.index:
                normalized_d = BacktestEngine._normalize_datetime(d)
                all_dates.add(normalized_d)
        
        # Sort dates (they're already normalized)
        dates = sorted(all_dates)
        
        # Filter dates by start/end using normalized comparisons
        # Ensure all dates are pandas Timestamps for comparison
        if start_date:
            dates = [d for d in dates if BacktestEngine._normalize_datetime(d) >= start_date]
        if end_date:
            dates = [d for d in dates if BacktestEngine._normalize_datetime(d) <= end_date]
        
        # Run simulation day by day
        for date in dates:
            # Ensure date is a normalized Timestamp (already normalized, but ensure type consistency)
            date_ts = BacktestEngine._normalize_datetime(date)
            
            # Get current market data for all symbols
            current_data = {}
            for symbol, df in data.items():
                # DataFrame index is already normalized, but ensure comparison works
                # Normalize index dates for comparison
                try:
                    df_index_normalized = pd.Series([BacktestEngine._normalize_datetime(d) for d in df.index], index=df.index)
                    matching_idx = df_index_normalized[df_index_normalized == date_ts]
                    if len(matching_idx) > 0:
                        original_idx = matching_idx.index[0]
                        current_data[symbol] = df.loc[original_idx]
                except:
                    # Fallback: try direct lookup
                    try:
                        if date_ts in df.index:
                            current_data[symbol] = df.loc[date_ts]
                    except:
                        pass
            
            if not current_data:
                continue
            
            # Generate signals - use data up to current date
            # For single symbol, pass the DataFrame directly (index already normalized)
            if len(data) == 1:
                symbol = list(data.keys())[0]
                df = data[symbol]
                # Get data up to and including current date
                # Normalize index for comparison
                try:
                    normalized_indices = [BacktestEngine._normalize_datetime(d) for d in df.index]
                    mask = pd.Series(normalized_indices, index=df.index) <= date_ts
                    if mask.any():
                        signal_data = df.loc[mask]
                        # For Inventory-Aware Trench Strategy, update position percentage BEFORE generating signals
                        portfolio_value = self._calculate_portfolio_value(current_data)
                        if hasattr(strategy, 'inventory') and hasattr(strategy, 'max_position_pct'):
                            # Update current position percentage and average entry price in strategy inventory
                            if symbol in strategy.inventory:
                                current_position_qty = self.positions.get(symbol, 0)
                                current_price = current_data.get(symbol, {}).get('Close', current_data.get(symbol, {}).get('close', 0))
                                if current_price > 0:
                                    current_position_value = current_position_qty * current_price
                                    current_position_pct = (current_position_value / portfolio_value) if portfolio_value > 0 else 0
                                    strategy.inventory[symbol]['current_position_value'] = current_position_value
                                    strategy.inventory[symbol]['current_position_pct'] = current_position_pct
                                    
                                    # Update average entry price for profit calculation
                                    if symbol in self.position_entry_costs and current_position_qty > 0:
                                        total_cost = self.position_entry_costs[symbol]
                                        avg_entry_price = total_cost / current_position_qty
                                        strategy.inventory[symbol]['avg_entry_price'] = avg_entry_price
                                    elif 'avg_entry_price' not in strategy.inventory[symbol]:
                                        # Fallback to current price if no entry cost tracked
                                        strategy.inventory[symbol]['avg_entry_price'] = current_price
                            
                            # Calculate macro regime target_position BEFORE generating signals
                            # This ensures the strategy knows how many trenches to deploy
                            if self.config.use_macro_regime and self.five_trench_sizer and self._historical_data:
                                try:
                                    # Get historical data up to current date
                                    symbol_data = None
                                    if symbol in self._historical_data:
                                        symbol_data = self._historical_data[symbol].copy()
                                        if isinstance(symbol_data.index, pd.DatetimeIndex):
                                            symbol_data = symbol_data[symbol_data.index <= date_ts]
                                    
                                    if symbol_data is not None and len(symbol_data) > 30:
                                        # Ensure column names are lowercase
                                        symbol_data_fixed = symbol_data.copy()
                                        if 'Close' in symbol_data_fixed.columns and 'close' not in symbol_data_fixed.columns:
                                            symbol_data_fixed = symbol_data_fixed.rename(columns={
                                                'Close': 'close', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Volume': 'volume'
                                            })
                                        
                                        # Calculate macro regime to get multipliers
                                        _, breakdown = self.five_trench_sizer.calculate_position_size(
                                            portfolio_value=portfolio_value,
                                            price=current_price if current_price > 0 else signal_data['close'].iloc[-1],
                                            data=symbol_data_fixed,
                                            classification_multiplier=self.config.macro_classification,
                                            persona_multiplier=self.config.macro_persona,
                                            current_date=date_ts
                                        )
                                        
                                        # Calculate target number of trenches based on macro regime
                                        regime_multiplier = breakdown.get('regime_multiplier', 1.0)
                                        volatility_multiplier = breakdown.get('volatility_multiplier', 1.0)
                                        classification_multiplier = breakdown.get('classification_multiplier', 1.0)
                                        persona_multiplier = breakdown.get('persona_multiplier', 1.0)
                                        
                                        standard_trench_size = strategy.max_position_pct / strategy.trench_levels
                                        standard_total_size = strategy.max_position_pct
                                        
                                        combined_multiplier = volatility_multiplier * regime_multiplier * classification_multiplier * persona_multiplier
                                        
                                        # IMPORTANT: Scale standard sizing by macro multipliers
                                        # Standard is 15% total (5% per trench × 3 trenches)
                                        # Macro adjusts this: 15% × combined_multiplier
                                        macro_adjusted_total = standard_total_size * combined_multiplier
                                        
                                        # Ensure macro target is reasonable (not too small, not too large)
                                        macro_adjusted_total = max(standard_total_size * 0.3, min(macro_adjusted_total, strategy.max_position_pct))
                                        
                                        # Determine minimum trenches based on regime
                                        # Even in risk-off, deploy at least 2 trenches for incremental scaling
                                        if regime_multiplier < 0.5:  # Severe risk-off
                                            min_trenches = 1  # Very conservative
                                        elif regime_multiplier < 0.7:  # Moderate risk-off
                                            min_trenches = 2  # Deploy at least 2 trenches
                                        else:  # Neutral or risk-on
                                            min_trenches = 2  # Deploy at least 2 trenches
                                        
                                        # Calculate how many trenches to deploy based on macro-adjusted total
                                        num_trenches_target = max(min_trenches, int(np.ceil(macro_adjusted_total / standard_trench_size)))
                                        num_trenches_target = min(num_trenches_target, strategy.trench_levels)
                                        
                                        # Recalculate macro_adjusted_total to ensure it supports target trenches
                                        # This ensures we deploy multiple trenches even if multiplier is low
                                        macro_adjusted_total = max(
                                            standard_trench_size * num_trenches_target,  # At least enough for target trenches
                                            min(macro_adjusted_total, strategy.max_position_pct)  # But cap at max
                                        )
                                        
                                        # Set target_position in strategy inventory BEFORE generating signals
                                        # Mark it as macro-regime set so strategy respects it
                                        if symbol in strategy.inventory:
                                            strategy.inventory[symbol]['target_position'] = num_trenches_target
                                            strategy.inventory[symbol]['_macro_regime_target'] = True  # Flag to indicate macro regime set this
                                            # Store regime multiplier for structural change detection
                                            strategy.inventory[symbol]['regime_multiplier'] = regime_multiplier
                                except Exception as e:
                                    # If macro regime calculation fails, let strategy use its default logic
                                    pass
                            
                            signals = strategy.generate_signals(signal_data, portfolio_value=portfolio_value)
                        else:
                            signals = strategy.generate_signals(signal_data)
                    else:
                        signals = []
                except Exception as e:
                    # Fallback: try with already-normalized index
                    try:
                        mask = df.index <= date_ts
                        if mask.any():
                            signal_data = df.loc[mask]
                            portfolio_value = self._calculate_portfolio_value(current_data)
                            if hasattr(strategy, 'inventory') and hasattr(strategy, 'max_position_pct'):
                                # Update current position percentage in strategy inventory
                                if symbol in strategy.inventory:
                                    current_position_qty = self.positions.get(symbol, 0)
                                    current_price = current_data.get(symbol, {}).get('Close', current_data.get(symbol, {}).get('close', 0))
                                    if current_price > 0:
                                        current_position_value = current_position_qty * current_price
                                        current_position_pct = (current_position_value / portfolio_value) if portfolio_value > 0 else 0
                                        strategy.inventory[symbol]['current_position_value'] = current_position_value
                                        strategy.inventory[symbol]['current_position_pct'] = current_position_pct
                                
                                # Calculate macro regime target_position BEFORE generating signals (same logic as above)
                                if self.config.use_macro_regime and self.five_trench_sizer and self._historical_data:
                                    try:
                                        symbol_data = None
                                        if symbol in self._historical_data:
                                            symbol_data = self._historical_data[symbol].copy()
                                            if isinstance(symbol_data.index, pd.DatetimeIndex):
                                                symbol_data = symbol_data[symbol_data.index <= date_ts]
                                        
                                        if symbol_data is not None and len(symbol_data) > 30:
                                            symbol_data_fixed = symbol_data.copy()
                                            if 'Close' in symbol_data_fixed.columns and 'close' not in symbol_data_fixed.columns:
                                                symbol_data_fixed = symbol_data_fixed.rename(columns={
                                                    'Close': 'close', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Volume': 'volume'
                                                })
                                            
                                            _, breakdown = self.five_trench_sizer.calculate_position_size(
                                                portfolio_value=portfolio_value,
                                                price=current_price if current_price > 0 else signal_data['close'].iloc[-1],
                                                data=symbol_data_fixed,
                                                classification_multiplier=self.config.macro_classification,
                                                persona_multiplier=self.config.macro_persona,
                                                current_date=date_ts
                                            )
                                            
                                            regime_multiplier = breakdown.get('regime_multiplier', 1.0)
                                            volatility_multiplier = breakdown.get('volatility_multiplier', 1.0)
                                            classification_multiplier = breakdown.get('classification_multiplier', 1.0)
                                            persona_multiplier = breakdown.get('persona_multiplier', 1.0)
                                            
                                            standard_trench_size = strategy.max_position_pct / strategy.trench_levels
                                            standard_total_size = strategy.max_position_pct
                                            
                                            combined_multiplier = volatility_multiplier * regime_multiplier * classification_multiplier * persona_multiplier
                                            macro_adjusted_total = standard_total_size * combined_multiplier
                                            
                                            if regime_multiplier < 0.5:
                                                min_trenches = 1
                                            elif regime_multiplier < 0.7:
                                                min_trenches = 2
                                            else:
                                                min_trenches = 2
                                            
                                            num_trenches_target = max(min_trenches, int(np.ceil(macro_adjusted_total / standard_trench_size)))
                                            num_trenches_target = min(num_trenches_target, strategy.trench_levels)
                                            
                                            if symbol in strategy.inventory:
                                                strategy.inventory[symbol]['target_position'] = num_trenches_target
                                                strategy.inventory[symbol]['_macro_regime_target'] = True  # Flag to indicate macro regime set this
                                    except Exception as e:
                                        pass
                                
                                signals = strategy.generate_signals(signal_data, portfolio_value=portfolio_value)
                            else:
                                signals = strategy.generate_signals(signal_data)
                        else:
                            signals = []
                    except:
                        signals = []
            else:
                # Multiple symbols - create combined DataFrame
                signal_data = {}
                for symbol, df in data.items():
                    # Normalize index for comparison
                    try:
                        normalized_indices = [BacktestEngine._normalize_datetime(d) for d in df.index]
                        mask = pd.Series(normalized_indices, index=df.index) <= date_ts
                        if mask.any():
                            signal_data[symbol] = df.loc[mask]
                    except:
                        try:
                            mask = df.index <= date_ts
                            if mask.any():
                                signal_data[symbol] = df.loc[mask]
                        except:
                            pass
                
                if signal_data:
                    signals = strategy.generate_signals(pd.DataFrame(signal_data))
                else:
                    signals = []
            
            # FIRST: Check for stop loss and take profit hits BEFORE processing new signals
            # This ensures we exit positions before entering new ones
            for symbol in list(self.positions.keys()):
                if symbol in current_data:
                    market_data = current_data[symbol]
                    current_price = market_data.get('Close', market_data.get('close', 0))
                    if current_price > 0:
                        # Find the original buy trade to get stop_loss and take_profit
                        buy_trade = None
                        for trade in reversed(self.trades):
                            if trade['symbol'] == symbol and trade['action'] == 'BUY':
                                buy_trade = trade
                                break
                        
                        if buy_trade:
                            stop_loss = buy_trade.get('stop_loss')
                            take_profit = buy_trade.get('take_profit')
                            risk_reward_ratio = buy_trade.get('risk_reward_ratio', 2.0)
                            
                            # Check stop loss
                            if stop_loss and current_price <= stop_loss:
                                quantity = self.positions[symbol]
                                proceeds = self._execute_trade(symbol, quantity, current_price, 'SELL', date)
                                if proceeds:
                                    self.positions[symbol] = 0
                                    del self.positions[symbol]
                                    if symbol in self.position_entry_dates:
                                        del self.position_entry_dates[symbol]
                                    self.trades.append({
                                        'date': date,
                                        'symbol': symbol,
                                        'action': 'SELL',
                                        'quantity': quantity,
                                        'price': current_price,
                                        'proceeds': proceeds,
                                        'reason': f"Stop Loss Hit ({risk_reward_ratio:.1f}:1 R:R) at ${stop_loss:.2f}"
                                    })
                                    continue  # Skip to next symbol
                            
                            # Check take profit - BUT respect institutional profit-taking rules
                            # For trench strategies: DISABLE automatic take-profit - let strategy handle via structural changes
                            # For other strategies: Use standard take-profit logic
                            is_trench_strategy = (hasattr(strategy, 'inventory') and 
                                                 hasattr(strategy, 'trench_levels') and
                                                 'Trench' in strategy.name)
                            
                            if take_profit and current_price >= take_profit:
                                # For trench strategies: DO NOT auto-take-profit
                                # Let the strategy's generate_signals handle exits based on structural changes
                                # This ensures we only exit when there's a structural change AND profit >= 20%
                                if is_trench_strategy:
                                    # Skip automatic take-profit - strategy will handle via signal generation
                                    pass  # Don't auto-close, let strategy decide
                                else:
                                    # Non-trench strategy: Use standard take-profit logic
                                    quantity = self.positions[symbol]
                                    proceeds = self._execute_trade(symbol, quantity, current_price, 'SELL', date)
                                    if proceeds:
                                        self.positions[symbol] = 0
                                        del self.positions[symbol]
                                        if symbol in self.position_entry_dates:
                                            del self.position_entry_dates[symbol]
                                        self.trades.append({
                                            'date': date,
                                            'symbol': symbol,
                                            'action': 'SELL',
                                            'quantity': quantity,
                                            'price': current_price,
                                            'proceeds': proceeds,
                                            'reason': f"Take Profit Hit ({risk_reward_ratio:.1f}:1 R:R) at ${take_profit:.2f}"
                                        })
                                        continue  # Skip to next symbol
            
            # SECOND: Process signals - deduplicate by symbol and action to prevent multiple trades per day
            # Track processed signals for this date to avoid duplicates
            processed_signals = {}  # (symbol, action) -> signal
            
            for signal in signals:
                if signal.symbol not in current_data:
                    continue
                
                # Create key for deduplication
                signal_key = (signal.symbol, signal.action)
                
                # Only process the first signal of each type per day
                # Prefer stronger signals if multiple exist
                if signal_key not in processed_signals:
                    processed_signals[signal_key] = signal
                elif signal.strength > processed_signals[signal_key].strength:
                    # Replace with stronger signal
                    processed_signals[signal_key] = signal
            
            # Process deduplicated signals
            for signal in processed_signals.values():
                self._process_signal(signal, current_data[signal.symbol], date)
            
            # THIRD: Check for forced exits due to max holding period
            for symbol in list(self.positions.keys()):
                can_exit, reason_msg = self._check_holding_period(symbol, date)
                if reason_msg and "forced exit" in reason_msg.lower():
                    # Force exit due to max holding period
                    if symbol in current_data:
                        market_data = current_data[symbol]
                        current_price = market_data.get('Close', market_data.get('close', 0))
                        if current_price > 0:
                            quantity = self.positions[symbol]
                            proceeds = self._execute_trade(symbol, quantity, current_price, 'SELL', date)
                            if proceeds:
                                self.positions[symbol] = 0
                                del self.positions[symbol]
                                if symbol in self.position_entry_dates:
                                    del self.position_entry_dates[symbol]
                                if symbol in self.position_entry_costs:
                                    del self.position_entry_costs[symbol]
                                self.trades.append({
                                    'date': date,
                                    'symbol': symbol,
                                    'action': 'SELL',
                                    'quantity': quantity,
                                    'price': current_price,
                                    'proceeds': proceeds,
                                    'reason': reason_msg
                                })
            
            # Update equity
            portfolio_value = self._calculate_portfolio_value(current_data)
            self.equity_history.append({
                'date': date,
                'equity': portfolio_value,
                'cash': self.cash,
                'positions_value': portfolio_value - self.cash
            })
        
        # Force exit all positions at end date if configured
        if self.config.force_exit_at_end and self.positions:
            last_date = dates[-1] if dates else date
            for symbol in list(self.positions.keys()):
                if symbol in data and len(data[symbol]) > 0:
                    last_row = data[symbol].iloc[-1]
                    current_price = last_row.get('Close', last_row.get('close', 0))
                    if current_price > 0:
                        quantity = self.positions[symbol]
                        proceeds = self._execute_trade(symbol, quantity, current_price, 'SELL', last_date)
                        if proceeds:
                            self.positions[symbol] = 0
                            del self.positions[symbol]
                            if symbol in self.position_entry_dates:
                                del self.position_entry_dates[symbol]
                            self.trades.append({
                                'date': last_date,
                                'symbol': symbol,
                                'action': 'SELL',
                                'quantity': quantity,
                                'price': current_price,
                                'proceeds': proceeds,
                                'reason': f"End of backtest - forced exit ({self.config.portfolio_type} portfolio)"
                            })
        
        # Calculate results
        return self._calculate_results()
    
    def _calculate_atr_for_symbol(self, symbol: str, current_price: float, data: Dict[str, pd.DataFrame] = None) -> float:
        """Calculate ATR for a symbol"""
        if data and symbol in data:
            try:
                df = data[symbol]
                if len(df) >= 14:
                    high = df['high'] if 'high' in df.columns else df['High']
                    low = df['low'] if 'low' in df.columns else df['Low']
                    close = df['close'] if 'close' in df.columns else df['Close']
                    
                    # Calculate True Range
                    tr1 = high - low
                    tr2 = abs(high - close.shift())
                    tr3 = abs(low - close.shift())
                    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                    
                    # Calculate ATR (14-period)
                    atr = tr.rolling(window=14).mean().iloc[-1]
                    if not pd.isna(atr) and atr > 0:
                        return float(atr)
            except:
                pass
        
        # Fallback: use 2% of price as ATR estimate
        return current_price * 0.02
    
    def _check_holding_period(self, symbol: str, current_date: datetime) -> Tuple[bool, Optional[str]]:
        """Check if position can be exited based on holding period constraints"""
        if symbol not in self.position_entry_dates:
            return True, None  # No position, can trade
        
        entry_date = self.position_entry_dates[symbol]
        days_held = (current_date - entry_date).days
        
        # Check minimum holding period
        if self.config.min_holding_period_days is not None and days_held < self.config.min_holding_period_days:
            return False, f"Minimum holding period not met: {days_held} < {self.config.min_holding_period_days} days"
        
        # Check maximum holding period
        if self.config.max_holding_period_days is not None and days_held >= self.config.max_holding_period_days:
            return True, f"Maximum holding period reached: {days_held} >= {self.config.max_holding_period_days} days (forced exit)"
        
        return True, None
    
    def _calculate_standard_position_size(self, signal: Signal, portfolio_value: float, market_data: pd.Series) -> int:
        """Calculate position size using standard method (non-macro regime)"""
        # Use 5-10% position sizing instead of default 2%
        # Adjust based on portfolio type: more aggressive for longer-term strategies
        portfolio_config = self._get_portfolio_type_config(self.config.portfolio_type)
        if self.config.portfolio_type in ["Long-Term", "Long term", "Positional"]:
            target_position_pct = 0.10  # 10% for long-term strategies
        elif self.config.portfolio_type == "Swing":
            target_position_pct = 0.075  # 7.5% for swing trading
        elif self.config.portfolio_type == "Intraday":
            target_position_pct = 0.06  # 6% for intraday
        else:  # Scalping
            target_position_pct = 0.05  # 5% for scalping (more conservative due to higher frequency)
        
        # For InventoryAwareTrenchStrategy, use standard trench size calculation
        # Standard sizing: each trench is max_position_pct / trench_levels
        # This ensures consistent behavior without macro regime
        if hasattr(self.strategy, 'trench_levels') and hasattr(self.strategy, 'max_position_pct'):
            # Standard trench size: divide max position equally across trenches
            standard_trench_size = self.strategy.max_position_pct / self.strategy.trench_levels
            # Use this as risk_per_trade so strategy uses standard trench sizing
            risk_per_trade = standard_trench_size
        elif hasattr(self.strategy, 'base_position_pct'):
            # Strategy multiplies by base_position_pct, so we need to divide target by it
            base_pct = getattr(self.strategy, 'base_position_pct', 1.0)
            if base_pct > 0:
                risk_per_trade = target_position_pct / base_pct
            else:
                risk_per_trade = target_position_pct
        else:
            # Strategy doesn't have multiplier, use target directly
            risk_per_trade = target_position_pct
        
        return self.strategy.calculate_position_size(signal, portfolio_value, risk_per_trade=risk_per_trade)
    
    def _process_signal(self, signal: Signal, market_data: pd.Series, date: datetime):
        """Process a trading signal"""
        if not self.strategy.validate_signal(signal):
            return
        
        current_price = market_data.get('Close', market_data.get('close', 0))
        if current_price == 0:
            return
        
        current_position = self.positions.get(signal.symbol, 0)
        
        # For Inventory-Aware Trench Strategy, inventory sync happens naturally
        # The strategy tracks trench deployment count separately from engine positions
        # This allows incremental scaling into positions (multiple trenches)
        # No need to override here - strategy manages its own inventory state
        
        # For Inventory-Aware Trench Strategy, allow scaling into positions (adding trenches)
        # Check if this is a trench strategy that supports incremental position building
        is_trench_strategy = (hasattr(self.strategy, 'inventory') and 
                             hasattr(self.strategy, 'trench_levels') and
                             'Trench' in self.strategy.name)
        
        # Allow BUY signals if:
        # 1. Standard: No position (current_position == 0), OR
        # 2. Trench strategy: Can add to existing long position (scaling in)
        allow_buy = (signal.action == 'BUY' and 
                    (current_position == 0 or (is_trench_strategy and current_position >= 0)))
        
        if allow_buy:
            # Calculate position size
            portfolio_value = self._calculate_portfolio_value({signal.symbol: market_data})
            
                    # Use 5-Trench macro regime model if enabled
            if self.config.use_macro_regime and self.five_trench_sizer and self._historical_data:
                try:
                    current_price = market_data.get('Close', market_data.get('close', signal.price))
                    
                    # Get historical data for the symbol up to current date
                    symbol_data = None
                    if signal.symbol in self._historical_data:
                        symbol_data = self._historical_data[signal.symbol].copy()
                        # Filter data up to current date
                        if isinstance(symbol_data.index, pd.DatetimeIndex):
                            symbol_data = symbol_data[symbol_data.index <= date]
                    else:
                        # Debug: symbol not in historical data
                        import warnings
                        warnings.warn(f"Symbol {signal.symbol} not found in _historical_data. Available: {list(self._historical_data.keys())}")
                    
                    # If we have historical data, use it; otherwise fallback
                    if symbol_data is not None and len(symbol_data) > 30:
                        # Use 5-Trench model with real historical data
                        # Ensure column names are lowercase for macro regime
                        symbol_data_fixed = symbol_data.copy()
                        if 'Close' in symbol_data_fixed.columns and 'close' not in symbol_data_fixed.columns:
                            symbol_data_fixed = symbol_data_fixed.rename(columns={
                                'Close': 'close', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Volume': 'volume'
                            })
                        
                        # Calculate macro regime position size
                        macro_quantity, breakdown = self.five_trench_sizer.calculate_position_size(
                            portfolio_value=portfolio_value,
                            price=current_price,
                            data=symbol_data_fixed,
                            classification_multiplier=self.config.macro_classification,
                            persona_multiplier=self.config.macro_persona,
                            current_date=date
                        )
                        
                        # For InventoryAwareTrenchStrategy, we need to adapt macro regime sizing
                        # The strategy deploys trenches incrementally, so we need to convert macro regime
                        # final position % into a risk_per_trade that the strategy can use
                        if hasattr(self.strategy, 'inventory') and hasattr(self.strategy, 'trench_levels'):
                            # Strategy uses incremental trench deployment
                            # For trench strategies, use macro regime multipliers to adjust STANDARD trench sizing
                            # rather than using the absolute final_pct (which is designed for single positions)
                            
                            # Standard trench sizing: 5% per trench × 3 trenches = 15% total
                            standard_trench_size = self.strategy.max_position_pct / self.strategy.trench_levels  # 5%
                            standard_total_size = self.strategy.max_position_pct  # 15% total
                            
                            # Extract multipliers from breakdown
                            regime_multiplier = breakdown.get('regime_multiplier', 1.0)
                            volatility_multiplier = breakdown.get('volatility_multiplier', 1.0)
                            classification_multiplier = breakdown.get('classification_multiplier', 1.0)
                            persona_multiplier = breakdown.get('persona_multiplier', 1.0)
                            
                            # Store original regime multiplier for display
                            original_regime_multiplier = regime_multiplier
                            
                            # Apply macro regime multipliers to standard trench sizing
                            # Standard sizing: 15% total (5% per trench × 3 trenches)
                            # Macro adjusts this: 15% × (Vol × Regime × Classification × Persona)
                            combined_multiplier = volatility_multiplier * regime_multiplier * classification_multiplier * persona_multiplier
                            
                            # Scale standard total by combined multiplier
                            macro_adjusted_total = standard_total_size * combined_multiplier
                            
                            # Ensure macro target is reasonable (not too small, not too large)
                            macro_adjusted_total = max(standard_total_size * 0.3, min(macro_adjusted_total, self.strategy.max_position_pct))
                            
                            # Determine minimum trenches based on regime
                            # Even in risk-off, deploy at least 2 trenches for incremental scaling (unless severe)
                            if regime_multiplier < 0.5:  # Severe risk-off
                                min_trenches = 1  # Very conservative: only 1 trench
                            elif regime_multiplier < 0.7:  # Moderate risk-off
                                min_trenches = 2  # Deploy at least 2 trenches
                            else:  # Neutral or risk-on
                                min_trenches = 2  # Deploy at least 2 trenches
                            
                            # Calculate target number of trenches based on macro-adjusted total
                            num_trenches_target = max(min_trenches, int(np.ceil(macro_adjusted_total / standard_trench_size)))
                            num_trenches_target = min(num_trenches_target, self.strategy.trench_levels)
                            
                            # Recalculate macro_adjusted_total to ensure it supports target trenches
                            # This ensures we deploy multiple trenches even if multiplier is low
                            macro_adjusted_total = max(
                                standard_trench_size * num_trenches_target,  # At least enough for target trenches
                                min(macro_adjusted_total, self.strategy.max_position_pct)  # But cap at max
                            )
                            
                            # Per-trench size: divide adjusted total by number of trenches
                            per_trench_pct = macro_adjusted_total / num_trenches_target if num_trenches_target > 0 else macro_adjusted_total
                            
                            # Ensure per-trench size doesn't exceed max_position_pct when all trenches deployed
                            max_per_trench_allowed = self.strategy.max_position_pct / num_trenches_target
                            per_trench_pct = min(per_trench_pct, max_per_trench_allowed)
                            
                            # Update breakdown to show adjusted values
                            breakdown['macro_adjusted_total'] = macro_adjusted_total
                            breakdown['combined_multiplier'] = combined_multiplier
                            # IMPORTANT: Keep the original regime multiplier for display (shows what regime was detected)
                            breakdown['regime_multiplier'] = original_regime_multiplier
                            breakdown['regime_at_deployment'] = original_regime_multiplier  # Also store for deployment tracking
                            
                            # Store regime multiplier in strategy inventory for structural change detection
                            if signal.symbol in self.strategy.inventory:
                                self.strategy.inventory[signal.symbol]['regime_multiplier'] = original_regime_multiplier
                            
                            macro_final_pct = macro_adjusted_total  # Use adjusted total for tracking
                            
                            # IMPORTANT: Set target_position in strategy inventory to ensure it deploys the calculated number of trenches
                            # The strategy uses target_position to determine how many trenches to deploy
                            if signal.symbol in self.strategy.inventory:
                                # Update target_position to match our calculated num_trenches_target
                                # This ensures the strategy generates enough signals to deploy all calculated trenches
                                self.strategy.inventory[signal.symbol]['target_position'] = num_trenches_target
                            
                            # Use strategy's own calculate_position_size with macro-adjusted risk_per_trade
                            # Strategy will use this as trench_size_pct when risk_per_trade is in reasonable range
                            # The strategy will enforce the total max_position_pct cap per instrument
                            quantity = self.strategy.calculate_position_size(signal, portfolio_value, risk_per_trade=per_trench_pct)
                            
                            # Update breakdown to show we're using macro-adjusted sizing
                            breakdown['macro_adjusted'] = True
                            breakdown['num_trenches_target'] = num_trenches_target
                            breakdown['per_trench_pct'] = per_trench_pct
                            breakdown['strategy_quantity'] = quantity
                            breakdown['total_target_pct'] = macro_final_pct
                            
                            # IMPORTANT: Update final_pct to show the ACTUAL value being used (macro_adjusted_total)
                            # not the raw macro calculation (which is for single positions, not trench strategies)
                            breakdown['final_pct'] = macro_final_pct  # Use the scaled value for trench strategies
                            
                            # Store the regime multiplier used for this specific deployment
                            # This allows tracking regime at time of each trench deployment
                            breakdown['deployment_date'] = date
                            # regime_at_deployment already set above with original_regime_multiplier
                        else:
                            # Non-trench strategy: use macro quantity directly
                            quantity = macro_quantity
                        
                        # Store breakdown for later analysis
                        # Ensure breakdown contains the correct regime multiplier used for this deployment
                        if hasattr(self.strategy, 'inventory') and hasattr(self.strategy, 'trench_levels'):
                            # For trench strategies, the breakdown has been updated with macro_adjusted values
                            # Make sure regime_multiplier reflects what was actually used
                            if 'regime_at_deployment' in breakdown:
                                breakdown['regime_multiplier'] = breakdown['regime_at_deployment']
                        
                        self.position_sizing_breakdowns.append({
                            'date': date,
                            'symbol': signal.symbol,
                            'breakdown': breakdown
                        })
                    else:
                        # Not enough historical data, use standard sizing
                        import warnings
                        warnings.warn(f"Insufficient historical data for macro regime: "
                                   f"symbol={signal.symbol}, date={date}, "
                                   f"data_length={len(symbol_data) if symbol_data is not None else 0}")
                        quantity = self._calculate_standard_position_size(signal, portfolio_value, market_data)
                    
                except Exception as e:
                    # Fallback to standard sizing if macro regime fails
                    import warnings
                    import traceback
                    warnings.warn(f"Macro regime sizing failed, using standard: {e}\n{traceback.format_exc()}")
                    quantity = self._calculate_standard_position_size(signal, portfolio_value, market_data)
            else:
                # Standard position sizing (existing logic)
                quantity = self._calculate_standard_position_size(signal, portfolio_value, market_data)
            
            if quantity > 0:
                cost = self._execute_trade(signal.symbol, quantity, current_price, 'BUY', date)
                if cost:
                    # Update strategy inventory with current position percentage
                    # This allows strategy to know when it's approaching 15% cap
                    if hasattr(self.strategy, 'inventory') and signal.symbol in self.strategy.inventory:
                        portfolio_value = self._calculate_portfolio_value({signal.symbol: market_data})
                        current_position_value = self.positions.get(signal.symbol, 0) * current_price
                        current_position_pct = (current_position_value / portfolio_value) if portfolio_value > 0 else 0
                        self.strategy.inventory[signal.symbol]['current_position_value'] = current_position_value
                        self.strategy.inventory[signal.symbol]['current_position_pct'] = current_position_pct
                    # Calculate stop loss and take profit based on risk:reward ratio
                    risk_reward_ratio = self.config.risk_reward_ratio
                    if risk_reward_ratio is None:
                        # Get default from portfolio type config
                        portfolio_config = self._get_portfolio_type_config(self.config.portfolio_type)
                        risk_reward_ratio = portfolio_config.get('risk_reward_default', 2.0)
                    
                    # Calculate ATR for volatility-based stop loss
                    # Use historical data stored in engine
                    atr = self._calculate_atr_for_symbol(signal.symbol, current_price, getattr(self, '_historical_data', None))
                    stop_loss_distance = atr * 2.0  # 2x ATR for stop loss
                    
                    # Ensure stop loss is reasonable (at least 0.5% of price, max 10%)
                    min_stop_distance = current_price * 0.005
                    max_stop_distance = current_price * 0.10
                    stop_loss_distance = max(min_stop_distance, min(stop_loss_distance, max_stop_distance))
                    
                    stop_loss_price = max(current_price - stop_loss_distance, 0.01)  # Ensure positive
                    take_profit_price = current_price + (stop_loss_distance * risk_reward_ratio)
                    
                    # Update position (add to existing if scaling in)
                    # Calculate average entry price for profit tracking
                    if signal.symbol in self.positions:
                        # Existing position: calculate weighted average entry price
                        old_qty = self.positions[signal.symbol]
                        old_cost = self.position_entry_costs.get(signal.symbol, old_qty * current_price)
                        new_cost = quantity * current_price
                        total_qty = old_qty + quantity
                        avg_entry_price = (old_cost + new_cost) / total_qty if total_qty > 0 else current_price
                        self.positions[signal.symbol] = total_qty
                        self.position_entry_costs[signal.symbol] = old_cost + new_cost
                    else:
                        self.positions[signal.symbol] = quantity
                        self.position_entry_dates[signal.symbol] = date
                        self.position_entry_costs[signal.symbol] = quantity * current_price
                        avg_entry_price = current_price
                    
                    # Update strategy inventory with current position percentage and average entry price
                    # This allows strategy to know when it's approaching 15% cap and calculate profits
                    if hasattr(self.strategy, 'inventory') and signal.symbol in self.strategy.inventory:
                        portfolio_value = self._calculate_portfolio_value({signal.symbol: market_data})
                        current_position_value = self.positions.get(signal.symbol, 0) * current_price
                        current_position_pct = (current_position_value / portfolio_value) if portfolio_value > 0 else 0
                        self.strategy.inventory[signal.symbol]['current_position_value'] = current_position_value
                        self.strategy.inventory[signal.symbol]['current_position_pct'] = current_position_pct
                        self.strategy.inventory[signal.symbol]['avg_entry_price'] = avg_entry_price
                    self.trades.append({
                        'date': date,
                        'symbol': signal.symbol,
                        'action': 'BUY',
                        'quantity': quantity,
                        'price': current_price,
                        'cost': cost,
                        'stop_loss': stop_loss_price,
                        'take_profit': take_profit_price,
                        'risk_reward_ratio': risk_reward_ratio,
                        'reason': signal.reason
                    })
        
        elif signal.action == 'SELL' and current_position > 0:
            # Check holding period constraints
            can_exit, reason_msg = self._check_holding_period(signal.symbol, date)
            
            if not can_exit:
                # Skip exit if minimum holding period not met
                return
            
            # Check if stop loss or take profit was hit
            # Find the original buy trade to get stop_loss and take_profit
            buy_trade = None
            for trade in reversed(self.trades):
                if trade['symbol'] == signal.symbol and trade['action'] == 'BUY':
                    buy_trade = trade
                    break
            
            exit_reason = signal.reason
            if buy_trade:
                stop_loss = buy_trade.get('stop_loss')
                take_profit = buy_trade.get('take_profit')
                risk_reward_ratio = buy_trade.get('risk_reward_ratio', 2.0)
                
                if stop_loss and current_price <= stop_loss:
                    exit_reason = f"Stop Loss Hit ({risk_reward_ratio:.1f}:1 R:R) - {signal.reason}"
                elif take_profit and current_price >= take_profit:
                    # For trench strategies, check if this is a structural change-based exit
                    # If signal.reason contains "structural change", it's from strategy logic
                    if "structural change" in signal.reason.lower():
                        exit_reason = f"Take Profit Hit ({risk_reward_ratio:.1f}:1 R:R) - {signal.reason}"
                    else:
                        # Calculate profit to check if it's very high
                        entry_price = buy_trade.get('price', current_price)
                        profit_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
                        is_trench_strategy = (hasattr(self.strategy, 'inventory') and 
                                             hasattr(self.strategy, 'trench_levels') and
                                             'Trench' in self.strategy.name)
                        
                        if is_trench_strategy and profit_pct < 50.0:
                            # Trench strategy with moderate profit - don't auto-take-profit
                            # Let strategy handle via structural change detection
                            exit_reason = signal.reason  # Use strategy's reason
                        else:
                            exit_reason = f"Take Profit Hit ({risk_reward_ratio:.1f}:1 R:R) - {signal.reason}"
            
            quantity = min(current_position, signal.quantity or current_position)
            proceeds = self._execute_trade(signal.symbol, quantity, current_price, 'SELL', date)
            
            if proceeds:
                self.positions[signal.symbol] -= quantity
                
                # Update entry cost basis (proportional reduction)
                if signal.symbol in self.position_entry_costs:
                    total_cost = self.position_entry_costs[signal.symbol]
                    total_qty = current_position
                    if total_qty > 0:
                        cost_per_share = total_cost / total_qty
                        self.position_entry_costs[signal.symbol] -= cost_per_share * quantity
                        if self.position_entry_costs[signal.symbol] < 0:
                            self.position_entry_costs[signal.symbol] = 0
                
                if self.positions[signal.symbol] == 0:
                    del self.positions[signal.symbol]
                    if signal.symbol in self.position_entry_dates:
                        del self.position_entry_dates[signal.symbol]
                    if signal.symbol in self.position_entry_costs:
                        del self.position_entry_costs[signal.symbol]
                
                # Use reason_msg if forced exit, otherwise use exit_reason
                final_reason = reason_msg if reason_msg else exit_reason
                
                self.trades.append({
                    'date': date,
                    'symbol': signal.symbol,
                    'action': 'SELL',
                    'quantity': quantity,
                    'price': current_price,
                    'proceeds': proceeds,
                    'reason': final_reason
                })
    
    def _execute_trade(self, symbol: str, quantity: int, price: float, 
                      side: str, date: datetime) -> Optional[float]:
        """Execute a trade with commission and slippage"""
        # Apply slippage
        if side == 'BUY':
            execution_price = price * (1 + self.config.slippage)
            cost = execution_price * quantity
            commission = cost * self.config.commission
            total_cost = cost + commission
            
            if total_cost > self.cash:
                return None
            
            self.cash -= total_cost
            return total_cost
        
        else:  # SELL
            execution_price = price * (1 - self.config.slippage)
            proceeds = execution_price * quantity
            commission = proceeds * self.config.commission
            net_proceeds = proceeds - commission
            
            self.cash += net_proceeds
            return net_proceeds
    
    def _calculate_portfolio_value(self, current_data: Dict[str, pd.Series]) -> float:
        """Calculate current portfolio value"""
        positions_value = 0.0
        
        for symbol, quantity in self.positions.items():
            if symbol in current_data:
                price = current_data[symbol].get('Close', current_data[symbol].get('close', 0))
                positions_value += price * quantity
        
        return self.cash + positions_value
    
    def _calculate_results(self) -> BacktestResult:
        """Calculate backtesting results"""
        if not self.equity_history:
            return BacktestResult(
                total_return=0.0, annualized_return=0.0, sharpe_ratio=0.0,
                sortino_ratio=0.0, max_drawdown=0.0, max_drawdown_duration=0,
                win_rate=0.0, profit_factor=0.0, total_trades=0,
                winning_trades=0, losing_trades=0, average_win=0.0,
                average_loss=0.0, total_pnl=0.0, total_pnl_percent=0.0,
            total_pnl_percent_deployed=0.0, total_capital_deployed=0.0,
                equity_curve=pd.Series(), 
                drawdown_curve=pd.Series(), trades=[]
            )
        
        equity_df = pd.DataFrame(self.equity_history)
        
        # Normalize date column to timezone-naive
        if 'date' in equity_df.columns:
            equity_df['date'] = pd.to_datetime(equity_df['date'])
            if isinstance(equity_df['date'], pd.Series):
                if hasattr(equity_df['date'].dt, 'tz_localize'):
                    try:
                        equity_df['date'] = equity_df['date'].dt.tz_localize(None)
                    except:
                        pass
                equity_df['date'] = equity_df['date'].dt.normalize()
        
        equity_series = equity_df.set_index('date')['equity']
        
        # Ensure index is timezone-naive and normalized
        if isinstance(equity_series.index, pd.DatetimeIndex):
            if equity_series.index.tz is not None:
                equity_series.index = equity_series.index.tz_localize(None)
            equity_series.index = equity_series.index.normalize()
        
        # Calculate returns
        returns = equity_series.pct_change().dropna()
        
        # Total return
        total_return = (equity_series.iloc[-1] / equity_series.iloc[0]) - 1
        
        # Annualized return - normalize dates for subtraction
        start_idx = BacktestEngine._normalize_datetime(equity_series.index[0])
        end_idx = BacktestEngine._normalize_datetime(equity_series.index[-1])
        days = (end_idx - start_idx).days
        annualized_return = ((1 + total_return) ** (252 / days)) - 1 if days > 0 else 0
        
        # Sharpe ratio
        excess_returns = returns - (self.config.risk_free_rate / 252)
        sharpe_ratio = (excess_returns.mean() / excess_returns.std() * np.sqrt(252)) if excess_returns.std() > 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = (annualized_return / downside_std) if downside_std > 0 else 0
        
        # Drawdown
        peak = equity_series.cummax()
        drawdown = (equity_series - peak) / peak
        max_drawdown = abs(drawdown.min())
        
        # Max drawdown duration
        drawdown_periods = (drawdown < 0).astype(int)
        max_dd_duration = drawdown_periods.sum()
        
        # Trade statistics
        if self.trades:
            # Group trades by symbol to calculate P&L
            trade_pnl = []
            symbol_positions = {}
            
            for trade in self.trades:
                symbol = trade['symbol']
                if trade['action'] == 'BUY':
                    if symbol not in symbol_positions:
                        symbol_positions[symbol] = []
                    # Use actual cost (includes commission/slippage) if available, otherwise calculate
                    cost_per_share = trade.get('cost', trade['price'] * trade['quantity']) / trade['quantity']
                    symbol_positions[symbol].append({
                        'quantity': trade['quantity'],
                        'cost_per_share': cost_per_share,  # Cost per share including fees
                        'date': trade['date']
                    })
                else:  # SELL
                    if symbol in symbol_positions and symbol_positions[symbol]:
                        # Calculate P&L using FIFO
                        remaining_qty = trade['quantity']
                        # Use actual proceeds (after commission/slippage) if available
                        proceeds_per_share = trade.get('proceeds', trade['price'] * trade['quantity']) / trade['quantity']
                        
                        while remaining_qty > 0 and symbol_positions[symbol]:
                            buy_trade = symbol_positions[symbol][0]
                            qty_to_close = min(remaining_qty, buy_trade['quantity'])
                            
                            # Calculate net P&L using actual costs and proceeds (already include fees)
                            net_pnl = (proceeds_per_share - buy_trade['cost_per_share']) * qty_to_close
                            
                            trade_pnl.append(net_pnl)
                            
                            buy_trade['quantity'] -= qty_to_close
                            remaining_qty -= qty_to_close
                            
                            if buy_trade['quantity'] == 0:
                                symbol_positions[symbol].pop(0)
            
            winning_trades = [pnl for pnl in trade_pnl if pnl > 0]
            losing_trades = [pnl for pnl in trade_pnl if pnl < 0]
            
            win_rate = len(winning_trades) / len(trade_pnl) if trade_pnl else 0
            profit_factor = abs(sum(winning_trades) / sum(losing_trades)) if losing_trades else float('inf')
            
            # Average win/loss in dollars
            average_win_dollar = np.mean(winning_trades) if winning_trades else 0
            average_loss_dollar = np.mean(losing_trades) if losing_trades else 0
            
            # Calculate average win/loss as percentage of average trade size
            # Get average trade cost basis for percentage calculation
            avg_trade_cost = 0
            if self.trades:
                buy_trades = [t for t in self.trades if t['action'] == 'BUY']
                if buy_trades:
                    total_cost = sum(t.get('cost', t['price'] * t['quantity']) for t in buy_trades)
                    total_qty = sum(t['quantity'] for t in buy_trades)
                    avg_trade_cost = total_cost / len(buy_trades) if buy_trades else 0
            
            # Convert to percentages if we have trade cost basis
            if avg_trade_cost > 0:
                average_win = (average_win_dollar / avg_trade_cost) if average_win_dollar != 0 else 0
                average_loss = (average_loss_dollar / avg_trade_cost) if average_loss_dollar != 0 else 0
            else:
                # Fallback: use dollar amounts as decimals (will be displayed as dollars)
                average_win = average_win_dollar
                average_loss = average_loss_dollar
            
            # Calculate total P&L
            total_pnl = sum(trade_pnl)
            total_pnl_percent = (total_pnl / self.config.initial_capital) * 100 if self.config.initial_capital > 0 else 0
            
            # Calculate deployed capital (sum of all buy trade costs)
            total_capital_deployed = 0.0
            if self.trades:
                buy_trades = [t for t in self.trades if t['action'] == 'BUY']
                if buy_trades:
                    # Sum all buy costs (this represents capital actually deployed)
                    total_capital_deployed = sum(t.get('cost', t.get('price', 0) * t.get('quantity', 0)) for t in buy_trades)
            
            # Calculate P&L as percentage of deployed capital (more accurate for strategy performance)
            total_pnl_percent_deployed = (total_pnl / total_capital_deployed) * 100 if total_capital_deployed > 0 else 0.0
        else:
            win_rate = 0
            profit_factor = 0
            winning_trades = []
            losing_trades = []
            average_win = 0
            average_loss = 0
            total_pnl = 0.0
            total_pnl_percent = 0.0
            total_pnl_percent_deployed = 0.0
            total_capital_deployed = 0.0
        
        return BacktestResult(
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_dd_duration,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=len(self.trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            average_win=average_win,
            average_loss=average_loss,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            total_pnl_percent_deployed=total_pnl_percent_deployed,
            total_capital_deployed=total_capital_deployed,
            equity_curve=equity_series,
            drawdown_curve=drawdown,
            trades=self.trades
        )
