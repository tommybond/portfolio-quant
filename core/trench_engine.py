
import numpy as np
import pandas as pd

class TrenchStrategyEngine:
    def __init__(self, avg_price, base_qty, capital, risk_limit=0.25):
        self.avg_price = avg_price
        self.base_qty = base_qty
        self.capital = capital
        self.risk_limit = risk_limit
        self.trenches = []
        self.inventory_value = avg_price * base_qty

    def volatility_spacing(self, atr, levels):
        return [atr * m for m in levels]

    def generate_buy_trenches(self, atr, multipliers, qty_weights):
        prices = [self.avg_price - x for x in self.volatility_spacing(atr, multipliers)]
        qtys = [self.base_qty * w for w in qty_weights]
        self.trenches = list(zip(prices, qtys))

    def blended_price(self):
        total_value = self.inventory_value
        total_qty = self.base_qty
        for p, q in self.trenches:
            total_value += p * q
            total_qty += q
        return total_value / total_qty

    def sell_levels(self, profit_steps, sell_weights):
        bp = self.blended_price()
        return [(bp * (1 + p), sell_weights[i]) for i, p in enumerate(profit_steps)]
