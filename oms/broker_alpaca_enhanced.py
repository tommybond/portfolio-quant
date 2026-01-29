"""
Enhanced Alpaca Broker Integration
Production-grade features: Advanced order types, order modification, multi-account support
"""

import os
from typing import Dict, Optional, List
from datetime import datetime
from .oms import Order, OrderStatus, OrderType

try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False


class EnhancedAlpacaBroker:
    """Enhanced Alpaca broker integration with advanced features"""
    
    def __init__(self, account_id: Optional[str] = None, paper: bool = True):
        """
        Initialize Alpaca API client
        
        Args:
            account_id: Optional account ID for multi-account support
            paper: Use paper trading account (default: True)
        """
        if not ALPACA_AVAILABLE:
            raise ImportError("alpaca-trade-api not installed")
        
        api_key = os.getenv('ALPACA_API_KEY')
        api_secret = os.getenv('ALPACA_SECRET_KEY')
        
        if paper:
            base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        else:
            base_url = os.getenv('ALPACA_LIVE_URL', 'https://api.alpaca.markets')
        
        if not api_key or not api_secret:
            raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set")
        
        self.api = tradeapi.REST(api_key, api_secret, base_url, api_version='v2')
        self.account_id = account_id
        self.paper = paper
    
    def submit_order(self, order: Order) -> Dict:
        """Submit order to Alpaca with advanced order types"""
        order_data = {
            'symbol': order.symbol,
            'qty': order.quantity,
            'side': order.side.lower(),
            'type': self._convert_order_type(order.order_type),
            'time_in_force': order.time_in_force or 'day'
        }
        
        # Handle different order types
        if order.order_type == OrderType.LIMIT:
            if not order.price:
                raise ValueError("Limit order requires price")
            order_data['limit_price'] = order.price
        
        elif order.order_type == OrderType.STOP:
            if not order.stop_price:
                raise ValueError("Stop order requires stop_price")
            order_data['stop_price'] = order.stop_price
        
        elif order.order_type == OrderType.STOP_LIMIT:
            if not order.stop_price or not order.price:
                raise ValueError("Stop-limit order requires both stop_price and price")
            order_data['stop_price'] = order.stop_price
            order_data['limit_price'] = order.price
        
        # Handle bracket orders (OCO)
        if hasattr(order, 'take_profit') and order.take_profit:
            order_data['order_class'] = 'bracket'
            order_data['take_profit'] = {'limit_price': order.take_profit}
            if hasattr(order, 'stop_loss') and order.stop_loss:
                order_data['stop_loss'] = {'stop_price': order.stop_loss}
        
        # Handle trailing stops
        if hasattr(order, 'trail_percent') and order.trail_percent:
            order_data['trail_percent'] = order.trail_percent
        elif hasattr(order, 'trail_price') and order.trail_price:
            order_data['trail_price'] = order.trail_price
        
        # Submit order
        try:
            submitted_order = self.api.submit_order(**order_data)
            
            return {
                'order_id': str(submitted_order.id),
                'status': self._convert_status(submitted_order.status),
                'submitted_at': submitted_order.submitted_at,
                'client_order_id': submitted_order.client_order_id
            }
        except Exception as e:
            raise Exception(f"Failed to submit order: {e}")
    
    def modify_order(self, order_id: str, quantity: Optional[int] = None, 
                    price: Optional[float] = None, stop_price: Optional[float] = None) -> Dict:
        """Modify an existing order"""
        try:
            # Alpaca doesn't have direct modify, so we cancel and replace
            original_order = self.api.get_order(order_id)
            
            # Cancel original
            self.api.cancel_order(order_id)
            
            # Create replacement order
            new_order_data = {
                'symbol': original_order.symbol,
                'qty': quantity or int(original_order.qty),
                'side': original_order.side,
                'type': original_order.type,
                'time_in_force': original_order.time_in_force
            }
            
            if price:
                new_order_data['limit_price'] = price
            elif hasattr(original_order, 'limit_price') and original_order.limit_price:
                new_order_data['limit_price'] = float(original_order.limit_price)
            
            if stop_price:
                new_order_data['stop_price'] = stop_price
            elif hasattr(original_order, 'stop_price') and original_order.stop_price:
                new_order_data['stop_price'] = float(original_order.stop_price)
            
            # Submit replacement
            new_order = self.api.submit_order(**new_order_data)
            
            return {
                'original_order_id': order_id,
                'new_order_id': str(new_order.id),
                'status': self._convert_status(new_order.status),
                'message': 'Order modified successfully'
            }
        except Exception as e:
            raise Exception(f"Failed to modify order: {e}")
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel order"""
        try:
            self.api.cancel_order(order_id)
            return True
        except Exception as e:
            print(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """Cancel all orders (optionally for a specific symbol)"""
        try:
            if symbol:
                orders = self.api.list_orders(status='open', symbols=[symbol])
            else:
                orders = self.api.list_orders(status='open')
            
            cancelled = 0
            for order in orders:
                try:
                    self.api.cancel_order(order.id)
                    cancelled += 1
                except:
                    pass
            
            return cancelled
        except Exception as e:
            print(f"Failed to cancel orders: {e}")
            return 0
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get order status from Alpaca"""
        try:
            order = self.api.get_order(order_id)
            return {
                'order_id': str(order.id),
                'status': self._convert_status(order.status),
                'symbol': order.symbol,
                'side': order.side,
                'quantity': int(order.qty),
                'filled_quantity': int(order.filled_qty) if order.filled_qty else 0,
                'average_fill_price': float(order.filled_avg_price) if order.filled_avg_price else None,
                'limit_price': float(order.limit_price) if hasattr(order, 'limit_price') and order.limit_price else None,
                'stop_price': float(order.stop_price) if hasattr(order, 'stop_price') and order.stop_price else None,
                'submitted_at': order.submitted_at,
                'updated_at': order.updated_at
            }
        except Exception as e:
            print(f"Failed to get order status: {e}")
            return {}
    
    def get_all_orders(self, status: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get all orders with optional status filter"""
        try:
            orders = self.api.list_orders(status=status, limit=limit)
            return [self.get_order_status(str(order.id)) for order in orders]
        except Exception as e:
            print(f"Failed to get orders: {e}")
            return []
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        try:
            positions = self.api.list_positions()
            return [
                {
                    'symbol': pos.symbol,
                    'quantity': int(pos.qty),
                    'average_price': float(pos.avg_entry_price),
                    'current_price': float(pos.current_price),
                    'market_value': float(pos.market_value),
                    'cost_basis': float(pos.cost_basis),
                    'unrealized_pl': float(pos.unrealized_pl),
                    'unrealized_plpc': float(pos.unrealized_plpc),
                    'side': pos.side
                }
                for pos in positions
            ]
        except Exception as e:
            print(f"Failed to get positions: {e}")
            return []
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get position for a specific symbol"""
        try:
            position = self.api.get_position(symbol)
            return {
                'symbol': position.symbol,
                'quantity': int(position.qty),
                'average_price': float(position.avg_entry_price),
                'current_price': float(position.current_price),
                'market_value': float(position.market_value),
                'cost_basis': float(position.cost_basis),
                'unrealized_pl': float(position.unrealized_pl),
                'unrealized_plpc': float(position.unrealized_plpc),
                'side': position.side
            }
        except Exception as e:
            # Position doesn't exist
            return None
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        try:
            account = self.api.get_account()
            return {
                'account_number': account.account_number,
                'buying_power': float(account.buying_power),
                'cash': float(account.cash),
                'equity': float(account.equity),
                'portfolio_value': float(account.portfolio_value),
                'pattern_day_trader': account.pattern_day_trader,
                'trading_blocked': account.trading_blocked,
                'account_blocked': account.account_blocked,
                'daytrading_buying_power': float(account.daytrading_buying_power) if hasattr(account, 'daytrading_buying_power') else None,
                'regt_buying_power': float(account.regt_buying_power) if hasattr(account, 'regt_buying_power') else None,
                'long_market_value': float(account.long_market_value) if hasattr(account, 'long_market_value') else None,
                'short_market_value': float(account.short_market_value) if hasattr(account, 'short_market_value') else None
            }
        except Exception as e:
            print(f"Failed to get account info: {e}")
            return {}
    
    def get_activities(self, activity_types: Optional[List[str]] = None, 
                      date: Optional[datetime] = None) -> List[Dict]:
        """Get account activities (trades, dividends, etc.)"""
        try:
            activities = self.api.get_activities(
                activity_types=activity_types,
                date=date.strftime('%Y-%m-%d') if date else None
            )
            
            result = []
            for activity in activities:
                result.append({
                    'id': activity.id,
                    'activity_type': activity.activity_type,
                    'symbol': activity.symbol if hasattr(activity, 'symbol') else None,
                    'date': activity.date,
                    'net_amount': float(activity.net_amount) if hasattr(activity, 'net_amount') else None,
                    'qty': float(activity.qty) if hasattr(activity, 'qty') else None,
                    'price': float(activity.price) if hasattr(activity, 'price') else None
                })
            
            return result
        except Exception as e:
            print(f"Failed to get activities: {e}")
            return []
    
    def _convert_order_type(self, order_type: OrderType) -> str:
        """Convert OrderType to Alpaca format"""
        mapping = {
            OrderType.MARKET: 'market',
            OrderType.LIMIT: 'limit',
            OrderType.STOP: 'stop',
            OrderType.STOP_LIMIT: 'stop_limit',
        }
        return mapping.get(order_type, 'market')
    
    def _convert_status(self, alpaca_status: str) -> str:
        """Convert Alpaca status to OrderStatus"""
        mapping = {
            'new': OrderStatus.PENDING.value,
            'accepted': OrderStatus.SUBMITTED.value,
            'pending_new': OrderStatus.PENDING.value,
            'accepted_for_bidding': OrderStatus.SUBMITTED.value,
            'partially_filled': OrderStatus.PARTIALLY_FILLED.value,
            'filled': OrderStatus.FILLED.value,
            'done_for_day': OrderStatus.FILLED.value,
            'canceled': OrderStatus.CANCELLED.value,
            'expired': OrderStatus.EXPIRED.value,
            'replaced': OrderStatus.SUBMITTED.value,
            'pending_cancel': OrderStatus.PENDING.value,
            'pending_replace': OrderStatus.PENDING.value,
            'rejected': OrderStatus.REJECTED.value,
            'stopped': OrderStatus.CANCELLED.value
        }
        return mapping.get(alpaca_status.lower(), OrderStatus.PENDING.value)
