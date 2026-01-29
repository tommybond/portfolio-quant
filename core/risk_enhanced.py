"""
Enhanced Risk Management
Sector limits, leverage controls, liquidity risk, concentration limits
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from core.risk import RiskManager


class EnhancedRiskManager(RiskManager):
    """Extended risk manager with additional controls"""
    
    def __init__(self, max_daily_dd=0.03, max_total_dd=0.12, max_var=-0.05,
                 max_sector_weight=0.25, max_leverage=2.0, min_liquidity_score=0.5):
        """
        Initialize enhanced risk manager
        
        Args:
            max_daily_dd: Maximum daily drawdown
            max_total_dd: Maximum total drawdown
            max_var: Maximum VaR limit
            max_sector_weight: Maximum weight per sector (25%)
            max_leverage: Maximum leverage ratio (2.0x)
            min_liquidity_score: Minimum liquidity score (0.0-1.0)
        """
        super().__init__(max_daily_dd, max_total_dd, max_var)
        self.max_sector_weight = max_sector_weight
        self.max_leverage = max_leverage
        self.min_liquidity_score = min_liquidity_score
        self.sector_weights = {}
        self.leverage_ratio = 1.0
    
    def check_sector_concentration(self, symbol: str, quantity: int, 
                                  price: float, portfolio_value: float) -> Dict:
        """
        Check sector concentration limits
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity
            price: Order price
            portfolio_value: Total portfolio value
            
        Returns:
            Dict with 'allowed', 'current_weight', 'max_weight', 'violation'
        """
        # Get sector for symbol (simplified - would use actual sector data)
        sector = self._get_sector(symbol)
        
        # Calculate new position value
        position_value = quantity * price
        new_weight = (position_value / portfolio_value) if portfolio_value > 0 else 0
        
        # Get current sector weight
        current_sector_weight = self.sector_weights.get(sector, 0.0)
        new_sector_weight = current_sector_weight + new_weight
        
        violation = new_sector_weight > self.max_sector_weight
        
        return {
            'allowed': not violation,
            'sector': sector,
            'current_weight': current_sector_weight,
            'new_weight': new_sector_weight,
            'max_weight': self.max_sector_weight,
            'violation': violation
        }
    
    def check_leverage_limit(self, portfolio_value: float, 
                            total_exposure: float) -> Dict:
        """
        Check leverage limits
        
        Args:
            portfolio_value: Portfolio equity value
            total_exposure: Total position exposure (including margin)
            
        Returns:
            Dict with 'allowed', 'current_leverage', 'max_leverage', 'violation'
        """
        current_leverage = (total_exposure / portfolio_value) if portfolio_value > 0 else 0
        violation = current_leverage > self.max_leverage
        
        return {
            'allowed': not violation,
            'current_leverage': current_leverage,
            'max_leverage': self.max_leverage,
            'violation': violation
        }
    
    def calculate_liquidity_score(self, symbol: str, quantity: int) -> float:
        """
        Calculate liquidity score for a position
        
        Args:
            symbol: Trading symbol
            quantity: Position quantity
            
        Returns:
            Liquidity score (0.0-1.0, higher is more liquid)
        """
        # Simplified liquidity scoring
        # Real implementation would use:
        # - Average daily volume (ADV)
        # - Bid-ask spread
        # - Order book depth
        # - Historical fill rates
        
        # For now, use a simple heuristic
        # Assume large-cap stocks are more liquid
        if symbol.endswith('.NS') or symbol.endswith('.BO'):
            # Indian stocks - assume moderate liquidity
            base_score = 0.6
        else:
            # US stocks - assume higher liquidity
            base_score = 0.8
        
        # Adjust for quantity (larger positions = lower liquidity)
        if quantity < 1000:
            quantity_factor = 1.0
        elif quantity < 10000:
            quantity_factor = 0.9
        else:
            quantity_factor = 0.7
        
        return base_score * quantity_factor
    
    def check_liquidity_requirement(self, symbol: str, quantity: int) -> Dict:
        """
        Check if position meets liquidity requirements
        
        Args:
            symbol: Trading symbol
            quantity: Position quantity
            
        Returns:
            Dict with 'allowed', 'liquidity_score', 'min_score', 'violation'
        """
        liquidity_score = self.calculate_liquidity_score(symbol, quantity)
        violation = liquidity_score < self.min_liquidity_score
        
        return {
            'allowed': not violation,
            'liquidity_score': liquidity_score,
            'min_score': self.min_liquidity_score,
            'violation': violation
        }
    
    def check_concentration_limit(self, symbol: str, quantity: int, price: float,
                                 portfolio_value: float, max_position_weight: float = 0.15) -> Dict:
        """
        Check single-name concentration limit
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity
            price: Order price
            portfolio_value: Total portfolio value
            max_position_weight: Maximum position weight (default 15%)
            
        Returns:
            Dict with 'allowed', 'current_weight', 'max_weight', 'violation'
        """
        position_value = quantity * price
        new_weight = (position_value / portfolio_value) if portfolio_value > 0 else 0
        violation = new_weight > max_position_weight
        
        return {
            'allowed': not violation,
            'current_weight': new_weight,
            'max_weight': max_position_weight,
            'violation': violation
        }
    
    def comprehensive_pre_trade_check(self, symbol: str, side: str, quantity: int,
                                     price: float, portfolio_value: float,
                                     total_exposure: float) -> Dict:
        """
        Comprehensive pre-trade risk check
        
        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Order quantity
            price: Order price
            portfolio_value: Portfolio equity value
            total_exposure: Total position exposure
            
        Returns:
            Dict with all risk checks and overall 'allowed' flag
        """
        checks = {
            'allowed': True,
            'checks': {}
        }
        
        # Sector concentration
        sector_check = self.check_sector_concentration(symbol, quantity, price, portfolio_value)
        checks['checks']['sector_concentration'] = sector_check
        if sector_check['violation']:
            checks['allowed'] = False
        
        # Leverage limit
        leverage_check = self.check_leverage_limit(portfolio_value, total_exposure)
        checks['checks']['leverage'] = leverage_check
        if leverage_check['violation']:
            checks['allowed'] = False
        
        # Liquidity requirement
        liquidity_check = self.check_liquidity_requirement(symbol, quantity)
        checks['checks']['liquidity'] = liquidity_check
        if liquidity_check['violation']:
            checks['allowed'] = False
        
        # Single-name concentration
        concentration_check = self.check_concentration_limit(
            symbol, quantity, price, portfolio_value
        )
        checks['checks']['concentration'] = concentration_check
        if concentration_check['violation']:
            checks['allowed'] = False
        
        return checks
    
    def _get_sector(self, symbol: str) -> str:
        """
        Get sector for a symbol (simplified)
        
        In production, this would query a sector classification database
        """
        # Simplified sector mapping
        # Real implementation would use GICS, ICB, or custom classification
        
        sector_map = {
            'AAPL': 'Technology',
            'MSFT': 'Technology',
            'GOOGL': 'Technology',
            'AMZN': 'Consumer Discretionary',
            'TSLA': 'Consumer Discretionary',
            'JPM': 'Financials',
            'BAC': 'Financials',
            'JNJ': 'Healthcare',
            'PG': 'Consumer Staples',
            'XOM': 'Energy'
        }
        
        # Remove exchange suffix for lookup
        base_symbol = symbol.split('.')[0]
        return sector_map.get(base_symbol, 'Other')
    
    def update_sector_weights(self, positions: Dict[str, Dict]):
        """
        Update sector weight tracking
        
        Args:
            positions: Dict of symbol -> position data (quantity, price, etc.)
        """
        sector_values = {}
        total_value = 0.0
        
        for symbol, pos in positions.items():
            sector = self._get_sector(symbol)
            position_value = pos.get('quantity', 0) * pos.get('price', 0)
            
            if sector not in sector_values:
                sector_values[sector] = 0.0
            sector_values[sector] += position_value
            total_value += position_value
        
        # Calculate weights
        if total_value > 0:
            self.sector_weights = {
                sector: value / total_value
                for sector, value in sector_values.items()
            }
