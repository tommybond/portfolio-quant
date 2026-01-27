
import pandas as pd
from monitoring.audit import log_event

class RiskManager:
    def __init__(self, max_daily_dd=0.03, max_total_dd=0.12):
        self.max_daily_dd = max_daily_dd
        self.max_total_dd = max_total_dd
        self.kill = False

    def evaluate(self, equity):
        peak = equity.cummax()
        dd = (peak - equity) / peak
        if dd.iloc[-1] > self.max_total_dd:
            self.kill = True
            log_event("KILL_SWITCH", float(dd.iloc[-1]))
            return "KILL"
        return "OK"
