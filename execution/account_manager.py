import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from core.logger import get_logger
from core.config import config

class AccountManager:
    """
    Manages account balance, positions, and PnL.
    Syncs with Exchange (Real/Paper) periodically.
    """
    def __init__(self, exchange):
        self.logger = get_logger("AccountManager")
        self.exchange = exchange
        
        # State
        self.balance: Dict[str, float] = {
            "deposit": 0.0,
            "total_asset": 0.0,
            "daily_pnl": 0.0,
            "total_pnl": 0.0,
            "total_purchase": 0.0,
            "total_eval": 0.0,
            "total_return": 0.0
        }
        self.positions: Dict[str, Dict[str, Any]] = {} # symbol -> position_info
        
        # Config
        self.sync_interval = 60 # 1 minute
        self.min_cash_ratio = 0.1 # Block buy if cash < 10% of total asset
        
        self._running = False
        self._task = None

    async def start(self):
        """Start background sync task."""
        self._running = True
        self._task = asyncio.create_task(self._sync_loop())
        self.logger.info("AccountManager Started")

    async def stop(self):
        """Stop background sync task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.logger.info("AccountManager Stopped")

    async def _sync_loop(self):
        """Periodic sync loop."""
        while self._running:
            try:
                await self.update_balance()
            except Exception as e:
                self.logger.error(f"Sync Error: {e}")
            
            await asyncio.sleep(self.sync_interval)

    async def update_balance(self):
        """Fetch latest balance and positions from Exchange."""
        # This calls KiwoomRestClient.get_account_balance or PaperExchange.get_account_balance
        # Expected format: {"output": {"single": [...], "multi": [...]}}
        
        try:
            res = await self.exchange.get_account_balance()
            if not res:
                self.logger.warning("Failed to fetch balance: No response (or API Error)")
                return

            # Check if response is wrapped in "output" (Mock) or flat (Real)
            data = res.get("output", res)
            
            # Update Balance
            # Real API Keys:
            # prsm_dpst_aset_amt: Presumed Deposit Asset (Total Asset?)
            # tot_evlt_amt: Total Evaluation Amount (Stocks)
            # tot_evlt_pl: Total Profit/Loss
            
            total_asset = float(data.get("prsm_dpst_aset_amt", 0))
            stock_eval = float(data.get("tot_evlt_amt", 0))
            
            # Estimate Cash = Total Asset - Stock Eval (if specific cash field missing)
            # Or use 'deposit' if available (Mock)
            cash = float(data.get("deposit", 0))
            if cash == 0 and total_asset > 0:
                cash = total_asset - stock_eval
            
            self.balance["deposit"] = cash
            self.balance["total_asset"] = total_asset
            self.balance["total_pnl"] = float(data.get("tot_evlt_pl", data.get("tot_evlt_pl_amt", 0)))
            self.balance["total_purchase"] = float(data.get("tot_pur_amt", 0))
            self.balance["total_eval"] = stock_eval
            self.balance["total_return"] = float(data.get("tot_prft_rt", data.get("tot_earning_rate", 0)))
            
            # Update Positions
            # Real Key: acnt_evlt_remn_indv_tot
            # Mock Key: output_list or multi
            multi = data.get("acnt_evlt_remn_indv_tot", data.get("output_list", data.get("multi", [])))
            
            new_positions = {}
            for pos in multi:
                # Real: stk_cd, stk_nm, cur_prc, evlt_amt, prft_rt
                code = pos.get("stk_cd", pos.get("code", "")).replace("A", "")
                if not code: continue
                
                new_positions[code] = {
                    "name": pos.get("stk_nm", pos.get("name")),
                    "qty": int(pos.get("rmnd_qty", pos.get("qty", 0))),
                    "avg_price": float(pos.get("pur_pric", pos.get("avg_price", 0))),
                    "current_price": float(pos.get("cur_prc", pos.get("cur_price", pos.get("current_price", 0)))),
                    "eval_amt": float(pos.get("evlt_amt", pos.get("eval_amt", 0))),
                    "earning_rate": float(pos.get("prft_rt", pos.get("earning_rate", 0)))
                }
            
            self.positions = new_positions
            self.logger.debug(f"Balance Updated. Asset: {self.balance['total_asset']:,.0f}, Positions: {len(self.positions)}")
            
            # Publish Event for UI
            from core.event_bus import event_bus
            # 1. Balance Summary
            event_bus.publish("account.summary", {"balance": self.balance})
            
            # 2. Portfolio (List of positions)
            # Add 'code' to each position dict for UI convenience if not already there
            portfolio_list = []
            for code, pos in self.positions.items():
                pos_data = pos.copy()
                pos_data["code"] = code
                portfolio_list.append(pos_data)
            
            event_bus.publish("account.portfolio", portfolio_list)
            
        except Exception as e:
            self.logger.error(f"Error updating balance: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """Return account summary."""
        return {
            "balance": self.balance,
            "positions": self.positions,
            "updated_at": datetime.now()
        }

    def check_buying_power(self, amount: float) -> bool:
        """
        Check if we have enough cash and meet risk requirements.
        Implements 'Block Buy if Cash Ratio < 10%' logic.
        """
        # 1. Absolute Cash Check
        if self.balance["deposit"] < amount:
            self.logger.warning(f"Not enough cash. Need: {amount}, Have: {self.balance['deposit']}")
            return False
            
        # 2. Risk Ratio Check (Min Cash Buffer)
        if self.balance["total_asset"] > 0:
            current_cash_ratio = self.balance["deposit"] / self.balance["total_asset"]
            if current_cash_ratio < self.min_cash_ratio:
                self.logger.warning(f"Low Cash Ratio ({current_cash_ratio:.1%}). New Buy Blocked.")
                return False
                
        return True
