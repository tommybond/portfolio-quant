"""
Strategy Base Class
Base class for implementing trading strategies
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from dataclasses import dataclass
import pandas as pd


@dataclass
class Signal:
    """Trading signal"""
    symbol: str
    action: str  # BUY, SELL, HOLD
    strength: float  # 0.0 to 1.0
    price: float
    quantity: Optional[int] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: str = ""


class StrategyBase(ABC):
    """Base class for trading strategies"""
    
    def __init__(self, name: str, parameters: Dict = None):
        """
        Initialize strategy
        
        Args:
            name: Strategy name
            parameters: Strategy-specific parameters
        """
        self.name = name
        self.parameters = parameters or {}
        self.signals = []
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> list[Signal]:
        """
        Generate trading signals from market data
        
        Args:
            data: Historical market data (OHLCV)
            
        Returns:
            List of trading signals
        """
        pass
    
    @abstractmethod
    def calculate_position_size(self, signal: Signal, portfolio_value: float, 
                               risk_per_trade: float = 0.02) -> int:
        """
        Calculate position size for a signal
        
        Args:
            signal: Trading signal
            portfolio_value: Current portfolio value
            risk_per_trade: Risk per trade (default 2%)
            
        Returns:
            Position size (quantity)
        """
        pass
    
    def validate_signal(self, signal: Signal) -> bool:
        """Validate signal before execution"""
        if signal.action not in ['BUY', 'SELL', 'HOLD']:
            return False
        
        if signal.strength < 0.0 or signal.strength > 1.0:
            return False
        
        if signal.price <= 0:
            return False
        
        return True
    
    def get_parameters(self) -> Dict:
        """Get strategy parameters"""
        return self.parameters.copy()
    
    def set_parameters(self, parameters: Dict):
        """Update strategy parameters"""
        self.parameters.update(parameters)
