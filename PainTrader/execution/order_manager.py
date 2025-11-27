import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from strategy.base_strategy import Signal
from data.kiwoom_rest_client import KiwoomRestClient
from core.logger import get_logger

class OrderManager:
    """
    Manages order lifecycle: Send, Monitor, Cancel/Modify.
    """
    def __init__(self, kiwoom: KiwoomRestClient):
        self.logger = get_logger("OrderManager")
        self.kiwoom = kiwoom
        self.active_orders: Dict[str, Dict[str, Any]] = {} # order_id -> order_info
        self.unfilled_check_interval = 5 # seconds
        self.max_unfilled_time = 60 # seconds

    async def send_order(self, signal: Signal, quantity: int, account_num: str) -> Optional[str]:
        """
        Send order to Kiwoom.
        """
        try:
            # Convert Signal type to Kiwoom type
            # 1: Buy, 2: Sell
            trade_type = "1" if signal.type == "BUY" else "2"
            
            # Price: If 0, use Market Order ("03"), else Limit Order ("00")
            # For simplicity, we use Limit Order at signal price if provided, else Market
            # But usually we want Limit Order.
            quote_type = "00" # Limit
            price = int(signal.price)
            
            if price <= 0:
                quote_type = "03" # Market
                price = 0
            
            # Call API
            # KiwoomRestClient.send_order(symbol, order_type, qty, price, trade_type)
            # Note: account_num is handled internally by KiwoomRestClient via KeyManager for now.
            # For PaperExchange, it uses its internal account.
            
            result = await self.kiwoom.send_order(
                signal.symbol, int(trade_type), quantity, price, quote_type
            )
            
            # Result usually contains order_no if successful?
            # Kiwoom returns 0 for success, but order_no comes via event.
            # For REST API, we might get it in response.
            # Let's assume result is a dict with status.
            
            if result and result.get("result_code") == 0:
                # We don't have order_id yet until event comes.
                # But we can track it temporarily?
                # In real Kiwoom, we wait for OnReceiveTrData or OnReceiveChejan.
                self.logger.info(f"Order Sent: {signal.type} {signal.symbol} {quantity} @ {price}")
                return "PENDING"
            else:
                self.logger.error(f"Order Send Failed: {result}")
                return None
                
        except Exception as e:
            self.logger.error(f"Order Send Exception: {e}")
            return None

    async def monitor_unfilled_orders(self):
        """
        Background task to monitor unfilled orders.
        """
        while True:
            try:
                now = datetime.now()
                to_remove = []
                
                for order_id, info in self.active_orders.items():
                    sent_time = info['timestamp']
                    if (now - sent_time).total_seconds() > self.max_unfilled_time:
                        # Cancel or Correct
                        self.logger.info(f"Order {order_id} unfilled for too long. Cancelling...")
                        await self.cancel_order(order_id, info['symbol'])
                        to_remove.append(order_id)
                
                for oid in to_remove:
                    self.active_orders.pop(oid, None)
                    
                await asyncio.sleep(self.unfilled_check_interval)
            except Exception as e:
                self.logger.error(f"Monitor Error: {e}")
                await asyncio.sleep(5)

    async def send_manual_order(self, symbol: str, order_type: str, price: int, quantity: int) -> Optional[str]:
        """
        Send a manual order from UI.
        order_type: 'BUY' or 'SELL'
        """
        try:
            trade_type = "1" if order_type == "BUY" else "2"
            quote_type = "00" # Limit
            
            if price <= 0:
                quote_type = "03" # Market
                price = 0
                
            self.logger.info(f"Manual Order: {order_type} {symbol} {quantity} @ {price}")
            
            result = await self.kiwoom.send_order(
                symbol, int(trade_type), quantity, price, quote_type
            )
            
            if result and result.get("result_code") == 0:
                return "PENDING"
            else:
                self.logger.error(f"Manual Order Failed: {result}")
                return None
        except Exception as e:
            self.logger.error(f"Manual Order Exception: {e}")
            return None

    async def cancel_order(self, order_id: str, symbol: str):
        """
        Cancel a specific order.
        """
        try:
            self.logger.info(f"Cancelling Order {order_id} ({symbol})")
            
            # Use KiwoomRestClient's dedicated cancel_order method
            # We need quantity to cancel. If not tracked, maybe cancel all (0)?
            # Kiwoom usually requires qty.
            
            order_info = self.active_orders.get(order_id)
            qty = 0 # Default to 0 (Cancel All remaining)
            
            if order_info:
                # If we track quantity in active_orders, use it.
                # Currently active_orders stores: symbol, type, timestamp.
                # We should probably store quantity too.
                qty = order_info.get('quantity', 0)
            
            # Call KiwoomRestClient.cancel_order(order_no, symbol, qty)
            await self.kiwoom.cancel_order(order_id, symbol, qty)
            
        except Exception as e:
            self.logger.error(f"Cancel Order Exception: {e}")

    async def cancel_all_orders(self):
        """
        Cancel all active orders.
        """
        self.logger.warning("Cancelling ALL active orders...")
        if not self.active_orders:
            self.logger.info("No active orders to cancel.")
            return

        # Create a copy of keys to iterate safely
        order_ids = list(self.active_orders.keys())
        for oid in order_ids:
            info = self.active_orders[oid]
            await self.cancel_order(oid, info['symbol'])
            
    def on_order_event(self, event_data: Dict[str, Any]):
        """
        Update order status from real-time events.
        """
        # Example event_data: {'order_no': '123', 'status': 'FILLED', ...}
        order_no = event_data.get('order_no')
        status = event_data.get('status')
        
        if order_no and status:
            if status == 'FILLED' or status == 'CANCELLED':
                if order_no in self.active_orders:
                    self.active_orders.pop(order_no)
                    self.logger.info(f"Order {order_no} removed from active list ({status})")
            elif status == 'ACCEPTED':
                # Add to active orders if not exists
                if order_no not in self.active_orders:
                    self.active_orders[order_no] = {
                        'symbol': event_data.get('code'),
                        'type': event_data.get('order_type'), # BUY/SELL
                        'quantity': int(event_data.get('qty', 0)),
                        'timestamp': datetime.now()
                    }
