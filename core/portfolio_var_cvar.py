
import numpy as np
import pandas as pd

class PortfolioRisk:
    def __init__(self, returns):
        self.returns = returns

    def var(self, level=0.05):
        return np.quantile(self.returns, level)

    def cvar(self, level=0.05):
        var = self.var(level)
        return self.returns[self.returns <= var].mean()
