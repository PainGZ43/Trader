import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from core.logger import get_logger

class PaperExchange:
    """
    Simulates an exchange for Paper Trading.
    Maintains virtual account balance and positions.
    Matches orders against real-time quotes (or current price).
    """
    def __init__(self, initial_capital: float = 100_000_000):
        self.logger = get_logger("PaperExchange")
        self.initial_capital = initial_capital
        self.balance = {
            "deposit": initial_capital,
            "total_asset": initial_capital,
            "daily_pnl": 0.0
        }
        self.positions: Dict[str, Dict[str, Any]] = {} # symbol -> {qty, avg_price, current_price}
        self.active_orders: Dict[str, Dict[str, Any]] = {} # order_id -> order_info
        
        # Fees
        self.fee_rate_buy = 0.00015
        self.fee_rate_sell = 0.00015 + 0.0020 # Includes Tax
        
        self.logger.info(f"Paper Exchange Initialized. Capital: {initial_capital:,.0f}")

    async def send_order(self, symbol: str, order_type: int, qty: int, price: int = 0, trade_type: str = "00") -> Dict[str, Any]:
        """
        Mimics KiwoomRestClient.send_order.
        order_type: 1 (Buy), 2 (Sell)
        trade_type: "00" (Limit), "03" (Market)
        """
        order_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now()
        
        # Validate Inputs
        if qty <= 0:
            return {"result_code": -1, "msg": "Invalid Quantity"}
            
        side = "BUY" if order_type == 1 else "SELL"
        is_market = (trade_type == "03") or (price == 0)
        
        order_info = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": price,
            "type": "MARKET" if is_market else "LIMIT",
            "status": "PENDING",
            "timestamp": timestamp
        }
        
        self.active_orders[order_id] = order_info
        self.logger.info(f"[PAPER] Order Accepted: {order_id} | {side} {symbol} {qty} @ {price if not is_market else 'MKT'}")
        
        # Try to match immediately (if market order or price allows)
        # In a real event loop, this might happen via on_quote.
        # For simplicity, we assume the caller will trigger matching or we do it here if we have price.
        # But we don't have price here. We rely on match_order being called externally with quote.
        
        return {"result_code": 0, "msg": "Success", "order_no": order_id}

    async def cancel_order(self, order_no: str, symbol: str, qty: int) -> Dict[str, Any]:
        if order_no in self.active_orders:
            self.active_orders.pop(order_no)
            self.logger.info(f"[PAPER] Order Cancelled: {order_no}")
            return {"result_code": 0, "msg": "Cancelled"}
        return {"result_code": -1, "msg": "Order Not Found"}

    async def get_account_balance(self) -> Dict[str, Any]:
        """
        Return balance in Kiwoom format.
        """
        # Update Total Asset based on current positions
        total_eval = 0.0
        total_buy = 0.0
        
        pos_list = []
        for sym, pos in self.positions.items():
            current_price = pos.get('current_price', pos['avg_price'])
            eval_amt = pos['qty'] * current_price
            buy_amt = pos['qty'] * pos['avg_price']
            
            total_eval += eval_amt
            total_buy += buy_amt
            
            profit = eval_amt - buy_amt
            rate = (profit / buy_amt * 100) if buy_amt > 0 else 0.0
            
            pos_list.append({
                "code": sym,
                "name": sym, # Mock Name
                "qty": str(pos['qty']),
                "avg_price": str(pos['avg_price']),
                "cur_price": str(current_price),
                "eval_amt": str(int(eval_amt)),
                "earning_rate": f"{rate:.2f}"
            })
            
        self.balance['total_asset'] = self.balance['deposit'] + total_eval
        
        return {
            "output": {
                "single": [{
                    "deposit": str(int(self.balance['deposit'])),
                    "pres_asset_total": str(int(self.balance['total_asset'])),
                    "total_purchase_amt": str(int(total_buy)),
                    "total_eval_amt": str(int(total_eval))
                }],
                "multi": pos_list
            }
        }

    async def load_state(self):
        """Load account state from DB."""
        from core.database import db
        try:
            query = "SELECT deposit, positions_json FROM paper_account WHERE account_id = ?"
            rows = await db.fetch_all(query, ("PAPER_ACC",))
            if rows:
                import json
                self.balance['deposit'] = rows[0]['deposit']
                self.positions = json.loads(rows[0]['positions_json'])
                self.logger.info(f"Paper Account Loaded. Deposit: {self.balance['deposit']:,.0f}")
        except Exception as e:
            self.logger.error(f"Failed to load paper account: {e}")

    async def save_state(self):
        """Save account state to DB."""
        from core.database import db
        try:
            import json
            query = """
                INSERT OR REPLACE INTO paper_account (account_id, deposit, positions_json, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """
            await db.execute(query, ("PAPER_ACC", self.balance['deposit'], json.dumps(self.positions)))
        except Exception as e:
            self.logger.error(f"Failed to save paper account: {e}")

    def match_orders(self, quote: Dict[str, Any]):
        """
        Called when real-time quote is received.
        quote: {symbol, current_price, ask1, bid1, ask_size1, bid_size1}
        """
        import random
        symbol = quote['symbol']
        current_price = quote.get('current_price')
        ask1 = quote.get('ask1', current_price) # Sell Price (Buy Order matches here)
        bid1 = quote.get('bid1', current_price) # Buy Price (Sell Order matches here)
        ask_size = quote.get('ask_size1', 1000000) # Default large if missing
        bid_size = quote.get('bid_size1', 1000000)
        
        # DEBUG
        # self.logger.debug(f"Match Quote: {ask_size=} {bid_size=} Keys: {list(quote.keys())}")
        
        # Update Position Current Price
        if symbol in self.positions:
            self.positions[symbol]['current_price'] = current_price

        # Match Orders
        filled_ids = []
        for order_id, order in self.active_orders.items():
            if order['symbol'] != symbol:
                continue
                
            executed = False
            exec_price = 0
            
            if order['side'] == "BUY":
                # Liquidity Check
                if order['qty'] > ask_size:
                    self.logger.debug(f"Liquidity Check Failed: Qty {order['qty']} > AskSize {ask_size}")
                    # Partial fill logic could be here, but for now skip or fill max?
                    # Let's assume we wait for enough liquidity or fill available.
                    # Simpler: Only fill if enough liquidity (Conservative)
                    continue

                # Market Order or Limit >= Ask1
                if order['type'] == "MARKET" or order['price'] >= ask1:
                    # Slippage: Randomly add 0~2 ticks or 0.05%
                    slippage = 0
                    if order['type'] == "MARKET":
                         slippage = ask1 * random.uniform(0, 0.0005) # Max 0.05%
                    
                    exec_price = ask1 + slippage
                    executed = True
                    
            elif order['side'] == "SELL":
                # Liquidity Check
                if order['qty'] > bid_size:
                    continue

                # Market Order or Limit <= Bid1
                if order['type'] == "MARKET" or order['price'] <= bid1:
                    # Slippage
                    slippage = 0
                    if order['type'] == "MARKET":
                         slippage = bid1 * random.uniform(0, 0.0005)
                         
                    exec_price = bid1 - slippage
                    executed = True
                    
            if executed:
                # We need to call save_state() but this method is sync (called from callback).
                # So we schedule it or run it? 
                # Ideally match_orders should be async or fire event.
                # For now, we just update memory and save periodically or on critical events.
                # Let's make _execute_trade async? No, match_orders is usually called from sync context?
                # If match_orders is called from async loop, we can use create_task.
                self._execute_trade(order, exec_price)
                filled_ids.append(order_id)
                
        for oid in filled_ids:
            self.active_orders.pop(oid)

    def _execute_trade(self, order: Dict[str, Any], price: float):
        qty = order['qty']
        amount = price * qty
        
        if order['side'] == "BUY":
            fee = amount * self.fee_rate_buy
            cost = amount + fee
            
            if self.balance['deposit'] >= cost:
                self.balance['deposit'] -= cost
                
                # Update Position
                if order['symbol'] in self.positions:
                    pos = self.positions[order['symbol']]
                    total_qty = pos['qty'] + qty
                    avg_price = (pos['qty'] * pos['avg_price'] + amount) / total_qty
                    pos['qty'] = total_qty
                    pos['avg_price'] = avg_price
                else:
                    self.positions[order['symbol']] = {
                        "qty": qty,
                        "avg_price": price,
                        "current_price": price
                    }
                self.logger.info(f"[PAPER] BUY EXEC: {order['symbol']} {qty} @ {price:.0f} (Fee: {fee:.0f})")
            else:
                self.logger.warning(f"[PAPER] Insufficient Funds for BUY: {cost} > {self.balance['deposit']}")
                
        elif order['side'] == "SELL":
            if order['symbol'] in self.positions:
                pos = self.positions[order['symbol']]
                if pos['qty'] >= qty:
                    fee = amount * self.fee_rate_sell
                    revenue = amount - fee
                    self.balance['deposit'] += revenue
                    
                    pos['qty'] -= qty
                    if pos['qty'] == 0:
                        del self.positions[order['symbol']]
                        
                    self.logger.info(f"[PAPER] SELL EXEC: {order['symbol']} {qty} @ {price:.0f} (Fee: {fee:.0f})")
                else:
                    self.logger.warning(f"[PAPER] Insufficient Qty for SELL: {qty} > {pos['qty']}")
            else:
                self.logger.warning(f"[PAPER] No Position for SELL: {order['symbol']}")
        
        # Trigger Save (Fire and Forget)
        asyncio.create_task(self.save_state())
