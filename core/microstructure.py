
import numpy as np

class MicrostructureModel:
    def __init__(self, spread, adv):
        self.spread = spread
        self.adv = adv

    def impact_cost(self, qty):
        return self.spread + (qty / self.adv) ** 0.5

    def expected_fill_price(self, mid_price, qty, side='buy'):
        impact = self.impact_cost(qty)
        if side == 'buy':
            return mid_price * (1 + impact)
        return mid_price * (1 - impact)
