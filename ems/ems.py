"""Execution Management System."""

from enum import Enum
from typing import Optional, Any


class AlgorithmType(str, Enum):
    TWAP = "TWAP"
    VWAP = "VWAP"
    IMPLEMENTATION_SHORTFALL = "IMPLEMENTATION_SHORTFALL"


class ExecutionManager:
    def __init__(self, broker=None, **kwargs: Any):
        self.broker = broker

    def execute(self, symbol: str, side: str, quantity: int, algorithm: AlgorithmType = AlgorithmType.TWAP, **kwargs: Any) -> Optional[dict]:
        return None
