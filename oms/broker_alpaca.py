"""
Alpaca Broker Integration
Handles order submission and management via Alpaca API
"""

import os
from typing import Dict, Optional
from .oms import Order, OrderStatus, OrderType

try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False


class AlpacaBroker:
    """Alpaca broker integration"""
    
    def __init__(self):
        """Initialize Alpaca API client"""
        if not ALPACA_AVAILABLE:
            raise ImportError("alpaca-trade-api not installed")
        
        api_key = os.getenv('ALPACA_API_KEY')
        api_secret = os.getenv('ALPACA_SECRET_KEY')
        base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        
        if not api_key or not api_secret:
            raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set")
        
        self.api = tradeapi.REST(api_key, api_secret, base_url, api_version='v2')
    
    def submit_order(self, order: Order) -> Dict:
        """Submit order to Alpaca"""
        try:
            # Convert order to Alpaca format
            # Alpaca expects lowercase for time_in_force: 'day', 'gtc', 'ioc', 'fok'
            time_in_force = (order.time_in_force or 'day').lower()
            
            order_data = {
                'symbol': order.symbol,
                'qty': order.quantity,
                'side': order.side.lower(),  # Alpaca expects lowercase: 'buy' or 'sell'
                'type': self._convert_order_type(order.order_type),
                'time_in_force': time_in_force
            }
            
            if order.order_type == OrderType.LIMIT:
                if not order.price:
                    raise ValueError("Limit order requires price")
                order_data['limit_price'] = float(order.price)
            elif order.order_type == OrderType.STOP:
                if not order.stop_price:
                    raise ValueError("Stop order requires stop_price")
                order_data['stop_price'] = float(order.stop_price)
            elif order.order_type == OrderType.STOP_LIMIT:
                if not order.stop_price or not order.price:
                    raise ValueError("Stop-limit order requires both stop_price and price")
                order_data['stop_price'] = float(order.stop_price)
                order_data['limit_price'] = float(order.price)
            
            # Submit order
            submitted_order = self.api.submit_order(**order_data)
            
            # Get rejection reason if order was rejected
            rejection_reason = None
            if hasattr(submitted_order, 'reject_reason') and submitted_order.reject_reason:
                rejection_reason = submitted_order.reject_reason
            elif hasattr(submitted_order, 'message') and submitted_order.message:
                rejection_reason = submitted_order.message
            
            result = {
                'order_id': submitted_order.id if hasattr(submitted_order, 'id') else None,
                'status': self._convert_status(submitted_order.status),
                'submitted_at': submitted_order.submitted_at if hasattr(submitted_order, 'submitted_at') else None
            }
            
            if rejection_reason:
                result['rejection_reason'] = rejection_reason
            
            return result
        except Exception as e:
            # Extract more details from Alpaca API errors
            error_msg = str(e)
            if hasattr(e, 'status_code'):
                error_msg += f" (Status: {e.status_code})"
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                error_msg += f" - {e.response.text}"
            # Re-raise with more context
            raise Exception(f"Alpaca order submission failed: {error_msg}")
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel order"""
        try:
            self.api.cancel_order(order_id)
            return True
        except Exception as e:
            print(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get order status from Alpaca"""
        try:
            order = self.api.get_order(order_id)
            return {
                'status': self._convert_status(order.status),
                'filled_quantity': int(order.filled_qty),
                'average_fill_price': float(order.filled_avg_price) if order.filled_avg_price else None
            }
        except Exception as e:
            print(f"Failed to get order status: {e}")
            return {}
    
    def get_positions(self) -> list:
        """Get current positions"""
        try:
            positions = self.api.list_positions()
            return [
                {
                    'symbol': pos.symbol,
                    'quantity': int(pos.qty),
                    'average_price': float(pos.avg_entry_price),
                    'current_price': float(pos.current_price),
                    'unrealized_pnl': float(pos.unrealized_pl)
                }
                for pos in positions
            ]
        except Exception as e:
            print(f"Failed to get positions: {e}")
            return []
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        try:
            account = self.api.get_account()
            return {
                'buying_power': float(account.buying_power),
                'cash': float(account.cash),
                'equity': float(account.equity),
                'portfolio_value': float(account.portfolio_value)
            }
        except Exception as e:
            print(f"Failed to get account info: {e}")
            return {}
    
    def _convert_order_type(self, order_type: OrderType) -> str:
        """Convert OrderType to Alpaca format"""
        mapping = {
            OrderType.MARKET: 'market',
            OrderType.LIMIT: 'limit',
            OrderType.STOP: 'stop',
            OrderType.STOP_LIMIT: 'stop_limit'
        }
        return mapping.get(order_type, 'market')
    
    def _convert_status(self, alpaca_status: str) -> str:
        """Convert Alpaca status to OrderStatus"""
        mapping = {
            'new': OrderStatus.PENDING.value,
            'accepted': OrderStatus.SUBMITTED.value,
            'partially_filled': OrderStatus.PARTIALLY_FILLED.value,
            'filled': OrderStatus.FILLED.value,
            'canceled': OrderStatus.CANCELLED.value,
            'expired': OrderStatus.EXPIRED.value,
            'rejected': OrderStatus.REJECTED.value
        }
        return mapping.get(alpaca_status.lower(), OrderStatus.PENDING.value)
