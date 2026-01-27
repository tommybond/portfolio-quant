
import numpy as np
import pandas as pd

class StressTester:
    def __init__(self, returns):
        self.returns = returns

    def shock(self, shock_pct):
        shocked_returns = self.returns + shock_pct
        return (1 + shocked_returns).cumprod()

    def historical_worst(self, percentile=0.01):
        shock = self.returns.quantile(percentile)
        return self.shock(shock)
