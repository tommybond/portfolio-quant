
import statsmodels.api as sm

class FactorAttribution:
    def __init__(self, returns, factors):
        self.returns = returns
        self.factors = factors

    def regress(self):
        X = sm.add_constant(self.factors)
        model = sm.OLS(self.returns, X).fit()
        return model.params, model.rsquared
