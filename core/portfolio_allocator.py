
import numpy as np
import pandas as pd

class PortfolioAllocator:
    def __init__(self, capital):
        self.capital = capital

    def allocate(self, returns_df, max_weight=0.3):
        corr = returns_df.corr()
        inv_corr = 1 / (corr.sum())
        weights = inv_corr / inv_corr.sum()
        weights = weights.clip(upper=max_weight)
        weights = weights / weights.sum()
        return weights, corr
