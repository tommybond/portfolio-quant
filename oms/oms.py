"""
Order Management System
Core OMS functionality for order lifecycle management
"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass
from database.models import Trade, create_session
from sqlalchemy.orm import Session


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"


@dataclass
class Order:
    """Order data structure"""
    symbol: str
    side: str  # BUY or SELL
    quantity: int
    order_type: OrderType
    price: Optional[float] = None  # For LIMIT orders
    stop_price: Optional[float] = None  # For STOP orders
    time_in_force: str = "DAY"  # DAY, GTC, IOC, FOK
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    average_fill_price: Optional[float] = None
    broker_order_id: Optional[str] = None
    created_at: datetime = None
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None  # Reason if order was rejected
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class OrderManager:
    """Manages order lifecycle"""
    
    def __init__(self, broker=None, db_session: Optional[Session] = None):
        """
        Initialize Order Manager
        
        Args:
            broker: Broker instance (AlpacaBroker, IBKRBroker, etc.)
            db_session: Database session
        """
        self.broker = broker
        self.db = db_session or create_session()
        self.orders: Dict[str, Order] = {}  # In-memory order cache
    
    def create_order(self, order: Order, user_id: int) -> Order:
        """Create and submit an order"""
        print(f"🔷 OMS.create_order called: {order.symbol} x{order.quantity}, user={user_id}")
        
        # Validate order
        print(f"   Validating order...")
        if not self._validate_order(order):
            print(f"   ❌ Order validation failed")
            order.status = OrderStatus.REJECTED
            return order
        print(f"   ✅ Order validation passed")
        
        # Pre-trade risk checks
        print(f"   Running pre-trade checks...")
        if not self._pre_trade_checks(order, user_id):
            print(f"   ❌ Pre-trade checks failed")
            order.status = OrderStatus.REJECTED
            return order
        print(f"   ✅ Pre-trade checks passed")
        
        # Submit to broker if available
        if self.broker:
            print(f"   📤 Submitting to broker: {self.broker.__class__.__name__}")
            try:
                broker_response = self.broker.submit_order(order)
                print(f"   ✅ Broker response received: {broker_response}")
                
                order.broker_order_id = broker_response.get('order_id')
                print(f"   Broker order ID: {order.broker_order_id}")
                
                # Check if broker rejected the order
                broker_status = broker_response.get('status', '').upper()
                print(f"   Broker status: {broker_status}")
                
                if broker_status == 'REJECTED':
                    order.status = OrderStatus.REJECTED
                    # Store rejection reason if available
                    if 'rejection_reason' in broker_response:
                        order.rejection_reason = broker_response['rejection_reason']
                    print(f"   ❌ Order REJECTED by broker: {order.rejection_reason}")
                elif broker_status == 'PENDING':
                    # Order is pending, mark as submitted since it's in the broker's system
                    order.status = OrderStatus.SUBMITTED
                    order.submitted_at = datetime.utcnow()
                    print(f"   ✅ Order PENDING/SUBMITTED at {order.submitted_at}")
                else:
                    # SUBMITTED or other valid status
                    order.status = OrderStatus.SUBMITTED
                    order.submitted_at = datetime.utcnow()
                    print(f"   ✅ Order SUBMITTED at {order.submitted_at}")
            except Exception as e:
                order.status = OrderStatus.REJECTED
                order.rejection_reason = str(e)
                print(f"   ❌ Broker submission exception: {e}")
        else:
            print(f"   ⚠️  No broker - simulating submission")
            # No broker - simulate submission
            order.status = OrderStatus.SUBMITTED
            order.submitted_at = datetime.utcnow()
        
        # Store in database
        print(f"   💾 Saving to database...")
        self._save_order_to_db(order, user_id)
        print(f"   ✅ Saved to database")
        
        # Cache order
        order_id = order.broker_order_id or f"local_{len(self.orders)}"
        self.orders[order_id] = order
        print(f"   📝 Cached order with ID: {order_id}")
        
        print(f"✅ OMS.create_order returning: status={order.status.value}, broker_id={order.broker_order_id}")
        return order
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        order = self.orders.get(order_id)
        if not order:
            return False
        
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
            return False
        
        # Cancel with broker
        if self.broker and order.broker_order_id:
            try:
                self.broker.cancel_order(order.broker_order_id)
            except Exception as e:
                print(f"Broker cancellation failed: {e}")
        
        order.status = OrderStatus.CANCELLED
        self._update_order_in_db(order)
        
        return True
    
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get current order status"""
        order = self.orders.get(order_id)
        
        # Update from broker if available
        if self.broker and order and order.broker_order_id:
            try:
                broker_status = self.broker.get_order_status(order.broker_order_id)
                order.status = OrderStatus(broker_status.get('status', order.status.value))
                order.filled_quantity = broker_status.get('filled_quantity', order.filled_quantity)
                order.average_fill_price = broker_status.get('average_fill_price', order.average_fill_price)
                
                if order.status == OrderStatus.FILLED:
                    order.filled_at = datetime.utcnow()
                
                self._update_order_in_db(order)
            except Exception as e:
                print(f"Failed to fetch order status: {e}")
        
        return order
    
    def _validate_order(self, order: Order) -> bool:
        """Validate order parameters"""
        if order.quantity <= 0:
            return False
        
        if order.order_type == OrderType.LIMIT and not order.price:
            return False
        
        if order.order_type == OrderType.STOP and not order.stop_price:
            return False
        
        if order.side not in ['BUY', 'SELL']:
            return False
        
        return True
    
    def _pre_trade_checks(self, order: Order, user_id: int) -> bool:
        """Pre-trade risk and compliance checks"""
        # TODO: Implement comprehensive pre-trade checks
        # - Position limits
        # - VaR limits
        # - Liquidity checks
        # - Compliance rules
        
        return True
    
    def _save_order_to_db(self, order: Order, user_id: int):
        """Save order to database"""
        trade = Trade(
            user_id=user_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=order.price or 0.0,
            order_type=order.order_type.value,
            status=order.status.value,
            broker_order_id=order.broker_order_id,
            execution_time=order.filled_at
        )
        
        self.db.add(trade)
        self.db.commit()
    
    def _update_order_in_db(self, order: Order):
        """Update order in database"""
        if order.broker_order_id:
            trade = self.db.query(Trade).filter(
                Trade.broker_order_id == order.broker_order_id
            ).first()
            
            if trade:
                trade.status = order.status.value
                trade.execution_time = order.filled_at
                self.db.commit()
