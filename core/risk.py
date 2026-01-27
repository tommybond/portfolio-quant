
import pandas as pd
import numpy as np
from monitoring.audit import log_event
from core.portfolio_var_cvar import PortfolioRisk
from core.stress_testing import StressTester
from monitoring.risk_limits_alerts import RiskLimits

class RiskManager:
    def __init__(self, max_daily_dd=0.03, max_total_dd=0.12, max_var=-0.05):
        self.max_daily_dd = max_daily_dd
        self.max_total_dd = max_total_dd
        self.max_var = max_var
        self.kill = False
        self.risk_limits = RiskLimits(max_drawdown=-max_total_dd, max_var=max_var)
        self.portfolio_risk = None
        self.stress_tester = None

    def evaluate(self, equity):
        peak = equity.cummax()
        dd = (peak - equity) / peak
        max_dd = float(dd.max())
        
        # Calculate returns for VaR/CVaR
        returns = equity.pct_change().dropna()
        if len(returns) > 0:
            self.portfolio_risk = PortfolioRisk(returns)
            self.stress_tester = StressTester(returns)
        
        # Check drawdown limits
        if dd.iloc[-1] > self.max_total_dd:
            self.kill = True
            log_event("KILL_SWITCH", {"drawdown": float(dd.iloc[-1]), "max_allowed": self.max_total_dd})
            return "KILL"
        
        # Check VaR limits if available
        if self.portfolio_risk is not None:
            var = self.portfolio_risk.var(level=0.05)
            metrics = {
                'Max Drawdown': -max_dd,
                'VaR': var
            }
            alerts = self.risk_limits.check(metrics)
            if alerts:
                log_event("RISK_LIMIT_ALERT", {"alerts": alerts, "metrics": metrics})
                if 'VAR LIMIT BREACHED' in alerts:
                    self.kill = True
                    return "KILL"
        
        return "OK"
    
    def get_var(self, level=0.05):
        """Get Value at Risk"""
        if self.portfolio_risk is None:
            return None
        return self.portfolio_risk.var(level=level)
    
    def get_cvar(self, level=0.05):
        """Get Conditional Value at Risk (Expected Shortfall)"""
        if self.portfolio_risk is None:
            return None
        return self.portfolio_risk.cvar(level=level)
    
    def stress_test(self, shock_pct=None):
        """Run stress test scenario"""
        if self.stress_tester is None:
            return None
        if shock_pct is None:
            return self.stress_tester.historical_worst(percentile=0.01)
        return self.stress_tester.shock(shock_pct)
