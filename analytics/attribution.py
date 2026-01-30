"""Performance attribution."""

from typing import Any, Optional


class PerformanceAttribution:
    def __init__(self, returns=None, **kwargs: Any):
        self.returns = returns

    def attribute(self, **kwargs: Any) -> Optional[dict]:
        return None
