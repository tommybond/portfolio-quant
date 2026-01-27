#!/usr/bin/env python3
"""
Backtest comparison: GOOGL with/without Macro Regime Position Sizing
Long-Term Portfolio, June 1, 2025 to Jan 27, 2026
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from backtesting.backtest_engine import BacktestEngine, BacktestConfig
from backtesting.strategies_advanced import InventoryAwareTrenchStrategy

def fetch_data(ticker: str, start_date: datetime, end_date: datetime):
    """Fetch historical data for ticker"""
    print(f"📊 Fetching {ticker} data from {start_date.date()} to {end_date.date()}...")
    
    # Fetch with extra buffer to ensure we have enough data
    buffer_days = 60  # Extra days for indicators
    fetch_start = start_date - timedelta(days=buffer_days)
    
    stock = yf.Ticker(ticker)
    hist = stock.history(start=fetch_start, end=end_date + timedelta(days=1))
    
    if hist.empty:
        raise ValueError(f"No data found for {ticker}")
    
    # Filter to actual date range
    hist = hist[(hist.index.date >= start_date.date()) & (hist.index.date <= end_date.date())]
    
    # Ensure proper column names
    hist.columns = [col.lower().capitalize() for col in hist.columns]
    if 'Close' not in hist.columns and 'close' in hist.columns:
        hist = hist.rename(columns={'close': 'Close', 'open': 'Open', 'high': 'High', 'low': 'Low', 'volume': 'Volume'})
    
    # Set symbol attribute
    hist.attrs = {'symbol': ticker}
    
    print(f"✅ Fetched {len(hist)} days of data")
    return hist

def run_backtest(config: BacktestConfig, strategy, data_dict: dict, test_name: str):
    """Run a single backtest"""
    print(f"\n{'='*60}")
    print(f"🧪 Running: {test_name}")
    print(f"{'='*60}")
    print(f"📋 Configuration:")
    print(f"   Portfolio Type: {config.portfolio_type}")
    print(f"   Initial Capital: ${config.initial_capital:,.2f}")
    print(f"   Risk:Reward Ratio: {config.risk_reward_ratio}")
    print(f"   Macro Regime: {'✅ Enabled' if config.use_macro_regime else '❌ Disabled'}")
    if config.use_macro_regime:
        print(f"   Base Position %: {config.macro_base_pct*100:.1f}%")
        print(f"   Max Position %: {config.macro_max_pct*100:.1f}%")
        print(f"   Classification: {config.macro_classification:.2f}x")
        print(f"   Persona: {config.macro_persona:.2f}x")
    print()
    
    engine = BacktestEngine(config)
    result = engine.run(strategy, data_dict)
    
    return result, engine

def print_results(result, engine, test_name: str):
    """Print formatted results"""
    print(f"\n{'='*60}")
    print(f"📊 RESULTS: {test_name}")
    print(f"{'='*60}")
    
    print(f"\n📈 Performance Metrics:")
    print(f"   Total Return: {result.total_return:.2f}%")
    print(f"   Annualized Return: {result.annualized_return:.2f}%")
    print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"   Sortino Ratio: {result.sortino_ratio:.2f}")
    print(f"   Max Drawdown: {result.max_drawdown:.2f}%")
    print(f"   Max DD Duration: {result.max_drawdown_duration} days")
    
    print(f"\n💰 Profit & Loss:")
    print(f"   Total P&L: ${result.total_pnl:,.2f}")
    print(f"   P&L % (Total Capital): {result.total_pnl_percent:.2f}%")
    print(f"   P&L % (Deployed Capital): {result.total_pnl_percent_deployed:.2f}%")
    print(f"   Total Capital Deployed: ${result.total_capital_deployed:,.2f}")
    
    print(f"\n📊 Trade Statistics:")
    print(f"   Total Trades: {result.total_trades}")
    print(f"   Winning Trades: {result.winning_trades}")
    print(f"   Losing Trades: {result.losing_trades}")
    print(f"   Win Rate: {result.win_rate:.2f}%")
    print(f"   Profit Factor: {result.profit_factor:.2f}")
    print(f"   Average Win: ${result.average_win:,.2f}")
    print(f"   Average Loss: ${result.average_loss:,.2f}")
    
    # Calculate average position size
    if result.trades:
        buy_trades = [t for t in result.trades if t.get('action') == 'BUY']
        if buy_trades:
            # Calculate cumulative positions per symbol for trench strategies
            symbol_positions = {}
            for trade in buy_trades:
                symbol = trade.get('symbol', 'UNKNOWN')
                trade_cost = trade.get('cost', trade.get('price', 0) * trade.get('quantity', 0))
                if symbol not in symbol_positions:
                    symbol_positions[symbol] = []
                symbol_positions[symbol].append(trade_cost)
            
            cumulative_positions = [sum(costs) for costs in symbol_positions.values()]
            avg_per_trade = sum([t.get('cost', t.get('price', 0) * t.get('quantity', 0)) for t in buy_trades]) / len(buy_trades)
            
            if cumulative_positions:
                avg_cumulative = sum(cumulative_positions) / len(cumulative_positions)
                is_trench = avg_cumulative > avg_per_trade * 1.5
                
                print(f"\n💼 Position Sizing:")
                if is_trench:
                    print(f"   Avg Cumulative Position: ${avg_cumulative:,.2f} ({avg_cumulative/result.total_capital_deployed*100:.1f}% of deployed)")
                    print(f"   Avg Per-Trade Size: ${avg_per_trade:,.2f} ({avg_per_trade/result.total_capital_deployed*100:.1f}% of deployed)")
                else:
                    print(f"   Avg Position Size: ${avg_per_trade:,.2f} ({avg_per_trade/result.total_capital_deployed*100:.1f}% of deployed)")
    
    # Show macro regime breakdown if available
    if engine.config.use_macro_regime and hasattr(engine, 'macro_regime_detector') and engine.macro_regime_detector:
        print(f"\n🏛️ Macro Regime Analysis:")
        regime_summary = engine.macro_regime_detector.get_regime_summary()
        if regime_summary:
            regimes = regime_summary.get('regimes', {})
            risk_on_pct = regimes.get('risk_on', {}).get('percentage', 0)
            neutral_pct = regimes.get('neutral', {}).get('percentage', 0)
            risk_off_pct = regimes.get('risk_off', {}).get('percentage', 0)
            avg_multiplier = regime_summary.get('avg_multiplier', 1.0)
            
            print(f"   Risk-On Periods: {risk_on_pct:.1f}%")
            print(f"   Neutral Periods: {neutral_pct:.1f}%")
            print(f"   Risk-Off Periods: {risk_off_pct:.1f}%")
            print(f"   Average Regime Multiplier: {avg_multiplier:.2f}x")
        
        if hasattr(engine, 'position_sizing_breakdowns') and engine.position_sizing_breakdowns:
            print(f"\n   Position Sizing Breakdowns: {len(engine.position_sizing_breakdowns)} decisions")
            # Show last 3 breakdowns
            for bd in engine.position_sizing_breakdowns[-3:]:
                breakdown = bd['breakdown']
                date_str = bd['date'].strftime('%Y-%m-%d') if hasattr(bd['date'], 'strftime') else str(bd['date'])
                print(f"      {date_str} ({bd['symbol']}): "
                      f"Base={breakdown['base_pct']*100:.1f}%, "
                      f"Vol={breakdown['volatility_multiplier']:.2f}x, "
                      f"Regime={breakdown['regime_multiplier']:.2f}x, "
                      f"Final={breakdown['final_pct']*100:.1f}%")

def compare_results(result_without, result_with, engine_without, engine_with):
    """Compare results between two backtests"""
    print(f"\n{'='*60}")
    print(f"📊 COMPARISON: Without vs With Macro Regime")
    print(f"{'='*60}")
    
    metrics = [
        ('Total Return', 'total_return', '%'),
        ('Annualized Return', 'annualized_return', '%'),
        ('Sharpe Ratio', 'sharpe_ratio', ''),
        ('Sortino Ratio', 'sortino_ratio', ''),
        ('Max Drawdown', 'max_drawdown', '%'),
        ('Win Rate', 'win_rate', '%'),
        ('Total P&L', 'total_pnl', '$'),
        ('P&L % (Deployed)', 'total_pnl_percent_deployed', '%'),
        ('Total Trades', 'total_trades', ''),
        ('Profit Factor', 'profit_factor', ''),
    ]
    
    print(f"\n{'Metric':<25} {'Without Macro':>15} {'With Macro':>15} {'Difference':>15}")
    print('-' * 70)
    
    for metric_name, attr, unit in metrics:
        val_without = getattr(result_without, attr)
        val_with = getattr(result_with, attr)
        diff = val_with - val_without
        
        if unit == '$':
            print(f"{metric_name:<25} {val_without:>14,.2f} {val_with:>14,.2f} {diff:>+14,.2f}")
        elif unit == '%':
            print(f"{metric_name:<25} {val_without:>14.2f}% {val_with:>14.2f}% {diff:>+14.2f}%")
        else:
            print(f"{metric_name:<25} {val_without:>15.2f} {val_with:>15.2f} {diff:>+15.2f}")
    
    # Capital utilization comparison
    print(f"\n💼 Capital Utilization:")
    if result_without.trades and result_with.trades:
        buy_without = [t for t in result_without.trades if t.get('action') == 'BUY']
        buy_with = [t for t in result_with.trades if t.get('action') == 'BUY']
        
        if buy_without and buy_with:
            deployed_without = result_without.total_capital_deployed
            deployed_with = result_with.total_capital_deployed
            
            initial_capital = 100000.0  # Use same initial capital for both
            print(f"   Capital Deployed (Without): ${deployed_without:,.2f} ({deployed_without/initial_capital*100:.1f}%)")
            print(f"   Capital Deployed (With): ${deployed_with:,.2f} ({deployed_with/initial_capital*100:.1f}%)")
            print(f"   Difference: ${deployed_with - deployed_without:,.2f} ({(deployed_with - deployed_without)/initial_capital*100:+.1f}%)")

def main():
    """Main test function"""
    print("="*60)
    print("🧪 GOOGL Backtest Comparison")
    print("   Strategy: Inventory-Aware Trench Strategy")
    print("   Portfolio Type: Long-Term")
    print("   Date Range: June 1, 2025 to Jan 27, 2026")
    print("="*60)
    
    # Configuration
    ticker = "GOOGL"
    start_date = datetime(2025, 6, 1)
    end_date = datetime(2026, 1, 27)
    initial_capital = 100000.0
    
    # Fetch data
    try:
        hist_data = fetch_data(ticker, start_date, end_date)
        print(f"\n📋 Data Info:")
        print(f"   Shape: {hist_data.shape}")
        print(f"   Columns: {list(hist_data.columns)}")
        print(f"   Date Range: {hist_data.index[0]} to {hist_data.index[-1]}")
        print(f"   Sample prices: Close={hist_data['Close'].iloc[-1]:.2f}, Open={hist_data['Open'].iloc[-1]:.2f}")
        
        # Ensure proper column names (lowercase for strategy)
        if 'Close' in hist_data.columns:
            hist_data = hist_data.rename(columns={'Close': 'close', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Volume': 'volume'})
        
        data_dict = {ticker: hist_data}
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Create strategy (same for both tests)
    strategy = InventoryAwareTrenchStrategy(
        base_position_pct=1.0,
        max_position_pct=0.15  # 15% cap per instrument
    )
    
    # Test 1: Without Macro Regime
    config_without = BacktestConfig(
        initial_capital=initial_capital,
        commission=0.001,  # 0.1%
        slippage=0.0005,   # 0.05%
        start_date=start_date,
        end_date=end_date,
        portfolio_type="Long-Term",
        risk_reward_ratio=4.0,  # Long-term default
        use_macro_regime=False
    )
    
    result_without, engine_without = run_backtest(
        config_without, strategy, data_dict, 
        "WITHOUT Macro Regime Position Sizing"
    )
    print_results(result_without, engine_without, "WITHOUT Macro Regime")
    
    # Test 2: With Macro Regime
    config_with = BacktestConfig(
        initial_capital=initial_capital,
        commission=0.001,
        slippage=0.0005,
        start_date=start_date,
        end_date=end_date,
        portfolio_type="Long-Term",
        risk_reward_ratio=4.0,
        use_macro_regime=True,
        macro_base_pct=0.04,  # 4% base
        macro_max_pct=0.15,   # 15% max
        macro_classification=1.2,  # CORE
        macro_persona=1.0     # Neutral aggression
    )
    
    # Create a fresh strategy instance for the second test
    strategy_with = InventoryAwareTrenchStrategy(
        base_position_pct=1.0,
        max_position_pct=0.15
    )
    
    result_with, engine_with = run_backtest(
        config_with, strategy_with, data_dict,
        "WITH Macro Regime Position Sizing"
    )
    
    # Debug: Check if macro regime detector initialized and signals generated
    if config_with.use_macro_regime:
        print(f"\n🔍 Debug: Macro Regime Status:")
        print(f"   Detector exists: {hasattr(engine_with, 'macro_regime_detector')}")
        print(f"   Detector initialized: {engine_with.macro_regime_detector is not None if hasattr(engine_with, 'macro_regime_detector') else False}")
        print(f"   Five trench sizer exists: {hasattr(engine_with, 'five_trench_sizer')}")
        print(f"   Five trench sizer initialized: {engine_with.five_trench_sizer is not None if hasattr(engine_with, 'five_trench_sizer') else False}")
        if hasattr(engine_with, '_historical_data') and engine_with._historical_data:
            print(f"   Historical data available: {list(engine_with._historical_data.keys())}")
            for symbol, df in engine_with._historical_data.items():
                print(f"      {symbol}: {len(df)} rows")
        print(f"   Position sizing breakdowns: {len(engine_with.position_sizing_breakdowns) if hasattr(engine_with, 'position_sizing_breakdowns') else 0}")
        print(f"   Total trades executed: {len(engine_with.trades) if hasattr(engine_with, 'trades') else 0}")
    
    print_results(result_with, engine_with, "WITH Macro Regime")
    
    # Compare results
    compare_results(result_without, result_with, engine_without, engine_with)
    
    print(f"\n{'='*60}")
    print("✅ Backtest comparison complete!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
