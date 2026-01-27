"""
Walk-Forward Analysis
Rolling window optimization and validation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .backtest_engine import BacktestEngine, BacktestConfig, BacktestResult
from .strategy_base import StrategyBase


class WalkForwardAnalyzer:
    """Walk-forward optimization and analysis"""
    
    def __init__(self, strategy: StrategyBase, optimization_window: int = 252, 
                 test_window: int = 63, step_size: int = 21):
        """
        Initialize walk-forward analyzer
        
        Args:
            strategy: Strategy to optimize
            optimization_window: Days in optimization window (default: 1 year)
            test_window: Days in test window (default: 1 quarter)
            step_size: Days to step forward (default: 1 month)
        """
        self.strategy = strategy
        self.optimization_window = optimization_window
        self.test_window = test_window
        self.step_size = step_size
    
    def optimize_parameters(self, data: pd.DataFrame, param_ranges: Dict[str, List]) -> Dict:
        """
        Optimize strategy parameters on optimization window
        
        Args:
            data: Historical data for optimization
            param_ranges: Dictionary of parameter names to value ranges
        
        Returns:
            Best parameters found
        """
        best_params = None
        best_sharpe = -np.inf
        
        # Generate parameter combinations
        from itertools import product
        
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        
        for param_combo in product(*param_values):
            params = dict(zip(param_names, param_combo))
            
            # Create strategy with these parameters
            strategy_instance = type(self.strategy)(**params)
            
            # Run backtest on optimization window
            config = BacktestConfig(
                initial_capital=100000,
                commission=0.001,
                slippage=0.0005
            )
            
            engine = BacktestEngine(config)
            result = engine.run_backtest(strategy_instance, data)
            
            # Use Sharpe ratio as optimization metric
            if result.sharpe_ratio > best_sharpe:
                best_sharpe = result.sharpe_ratio
                best_params = params
        
        return best_params or {}
    
    def run_walk_forward(self, data: pd.DataFrame, param_ranges: Optional[Dict] = None) -> List[BacktestResult]:
        """
        Run walk-forward analysis
        
        Args:
            data: Full historical data
            param_ranges: Parameter ranges for optimization (optional)
        
        Returns:
            List of backtest results for each test period
        """
        results = []
        
        # Sort data by date
        data_sorted = data.sort_index()
        start_date = data_sorted.index[0]
        end_date = data_sorted.index[-1]
        
        current_date = start_date + timedelta(days=self.optimization_window)
        
        while current_date + timedelta(days=self.test_window) <= end_date:
            # Define windows
            opt_start = current_date - timedelta(days=self.optimization_window)
            opt_end = current_date
            test_start = current_date
            test_end = current_date + timedelta(days=self.test_window)
            
            # Get data windows
            opt_data = data_sorted[(data_sorted.index >= opt_start) & (data_sorted.index < opt_end)]
            test_data = data_sorted[(data_sorted.index >= test_start) & (data_sorted.index < test_end)]
            
            if len(opt_data) < 50 or len(test_data) < 10:
                current_date += timedelta(days=self.step_size)
                continue
            
            # Optimize parameters on optimization window
            if param_ranges:
                best_params = self.optimize_parameters(opt_data, param_ranges)
                # Create strategy with optimized parameters
                strategy_instance = type(self.strategy)(**best_params)
            else:
                strategy_instance = self.strategy
            
            # Test on test window
            config = BacktestConfig(
                initial_capital=100000,
                commission=0.001,
                slippage=0.0005
            )
            
            engine = BacktestEngine(config)
            result = engine.run_backtest(strategy_instance, test_data)
            
            # Add metadata
            result.period_start = test_start
            result.period_end = test_end
            result.optimization_params = best_params if param_ranges else {}
            
            results.append(result)
            
            # Move forward
            current_date += timedelta(days=self.step_size)
        
        return results
    
    def analyze_results(self, results: List[BacktestResult]) -> Dict:
        """Analyze walk-forward results"""
        if not results:
            return {}
        
        sharpe_ratios = [r.sharpe_ratio for r in results if not np.isnan(r.sharpe_ratio)]
        returns = [r.total_return for r in results if not np.isnan(r.total_return)]
        max_drawdowns = [r.max_drawdown for r in results if not np.isnan(r.max_drawdown)]
        
        return {
            'num_periods': len(results),
            'avg_sharpe': np.mean(sharpe_ratios) if sharpe_ratios else 0,
            'std_sharpe': np.std(sharpe_ratios) if sharpe_ratios else 0,
            'avg_return': np.mean(returns) if returns else 0,
            'avg_max_dd': np.mean(max_drawdowns) if max_drawdowns else 0,
            'consistency': len([r for r in results if r.sharpe_ratio > 0]) / len(results) if results else 0,
            'best_period': max(results, key=lambda x: x.sharpe_ratio if not np.isnan(x.sharpe_ratio) else -np.inf),
            'worst_period': min(results, key=lambda x: x.sharpe_ratio if not np.isnan(x.sharpe_ratio) else np.inf)
        }


class MonteCarloBacktest:
    """Monte Carlo simulation for backtesting"""
    
    def __init__(self, n_simulations: int = 1000):
        """
        Initialize Monte Carlo backtest
        
        Args:
            n_simulations: Number of Monte Carlo simulations
        """
        self.n_simulations = n_simulations
    
    def simulate(self, returns: pd.Series, initial_capital: float = 100000) -> List[Dict]:
        """
        Run Monte Carlo simulation
        
        Args:
            returns: Historical returns series
            initial_capital: Starting capital
        
        Returns:
            List of simulation results
        """
        results = []
        
        for _ in range(self.n_simulations):
            # Bootstrap sample returns
            simulated_returns = np.random.choice(returns.values, size=len(returns), replace=True)
            
            # Calculate equity curve
            equity = initial_capital
            equity_curve = [equity]
            
            for ret in simulated_returns:
                equity *= (1 + ret)
                equity_curve.append(equity)
            
            # Calculate metrics
            final_value = equity_curve[-1]
            total_return = (final_value / initial_capital) - 1
            
            equity_series = pd.Series(equity_curve)
            returns_series = equity_series.pct_change().dropna()
            
            if len(returns_series) > 0:
                sharpe = returns_series.mean() / returns_series.std() * np.sqrt(252) if returns_series.std() > 0 else 0
                
                # Calculate drawdown
                running_max = equity_series.expanding().max()
                drawdown = (equity_series - running_max) / running_max
                max_drawdown = drawdown.min()
            else:
                sharpe = 0
                max_drawdown = 0
            
            results.append({
                'final_value': final_value,
                'total_return': total_return,
                'sharpe_ratio': sharpe,
                'max_drawdown': max_drawdown,
                'equity_curve': equity_curve
            })
        
        return results
    
    def analyze_simulations(self, results: List[Dict]) -> Dict:
        """Analyze Monte Carlo simulation results"""
        returns = [r['total_return'] for r in results]
        sharpe_ratios = [r['sharpe_ratio'] for r in results]
        max_drawdowns = [r['max_drawdown'] for r in results]
        
        return {
            'mean_return': np.mean(returns),
            'std_return': np.std(returns),
            'percentile_5': np.percentile(returns, 5),
            'percentile_95': np.percentile(returns, 95),
            'mean_sharpe': np.mean(sharpe_ratios),
            'mean_max_dd': np.mean(max_drawdowns),
            'worst_case_return': np.min(returns),
            'best_case_return': np.max(returns),
            'probability_positive': len([r for r in returns if r > 0]) / len(returns)
        }
