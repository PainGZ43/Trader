import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from strategy.base_strategy import Signal
from data.kiwoom_rest_client import KiwoomRestClient
from core.logger import get_logger
from core.database import db
from core.event_bus import event_bus

class OrderManager:
    """
    Manages order lifecycle: Send, Monitor, Cancel/Modify.
    """
    def __init__(self, kiwoom: KiwoomRestClient, notification_manager=None):
        self.logger = get_logger("OrderManager")
        self.kiwoom = kiwoom
        self.notification = notification_manager
        self.active_orders: Dict[str, Dict[str, Any]] = {} # order_id -> order_info
        self.unfilled_check_interval = 5 # seconds
        self.max_unfilled_time = 60 # seconds

    async def initialize(self):
        """
        Initialize DB table and load active orders.
        """
        await db.execute("""
            CREATE TABLE IF NOT EXISTS active_orders (
                order_id TEXT PRIMARY KEY,
                symbol TEXT,
                type TEXT,
                quantity INTEGER,
                filled_qty INTEGER,
                price REAL,
                source TEXT,
                timestamp DATETIME,
                strategy_id TEXT
            )
        """)
        
        # Migration: Add strategy_id column if not exists
        try:
            # Check if column exists
            columns = await db.fetch_all("PRAGMA table_info(active_orders)")
            has_strategy_id = any(col['name'] == 'strategy_id' for col in columns)
            
            if not has_strategy_id:
                await db.execute("ALTER TABLE active_orders ADD COLUMN strategy_id TEXT")
                self.logger.info("Migrated active_orders table: Added strategy_id column")
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            
        await self.load_active_orders()

    async def load_active_orders(self):
        """Load active orders from DB."""
        # Check columns to handle legacy schema if needed, but we did migration above.
        # We need to select all columns.
        rows = await db.fetch_all("SELECT * FROM active_orders")
        for row in rows:
            # row: order_id, symbol, type, quantity, filled_qty, price, source, timestamp, strategy_id
            order_id = row[0]
            self.active_orders[order_id] = {
                'symbol': row[1],
                'type': row[2],
                'quantity': row[3],
                'filled_qty': row[4],
                'price': row[5],
                'source': row[6],
                'timestamp': row[7],
                'strategy_id': row[8] if len(row) > 8 else None
            }
        self.logger.info(f"Loaded {len(self.active_orders)} active orders from DB.")

    async def save_order(self, order_id: str, info: Dict[str, Any]):
        """Save order to DB."""
        query = """
            INSERT OR REPLACE INTO active_orders 
            (order_id, symbol, type, quantity, filled_qty, price, source, timestamp, strategy_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        await db.execute(query, (
            order_id, info['symbol'], info['type'], info['quantity'], 
            info['filled_qty'], info['price'], info['source'], info['timestamp'],
            info.get('strategy_id')
        ))

    async def remove_order(self, order_id: str):
        """Remove order from DB."""
        await db.execute("DELETE FROM active_orders WHERE order_id = ?", (order_id,))

    async def send_order(self, signal: Signal, quantity: int, account_num: str, extra_data: Dict[str, Any] = None) -> Optional[str]:
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
                    order_info = {
                        'symbol': signal.symbol,
                        'type': signal.type,
                        'quantity': quantity,
                        'filled_qty': 0,
                        'price': price,
                        'source': 'STRATEGY',
                        'timestamp': datetime.now(),
                        'strategy_id': extra_data.get('strategy_id') if extra_data else None
                    }
                    self.active_orders[order_no] = order_info
                    await self.save_order(order_no, order_info)
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
                    order_info = {
                        'symbol': symbol,
                        'type': order_type,
                        'quantity': quantity,
                        'filled_qty': 0,
                        'price': price,
                        'source': 'MANUAL',
                        'timestamp': datetime.now(),
                        'strategy_id': None
                    }
                    self.active_orders[order_no] = order_info
                    await self.save_order(order_no, order_info)
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
        else:
            order_ids = list(self.active_orders.keys())
            for oid in order_ids:
                info = self.active_orders[oid]
                await self.cancel_order(oid, info['symbol'])
                await asyncio.sleep(0.5) # Prevent burst rate limit
            
    async def close_all_positions(self):
        """
        Liquidate all holding positions (Panic Sell).
        """
        self.logger.warning("CLOSING ALL POSITIONS (Panic Liquidation)...")
        try:
            # 1. Get Balance/Positions
            balance = await self.kiwoom.get_account_balance()
            if not balance:
                self.logger.error("Failed to get balance for liquidation.")
                return

            # Parse positions
            # Output format depends on KiwoomRestClient implementation (mock/real)
            # Based on mock: {'output': {'multi': [{'code': '...', 'qty': '...'}]}}
            positions = []
            output = balance.get('output', {})
            if 'multi' in output:
                positions = output['multi']
            elif 'single' in output: # Sometimes single list?
                pass 
            
            # 2. Sell Each
            for pos in positions:
                symbol = pos.get('code')
                qty = int(pos.get('qty', 0))
                if qty > 0:
                    self.logger.warning(f"Liquidating {symbol}: {qty} shares")
                    # Send Market Sell Order
                    # trade_type=2 (Sell), quote_type=03 (Market)
                    await self.kiwoom.send_order(symbol, 2, qty, 0, "03")
                    await asyncio.sleep(0.5) # Prevent burst rate limit
                    
        except Exception as e:
            self.logger.error(f"Panic Liquidation Failed: {e}")
            
    async def on_order_event(self, event_data: Dict[str, Any]):
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
                order_info = {
                    'symbol': event_data.get('code'),
                    'type': event_data.get('order_type'),
                    'quantity': int(event_data.get('qty', 0)),
                    'filled_qty': 0,
                    'price': float(event_data.get('price', 0)),
                    'source': 'UNKNOWN', # External order
                    'timestamp': datetime.now(),
                    'strategy_id': None
                }
                self.active_orders[order_no] = order_info
                await self.save_order(order_no, order_info)
            return

        # Update existing order
        order_info = self.active_orders[order_no]
        
        if status == 'FILLED':
            # Assuming incremental fill quantity in 'exec_qty'
            current_fill = int(event_data.get('exec_qty', 0)) 
            if current_fill == 0:
                 current_fill = int(event_data.get('qty', 0)) # Fallback
            
            order_info['filled_qty'] += current_fill
            
            # Emit Event for Strategy
            event_bus.publish("order.filled", {
                "order_id": order_no,
                "symbol": order_info['symbol'],
                "type": order_info['type'],
                "price": order_info['price'],
                "qty": current_fill,
                "strategy_id": order_info.get('strategy_id')
            })
            
            remaining = order_info['quantity'] - order_info['filled_qty']
            self.logger.info(f"Order {order_no} Partial Fill: {current_fill} (Rem: {remaining})")
            
            if remaining <= 0:
                self.active_orders.pop(order_no)
                await self.remove_order(order_no)
                self.logger.info(f"Order {order_no} Fully Filled.")
                
                # Send Notification
                if self.notification:
                    msg = (
                        f"✅ [체결 완료]\n"
                        f"{order_info['symbol']} ({order_info['symbol']})\n\n"
                        f"• 구분: {order_info['type']}\n"
                        f"• 수량: {current_fill}주 (잔여: {remaining})\n"
                        f"• 가격: {order_info['price']:,.0f}원"
                    )
                    await self.notification.send_message(msg)
            else:
                await self.save_order(order_no, order_info)
                
                # Send Partial Fill Notification
                if self.notification:
                    msg = (
                        f"⚠️ [부분 체결]\n"
                        f"{order_info['symbol']} ({order_info['symbol']})\n\n"
                        f"• 구분: {order_info['type']}\n"
                        f"• 수량: {current_fill}주 (잔여: {remaining})\n"
                        f"• 가격: {order_info['price']:,.0f}원"
                    )
                    await self.notification.send_message(msg)
                
        elif status == 'CANCELLED':
            self.active_orders.pop(order_no)
            await self.remove_order(order_no)
            self.logger.info(f"Order {order_no} Cancelled.")

    async def monitor_unfilled_orders(self):
        """
        Background task to monitor unfilled orders.
        """
        self.logger.info("Started monitoring unfilled orders.")
        while True:
            try:
                await asyncio.sleep(self.unfilled_check_interval)
                
                now = datetime.now()
                # Check for stale orders
                for order_id, info in list(self.active_orders.items()):
                    timestamp = info.get('timestamp')
                    if isinstance(timestamp, str):
                        try:
                            timestamp = datetime.fromisoformat(timestamp)
                        except:
                            continue
                            
                    # Check if we already tried to cancel recently
                    last_cancel = info.get('last_cancel_attempt')
                    if last_cancel and (now - last_cancel).total_seconds() < 10: # Wait 10s before retry
                        continue

                    if (now - timestamp).total_seconds() > self.max_unfilled_time:
                        self.logger.warning(f"Order {order_id} is unfilled for too long. Cancelling...")
                        info['last_cancel_attempt'] = now
                        await self.cancel_order(order_id, info['symbol'])
                        await asyncio.sleep(0.5) # Prevent burst rate limit (429)
                        
            except asyncio.CancelledError:
                self.logger.info("Stopped monitoring unfilled orders.")
                break
            except Exception as e:
                self.logger.error(f"Error in monitor_unfilled_orders: {e}")
                await asyncio.sleep(5)
