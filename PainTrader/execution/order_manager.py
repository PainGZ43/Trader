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
            # 1: Buy, 2: Sell
            trade_type = "1" if signal.type == "BUY" else "2"
            quote_type = "00" # Limit
            price = int(signal.price)
            
            if price <= 0:
                quote_type = "03" # Market
                price = 0
            
            result = await self.kiwoom.send_order(
                signal.symbol, int(trade_type), quantity, price, quote_type
            )
            
            if result and result.get("rt_cd") == "0":
                order_no = result.get("output", {}).get("order_no")
                if order_no:
                    self.logger.info(f"Order Sent: {signal.type} {signal.symbol} {quantity} @ {price} (ID: {order_no})")
                    # Register immediately to track source
                    self.active_orders[order_no] = {
                        'symbol': signal.symbol,
                        'type': signal.type,
                        'quantity': quantity,
                        'filled_qty': 0,
                        'price': price,
                        'source': 'STRATEGY',
                        'timestamp': datetime.now()
                    }
                    return order_no
            
            self.logger.error(f"Order Send Failed: {result}")
            return None
                
        except Exception as e:
            self.logger.error(f"Order Send Exception: {e}")
            return None

    async def send_manual_order(self, symbol: str, order_type: str, price: int, quantity: int) -> Optional[str]:
        """
        Send a manual order from UI.
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
            
            if result and result.get("rt_cd") == "0":
                order_no = result.get("output", {}).get("order_no")
                if order_no:
                    self.active_orders[order_no] = {
                        'symbol': symbol,
                        'type': order_type,
                        'quantity': quantity,
                        'filled_qty': 0,
                        'price': price,
                        'source': 'MANUAL',
                        'timestamp': datetime.now()
                    }
                    return order_no
            
            self.logger.error(f"Manual Order Failed: {result}")
            return None
        except Exception as e:
            self.logger.error(f"Manual Order Exception: {e}")
            return None

    async def modify_order(self, order_id: str, price: int, quantity: int):
        """
        Modify an existing order (Price/Qty).
        """
        try:
            order_info = self.active_orders.get(order_id)
            if not order_info:
                self.logger.warning(f"Cannot modify unknown order {order_id}")
                return False

            symbol = order_info['symbol']
            is_buy = order_info['type'] == 'BUY'
            
            # Kiwoom Modify Types: 5 (Buy Modify), 6 (Sell Modify)
            modify_type = 5 if is_buy else 6
            
            self.logger.info(f"Modifying Order {order_id}: {quantity} @ {price}")
            
            # org_order_no is required
            result = await self.kiwoom.send_order(
                symbol, modify_type, quantity, price, "00", org_order_no=order_id
            )
            
            if result and result.get("rt_cd") == "0":
                # Update local state optimistically or wait for event?
                # Usually modification results in a NEW order number or updates the existing one depending on exchange.
                # Kiwoom usually keeps order_no or issues new one for remaining?
                # Actually for correction, order_no might change or stay.
                # Let's assume it stays for now or we handle the new one in event.
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Modify Order Exception: {e}")
            return False

    async def cancel_order(self, order_id: str, symbol: str):
        """
        Cancel a specific order.
        """
        try:
            self.logger.info(f"Cancelling Order {order_id} ({symbol})")
            
            order_info = self.active_orders.get(order_id)
            qty = 0 # Default to 0 (Cancel All remaining)
            
            if order_info:
                # Cancel remaining quantity
                total_qty = order_info.get('quantity', 0)
                filled_qty = order_info.get('filled_qty', 0)
                qty = total_qty - filled_qty
            
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

        order_ids = list(self.active_orders.keys())
        for oid in order_ids:
            info = self.active_orders[oid]
            await self.cancel_order(oid, info['symbol'])
            
    def on_order_event(self, event_data: Dict[str, Any]):
        """
        Update order status from real-time events.
        Handles Partial Fills.
        """
        order_no = event_data.get('order_no')
        status = event_data.get('status') # ACCEPTED, FILLED, CANCELLED
        
        if not order_no:
            return

        if order_no not in self.active_orders:
            # New order from outside (e.g. HTS)?
            if status == 'ACCEPTED':
                self.active_orders[order_no] = {
                    'symbol': event_data.get('code'),
                    'type': event_data.get('order_type'),
                    'quantity': int(event_data.get('qty', 0)),
                    'filled_qty': 0,
                    'price': float(event_data.get('price', 0)),
                    'source': 'UNKNOWN', # External order
                    'timestamp': datetime.now()
                }
            return

        # Update existing order
        order_info = self.active_orders[order_no]
        
        if status == 'FILLED':
            filled_qty = int(event_data.get('filled_qty', 0)) # This event usually gives *accumulated* or *this execution* qty?
            # Kiwoom 'chejan' data usually gives 'che_qty' (this execution).
            # We need to accumulate.
            # Let's assume event_data['filled_qty'] is the amount filled IN THIS EVENT.
            
            # NOTE: We need to be careful about what 'filled_qty' means in the event passed here.
            # Assuming it's incremental.
            current_fill = int(event_data.get('exec_qty', 0)) # Use 'exec_qty' for incremental
            if current_fill == 0:
                 current_fill = int(event_data.get('qty', 0)) # Fallback if full fill implied
            
            order_info['filled_qty'] += current_fill
            
            remaining = order_info['quantity'] - order_info['filled_qty']
            self.logger.info(f"Order {order_no} Partial Fill: {current_fill} (Rem: {remaining})")
            
            if remaining <= 0:
                self.active_orders.pop(order_no)
                self.logger.info(f"Order {order_no} Fully Filled.")
                
        elif status == 'CANCELLED':
            self.active_orders.pop(order_no)
            self.logger.info(f"Order {order_no} Cancelled.")
