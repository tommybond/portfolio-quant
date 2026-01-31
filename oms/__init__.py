"""
Order Management System (OMS)
Handles order creation, routing, and execution
"""

from .oms import OrderManager, Order, OrderStatus, OrderType
from .broker_alpaca import AlpacaBroker
# removed: from .broker_ibkr import IBKRBroker   # avoid import-time ib_insync/eventkit side effects

# Lazily create IBKRBroker to avoid importing ib_insync at module import time
def get_ibkr_broker(*args, **kwargs):
    from .broker_ibkr import IBKRBroker
    return IBKRBroker(*args, **kwargs)

__all__ = [
    "get_ibkr_broker",
    "OrderManager", "Order", "OrderStatus", "OrderType",
]
