"""
Interactive Brokers (IBKR) Broker Integration
Handles order submission and management via IBKR TWS/IB Gateway API
Requires ib_insync library and TWS/IB Gateway to be running
"""

import os
import asyncio
import threading
from typing import Dict, Optional, List
from datetime import datetime
from .oms import Order, OrderStatus, OrderType

try:
    from ib_insync import IB, MarketOrder, LimitOrder, StopOrder, StopLimitOrder, util
    from ib_insync.contract import Stock
    IBKR_AVAILABLE = True
except ImportError:
    IBKR_AVAILABLE = False
    Stock = None  # For type hints when not available


class IBKRBroker:
    """Interactive Brokers broker integration"""
    
    def __init__(self, host: str = None, port: int = None, client_id: int = None):
        """
        Initialize IBKR connection
        
        Args:
            host: TWS/IB Gateway host (default: 127.0.0.1)
            port: TWS/IB Gateway port (default: 7497 for paper, 7496 for live)
            client_id: Client ID (default: 1)
        """
        if not IBKR_AVAILABLE:
            raise ImportError("ib_insync not installed. Install with: pip install ib_insync")
        
        self.host = host or os.getenv('IBKR_HOST', '127.0.0.1')
        self.port = port or int(os.getenv('IBKR_PORT', '7497'))  # 7497 = paper, 7496 = live
        self.client_id = client_id or int(os.getenv('IBKR_CLIENT_ID', '1'))
        
        # Initialize IB instance
        self.ib = IB()
        self._connected = False
        self._loop_started = False
        
        # Start event loop for this thread (required for ib-insync in Streamlit)
        self._ensure_event_loop()
        
        # Connect to TWS/IB Gateway (lazy connection - only when needed)
        # Don't connect in __init__ to avoid blocking Streamlit
    
    def _ensure_event_loop(self):
        """Ensure event loop exists in current thread"""
        try:
            # Try to get current event loop
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            # No event loop in this thread - create one
            try:
                # Start the event loop in a separate thread
                if not self._loop_started:
                    util.startLoop()  # This starts the event loop for ib-insync
                    self._loop_started = True
            except Exception as e:
                # If startLoop fails, try creating a new event loop
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    # Start loop in background thread
                    def run_loop():
                        asyncio.set_event_loop(loop)
                        loop.run_forever()
                    thread = threading.Thread(target=run_loop, daemon=True)
                    thread.start()
                    self._loop_started = True
                except Exception as e2:
                    print(f"Warning: Could not start event loop: {e2}")
    
    def _connect(self):
        """Connect to TWS/IB Gateway"""
        try:
            # Ensure event loop is running
            self._ensure_event_loop()
            
            if not self.ib.isConnected():
                # Use run() wrapper for async operations
                self.ib.connect(
                    host=self.host,
                    port=self.port,
                    clientId=self.client_id,
                    readonly=False
                )
                self._connected = True
                print(f"✅ Connected to IBKR TWS/Gateway at {self.host}:{self.port}")
        except Exception as e:
            self._connected = False
            error_msg = (
                f"Failed to connect to IBKR TWS/Gateway at {self.host}:{self.port}. "
                f"Make sure TWS or IB Gateway is running and API connections are enabled. "
                f"Error: {str(e)}"
            )
            # Don't raise immediately - allow lazy connection
            print(f"⚠️ {error_msg}")
            raise ConnectionError(error_msg)
    
    def _ensure_connected(self):
        """Ensure connection is active, reconnect if needed"""
        try:
            # Ensure event loop is running
            self._ensure_event_loop()
            
            if not self.ib.isConnected():
                self._connect()
        except Exception as e:
            print(f"Connection check failed: {e}")
            raise
    
    def _create_contract(self, symbol: str, exchange: str = 'SMART', currency: str = 'USD'):
        """
        Create IBKR contract from symbol
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            exchange: Exchange (default: 'SMART' for smart routing)
            currency: Currency (default: 'USD')
        """
        # Ensure event loop is running
        self._ensure_event_loop()
        
        contract = Stock(symbol, exchange, currency)
        # Qualify contract to get full details
        qualified = self.ib.qualifyContracts(contract)
        if qualified:
            return qualified[0]
        return contract
    
    def _convert_order_type(self, order: Order) -> object:
        """
        Convert Order to IBKR order type
        
        Args:
            order: Order object
            
        Returns:
            IBKR order object (MarketOrder, LimitOrder, etc.)
        """
        quantity = order.quantity
        if order.side.upper() == 'SELL':
            quantity = -abs(quantity)  # Negative for sell
        
        if order.order_type == OrderType.MARKET:
            return MarketOrder('BUY' if quantity > 0 else 'SELL', abs(quantity))
        
        elif order.order_type == OrderType.LIMIT:
            if not order.price:
                raise ValueError("Limit order requires price")
            return LimitOrder('BUY' if quantity > 0 else 'SELL', abs(quantity), order.price)
        
        elif order.order_type == OrderType.STOP:
            if not order.stop_price:
                raise ValueError("Stop order requires stop_price")
            return StopOrder('BUY' if quantity > 0 else 'SELL', abs(quantity), order.stop_price)
        
        elif order.order_type == OrderType.STOP_LIMIT:
            if not order.stop_price or not order.price:
                raise ValueError("Stop-limit order requires both stop_price and price")
            return StopLimitOrder('BUY' if quantity > 0 else 'SELL', abs(quantity), order.price, order.stop_price)
        
        else:
            # Default to market order
            return MarketOrder('BUY' if quantity > 0 else 'SELL', abs(quantity))
    
    def _convert_time_in_force(self, tif: str) -> str:
        """Convert time_in_force to IBKR format"""
        mapping = {
            'DAY': 'DAY',
            'GTC': 'GTC',  # Good Till Cancel
            'IOC': 'IOC',  # Immediate or Cancel
            'FOK': 'FOK'   # Fill or Kill
        }
        return mapping.get(tif.upper(), 'DAY')
    
    def submit_order(self, order: Order) -> Dict:
        """Submit order to IBKR"""
        try:
            # Ensure event loop is running
            self._ensure_event_loop()
            self._ensure_connected()
            
            # Create contract
            contract = self._create_contract(order.symbol)
            
            # Create IBKR order
            ib_order = self._convert_order_type(order)
            ib_order.tif = self._convert_time_in_force(order.time_in_force)
            
            # Place order
            trade = self.ib.placeOrder(contract, ib_order)
            
            # Wait for order acknowledgment (non-blocking check)
            # Note: In production, you might want to use async/await for better handling
            self.ib.sleep(0.1)  # Brief wait for order acknowledgment
            
            # Get order status
            order_status = trade.orderStatus.status
            
            result = {
                'order_id': str(trade.order.orderId) if trade.order.orderId else None,
                'status': self._convert_status(order_status),
                'submitted_at': datetime.utcnow().isoformat()
            }
            
            # Check for rejection
            if order_status in ['Cancelled', 'Inactive', 'ApiCancelled']:
                result['rejection_reason'] = f"Order {order_status}"
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            # Provide more context for common errors
            if 'not connected' in error_msg.lower():
                error_msg = f"Not connected to TWS/Gateway. {error_msg}"
            elif 'contract' in error_msg.lower():
                error_msg = f"Invalid contract for symbol {order.symbol}. {error_msg}"
            elif 'event loop' in error_msg.lower() or 'no current event loop' in error_msg.lower():
                error_msg = f"Event loop issue. Try restarting the app. {error_msg}"
            
            raise Exception(f"IBKR order submission failed: {error_msg}")
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel order"""
        try:
            # Ensure event loop is running
            self._ensure_event_loop()
            self._ensure_connected()
            
            # Find the trade by order ID
            for trade in self.ib.openTrades():
                if str(trade.order.orderId) == str(order_id):
                    self.ib.cancelOrder(trade.order)
                    return True
            
            # If not found in open trades, try to cancel by order ID
            # Note: This is a simplified approach. In production, you'd track orders better
            print(f"Order {order_id} not found in open trades")
            return False
            
        except Exception as e:
            print(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get order status from IBKR"""
        try:
            # Ensure event loop is running
            self._ensure_event_loop()
            self._ensure_connected()
            
            # Find the trade by order ID
            for trade in self.ib.openTrades() + self.ib.filledOrders():
                if str(trade.order.orderId) == str(order_id):
                    status = trade.orderStatus
                    return {
                        'status': self._convert_status(status.status),
                        'filled_quantity': int(status.filled),
                        'average_fill_price': float(status.avgFillPrice) if status.avgFillPrice else None,
                        'remaining_quantity': int(status.remaining) if hasattr(status, 'remaining') else None
                    }
            
            return {'status': 'NOT_FOUND'}
            
        except Exception as e:
            print(f"Failed to get order status: {e}")
            return {}
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        try:
            # Ensure event loop is running
            self._ensure_event_loop()
            self._ensure_connected()
            
            positions = []
            for position in self.ib.positions():
                if position.position != 0:  # Only non-zero positions
                    # Get contract details
                    contract = position.contract
                    
                    # Get current market price
                    ticker = self.ib.reqMktData(contract, '', False, False)
                    self.ib.sleep(0.5)  # Wait for market data
                    current_price = ticker.marketPrice() if ticker.marketPrice() else 0.0
                    
                    positions.append({
                        'symbol': contract.symbol,
                        'quantity': int(position.position),
                        'average_price': float(position.avgCost) if position.avgCost else 0.0,
                        'current_price': current_price,
                        'unrealized_pnl': float(position.unrealizedPNL) if hasattr(position, 'unrealizedPNL') else 0.0,
                        'market_value': abs(float(position.position) * current_price) if current_price else 0.0
                    })
            
            return positions
            
        except Exception as e:
            error_msg = str(e)
            if 'event loop' in error_msg.lower() or 'no current event loop' in error_msg.lower():
                print(f"⚠️ Event loop issue: {e}. Try restarting the app.")
            else:
                print(f"Failed to get positions: {e}")
            return []
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        try:
            # Ensure event loop is running
            self._ensure_event_loop()
            self._ensure_connected()
            
            # Get account values
            account_values = self.ib.accountValues()
            
            # Extract key values
            info = {}
            for av in account_values:
                tag = av.tag
                value = float(av.value) if av.value else 0.0
                
                if tag == 'BuyingPower':
                    info['buying_power'] = value
                elif tag == 'CashBalance':
                    info['cash'] = value
                elif tag == 'NetLiquidation':
                    info['equity'] = value
                elif tag == 'TotalCashValue':
                    info['total_cash'] = value
                elif tag == 'GrossPositionValue':
                    info['portfolio_value'] = value
            
            # Set defaults if not found
            info.setdefault('buying_power', 0.0)
            info.setdefault('cash', 0.0)
            info.setdefault('equity', 0.0)
            info.setdefault('portfolio_value', 0.0)
            
            return info
            
        except Exception as e:
            error_msg = str(e)
            if 'event loop' in error_msg.lower() or 'no current event loop' in error_msg.lower():
                print(f"⚠️ Event loop issue: {e}. Try restarting the app.")
            else:
                print(f"Failed to get account info: {e}")
            return {}
    
    def disconnect(self):
        """Disconnect from TWS/IB Gateway"""
        try:
            if self.ib.isConnected():
                self.ib.disconnect()
                self._connected = False
                print("Disconnected from IBKR")
        except Exception as e:
            print(f"Error disconnecting: {e}")
    
    def _convert_status(self, ibkr_status: str) -> str:
        """Convert IBKR status to OrderStatus"""
        mapping = {
            'ApiPending': OrderStatus.PENDING.value,
            'PendingSubmit': OrderStatus.PENDING.value,
            'PendingCancel': OrderStatus.PENDING.value,
            'PreSubmitted': OrderStatus.SUBMITTED.value,
            'Submitted': OrderStatus.SUBMITTED.value,
            'Filled': OrderStatus.FILLED.value,
            'PartiallyFilled': OrderStatus.PARTIALLY_FILLED.value,
            'Cancelled': OrderStatus.CANCELLED.value,
            'ApiCancelled': OrderStatus.CANCELLED.value,
            'Inactive': OrderStatus.REJECTED.value
        }
        return mapping.get(ibkr_status, OrderStatus.PENDING.value)
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            if hasattr(self, 'ib') and self.ib.isConnected():
                self.ib.disconnect()
        except:
            pass
