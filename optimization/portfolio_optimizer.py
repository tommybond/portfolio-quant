"""Portfolio optimizer."""

from typing import Any, Optional, List


class PortfolioOptimizer:
    def __init__(self, returns=None, **kwargs: Any):
        self.returns = returns

    def optimize(self, **kwargs: Any) -> Optional[dict]:
        return None

    def get_weights(self) -> Optional[List[float]]:
        return None
