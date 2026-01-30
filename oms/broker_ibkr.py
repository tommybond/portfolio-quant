"""
Interactive Brokers (IBKR) Broker Integration
Handles order submission and management via IBKR TWS/IB Gateway API
Requires ib_insync library and TWS/IB Gateway to be running
"""

from __future__ import annotations

import os
import asyncio
import random
from datetime import datetime
from typing import Dict, List, Optional

# Import OrderType from oms module for type checking
try:
    from oms.oms import OrderType
except ImportError:
    # Fallback if circular import - will be available at runtime
    OrderType = None

# Ensure an asyncio event loop exists for this thread
def _ensure_event_loop():
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

_ib_ready = False
def _import_ib_insync():
    global _ib_ready, IB, Stock, MarketOrder, LimitOrder, StopOrder, StopLimitOrder, util
    if _ib_ready:
        return
    _ensure_event_loop()
    # local import to avoid import-time event-loop side effects
    from ib_insync import IB, Stock, MarketOrder, LimitOrder, StopOrder, StopLimitOrder, util
    _ib_ready = True


class IBKRBroker:
    """Interactive Brokers broker integration — Streamlit/ib_insync safe."""

    def _ensure_event_loop(self):
        """Instance helper that ensures a loop exists for this thread."""
        _ensure_event_loop()

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        client_id: Optional[int] = None,
        username: Optional[str] = None,
        timeout: float = 5.0,
        auto_connect: bool = False,
        *args,
        **kwargs,
    ):
        """
        Initialize IBKR broker without forcing immediate connect.
        - client_id: if None, a random client id is chosen to avoid collisions.
        - auto_connect: if True, will attempt to connect during init.
        """
        # lazy import ib_insync types
        _import_ib_insync()

        self.host = host or os.getenv("IBKR_HOST", "127.0.0.1")
        self.port = int(port or os.getenv("IBKR_PORT", "4002"))
        # choose a random client id when not provided to avoid duplicate-client errors
        if client_id is None:
            # reserve low ids for interactive/manual sessions; pick a high random id
            self.client_id = int(os.getenv("IBKR_CLIENT_ID") or random.randint(2000, 65000))
        else:
            self.client_id = client_id
        self.username = username or os.getenv("IBKR_USERNAME")
        self.timeout = timeout

        # IB instance created here (safe because _import_ib_insync called)
        self.ib = IB()
        self.connected = False
        self._last_connect_error: Optional[Exception] = None

        if auto_connect:
            try:
                self.connect()
            except Exception as e:
                # record error, but do not raise during import-time usage
                self._last_connect_error = e

    def connect(self, timeout: Optional[float] = None, readonly: bool = False) -> bool:
        """Connect to TWS/IB Gateway. Returns True on success."""
        self._ensure_event_loop()
        try:
            if self.ib.isConnected():
                self.connected = True
                return True

            self.ib.connect(
                host=self.host,
                port=self.port,
                clientId=self.client_id,
                timeout=timeout or self.timeout,
                readonly=readonly,
            )
            self.connected = self.ib.isConnected()
            if not self.connected:
                raise ConnectionError(f"Could not connect to IB at {self.host}:{self.port} (clientId={self.client_id})")
            return True
        except Exception as e:
            self.connected = False
            self._last_connect_error = e
            raise

    def disconnect(self):
        """Disconnect the IB session if connected."""
        try:
            if hasattr(self, "ib") and self.ib.isConnected():
                self.ib.disconnect()
            self.connected = False
        except Exception:
            self.connected = False

    def _ensure_connected(self):
        """Ensure an active connection, attempt reconnect if necessary."""
        self._ensure_event_loop()
        if not self.ib.isConnected():
            self.connect()

    def _create_contract(self, symbol: str, exchange: str = 'SMART', currency: str = 'USD'):
        """
        Create a contract for the given symbol.
        For common US stocks, we can use the contract directly without qualification.
        """
        self._ensure_event_loop()
        contract = Stock(symbol, exchange, currency)
        print(f"      Created Stock contract: {contract}")
        
        # Skip qualification for now - IBKR can handle unqualified contracts for most US stocks
        # qualifyContracts can hang in Streamlit environments
        print(f"      ✅ Returning contract (skipping qualification to avoid hang)")
        return contract

    def _convert_order_type(self, order: "Order") -> object:
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

    def submit_order(self, order: "Order") -> Dict:
        """Submit order to IBKR"""
        try:
            print(f"🔵 IBKR submit_order called for {order.symbol} x{order.quantity}")
            self._ensure_event_loop()
            print(f"   Event loop ensured")
            self._ensure_connected()
            print(f"   Connection ensured (connected={self.connected})")

            print(f"   Creating contract for {order.symbol}...")
            contract = self._create_contract(order.symbol)
            print(f"   ✅ Contract created: {contract}")
            
            print(f"   Converting order type {order.order_type}...")
            ib_order = self._convert_order_type(order)
            print(f"   ✅ IB order created: {ib_order}")
            
            ib_order.tif = self._convert_time_in_force(order.time_in_force)
            print(f"   Time in force set to: {ib_order.tif}")

            print(f"   📤 Placing order with IBKR...")
            trade = self.ib.placeOrder(contract, ib_order)
            print(f"   ✅ Order placed! Trade object: {trade}")
            
            # Wait longer for IBKR to process and update order status
            # Inactive -> PreSubmitted/Submitted transition takes time
            self.ib.sleep(1.0)  # Increased from 0.1 to 1.0 seconds

            order_status = trade.orderStatus.status
            print(f"   Order status from IBKR: {order_status}")
            
            result = {
                'order_id': str(trade.order.orderId) if trade.order.orderId else None,
                'status': self._convert_status(order_status),
                'submitted_at': datetime.utcnow().isoformat()
            }
            print(f"   📊 Result: {result}")
            
            # Only treat explicitly cancelled orders as rejected
            # Inactive status means order is pending, not rejected
            if order_status in ['Cancelled', 'ApiCancelled']:
                result['rejection_reason'] = f"Order {order_status}"
                print(f"   ⚠️  Order has rejection status: {order_status}")
            
            print(f"✅ IBKR submit_order returning successfully: {result}")
            return result

        except Exception as e:
            msg = str(e)
            if 'not connected' in msg.lower():
                msg = f"Not connected to TWS/Gateway. {msg}"
            print(f"❌ IBKR submit_order FAILED: {msg}")
            raise Exception(f"IBKR order submission failed: {msg}")

    def cancel_order(self, order_id: str) -> bool:
        """Cancel order"""
        try:
            self._ensure_event_loop()
            self._ensure_connected()

            for trade in self.ib.openTrades():
                if str(trade.order.orderId) == str(order_id):
                    self.ib.cancelOrder(trade.order)
                    return True

            return False

        except Exception as e:
            print(f"Failed to cancel order {order_id}: {e}")
            return False

    def get_order_status(self, order_id: str) -> Dict:
        """Get order status from IBKR"""
        try:
            self._ensure_event_loop()
            self._ensure_connected()

            # Check open trades
            for trade in self.ib.openTrades():
                if str(trade.order.orderId) == str(order_id):
                    status = trade.orderStatus
                    return {
                        'status': self._convert_status(status.status),
                        'filled_quantity': int(status.filled),
                        'average_fill_price': float(status.avgFillPrice) if status.avgFillPrice else None,
                        'remaining_quantity': int(status.remaining) if hasattr(status, 'remaining') else None
                    }
            
            # Check filled trades
            try:
                for trade in self.ib.trades():
                    if str(trade.order.orderId) == str(order_id):
                        status = trade.orderStatus
                        return {
                            'status': self._convert_status(status.status),
                            'filled_quantity': int(status.filled),
                            'average_fill_price': float(status.avgFillPrice) if status.avgFillPrice else None,
                            'remaining_quantity': int(status.remaining) if hasattr(status, 'remaining') else None
                        }
            except Exception:
                pass  # trades() may not be available

            return {'status': 'NOT_FOUND'}

        except Exception as e:
            print(f"Failed to get order status: {e}")
            return {}

    def _convert_status(self, ib_status: str) -> str:
        """Convert IBKR order status to OMS standard status"""
        status_map = {
            'PendingSubmit': 'PENDING',
            'PendingCancel': 'PENDING',
            'PreSubmitted': 'PENDING',
            'Submitted': 'SUBMITTED',
            'ApiPending': 'PENDING',
            'ApiCancelled': 'CANCELLED',
            'Cancelled': 'CANCELLED',
            'Filled': 'FILLED',
            'Inactive': 'PENDING',  # Orders often start as Inactive before being Submitted
        }
        return status_map.get(ib_status, ib_status.upper())

    def _get_default_account(self) -> Optional[str]:
        """Return a default managed account or None."""
        try:
            self._ensure_event_loop()
            accounts = self.ib.managedAccounts()
            return accounts[0] if accounts else None
        except Exception:
            return None

    def get_positions(self, account_id: Optional[str] = None) -> List[Dict]:
        """Get current positions (optionally filtered by account)"""
        try:
            self._ensure_event_loop()
            self._ensure_connected()

            account_id = account_id or self._get_default_account()

            positions = []
            for position in self.ib.positions():
                # If an account was specified, skip positions from other accounts
                pos_account = getattr(position, "account", None)
                if account_id and pos_account and pos_account != account_id:
                    continue

                if position.position != 0:  # Only non-zero positions
                    # Get contract details
                    contract = position.contract

                    # Get current market price with NaN checking
                    import math
                    ticker = self.ib.reqMktData(contract, '', False, False)
                    self.ib.sleep(0.5)  # Wait for market data
                    
                    # Check for valid price (not NaN, not None, greater than 0)
                    market_price = ticker.marketPrice()
                    if market_price and not math.isnan(market_price) and market_price > 0:
                        current_price = float(market_price)
                    else:
                        # Try other price sources
                        if ticker.last and not math.isnan(ticker.last) and ticker.last > 0:
                            current_price = float(ticker.last)
                        elif ticker.close and not math.isnan(ticker.close) and ticker.close > 0:
                            current_price = float(ticker.close)
                        else:
                            current_price = 0.0
                    
                    # Clean up market data subscription
                    self.ib.cancelMktData(contract)

                    positions.append({
                        'symbol': contract.symbol,
                        'quantity': int(position.position),
                        'average_price': float(position.avgCost) if position.avgCost else 0.0,
                        'current_price': current_price,
                        'unrealized_pnl': float(position.unrealizedPNL) if hasattr(position, 'unrealizedPNL') else 0.0,
                        'market_value': abs(float(position.position) * current_price) if current_price else 0.0,
                        'account': pos_account
                    })

            return positions

        except Exception as e:
            error_msg = str(e)
            if 'event loop' in error_msg.lower() or 'no current event loop' in error_msg.lower():
                print(f"⚠️ Event loop issue: {e}. Try restarting the app.")
            else:
                print(f"Failed to get positions: {e}")
            return []

    def get_current_price(self, symbol: str, exchange: str = 'SMART', currency: str = 'USD') -> Optional[Dict]:
        """Get current price for a symbol (works even without position)
        
        Returns dict with 'price', 'bid', 'ask', 'last' or None if unavailable
        
        Note: Paper trading accounts may not have realtime market data subscriptions.
        This method will return None if no data is available, allowing fallback to yfinance.
        """
        try:
            self._ensure_event_loop()
            self._ensure_connected()
            
            # Create and qualify contract
            contract = Stock(symbol, exchange, currency)
            
            # Try to get delayed or real-time market data
            # Using snapshot=True for delayed data if real-time unavailable
            ticker = self.ib.reqMktData(contract, '', True, False)
            self.ib.sleep(2.0)  # Wait longer for market data to arrive
            
            # Debug: check what we received
            print(f"🔍 IBKR data for {symbol}: bid={ticker.bid}, ask={ticker.ask}, last={ticker.last}, close={ticker.close}")
            
            # Try to get best available price
            price_data = {}
            
            # Check for valid (non-NaN, non-None) values
            import math
            
            # Helper function to check if value is valid
            def is_valid_price(value):
                return value is not None and not math.isnan(value) and value > 0
            
            if is_valid_price(ticker.bid):
                price_data['bid'] = float(ticker.bid)
            if is_valid_price(ticker.ask):
                price_data['ask'] = float(ticker.ask)
            if is_valid_price(ticker.last):
                price_data['last'] = float(ticker.last)
            if is_valid_price(ticker.close):
                price_data['close'] = float(ticker.close)
            
            # Calculate price from available data
            if 'bid' in price_data and 'ask' in price_data:
                # Best case: use bid/ask midpoint
                price_data['price'] = (price_data['bid'] + price_data['ask']) / 2.0
            elif 'last' in price_data:
                # Use last trade price
                price_data['price'] = price_data['last']
            elif 'close' in price_data:
                # Use previous close
                price_data['price'] = price_data['close']
            else:
                # Try marketPrice() as last resort
                market_price = ticker.marketPrice()
                if is_valid_price(market_price):
                    price_data['price'] = float(market_price)
                else:
                    print(f"⚠️ No valid price data for {symbol} - IBKR may require market data subscription")
                    print(f"   This is common with Paper Trading accounts. Will fall back to yfinance.")
                    # Cancel subscription before returning None
                    self.ib.cancelMktData(contract)
                    return None
            
            # Cancel market data subscription to clean up
            self.ib.cancelMktData(contract)
            
            return price_data if price_data else None
            
        except Exception as e:
            print(f"❌ Failed to get current price for {symbol}: {e}")
            return None

    def get_account_info(self, account_id: Optional[str] = None) -> Dict:
        """Get account information (optionally for a specific account)"""
        try:
            self._ensure_event_loop()
            self._ensure_connected()

            account_id = account_id or self._get_default_account()

            # Get account values (may include multiple accounts)
            account_values = self.ib.accountValues()

            # Extract key values
            info = {}
            NUMERIC_FIELDS = {
                "BuyingPower",
                "CashBalance",
                "NetLiquidation",
                "TotalCashValue",
                "GrossPositionValue",
                "AvailableFunds",
            }
            for av in account_values:
                # Skip other accounts when filtering
                if account_id and getattr(av, "account", None) and av.account != account_id:
                    continue

                tag = av.tag
                raw_value = av.value
                if tag in NUMERIC_FIELDS:
                    try:
                        value = float(raw_value) if raw_value not in (None, "") else 0.0
                    except Exception:
                        value = 0.0
                else:
                    value = raw_value  # keep as string for non-numeric fields

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

            info.setdefault('buying_power', 0.0)
            info.setdefault('cash', 0.0)
            info.setdefault('equity', 0.0)
            info.setdefault('portfolio_value', 0.0)

            # include account id in result when available
            if account_id:
                info['account'] = account_id
            else:
                default_acc = self._get_default_account()
                if default_acc:
                    info['account'] = default_acc

            return info

        except Exception as e:
            error_msg = str(e)
            if 'event loop' in error_msg.lower() or 'no current event loop' in error_msg.lower():
                print(f"⚠️ Event loop issue: {e}. Try restarting the app.")
            else:
                print(f"Failed to get account info: {e}")
            return {}

    def __del__(self):
        """Cleanup on deletion"""
        try:
            if hasattr(self, 'ib') and self.ib.isConnected():
                self.ib.disconnect()
        except Exception:
            pass
