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
            "total_pnl": 0.0
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
            if not res or "output" not in res:
                self.logger.warning("Failed to fetch balance: Invalid response")
                return

            output = res["output"]
            single = output.get("single", [{}])[0]
            multi = output.get("multi", [])

            # Update Balance
            # Note: Keys might vary depending on TR (opw00018). 
            # Adjusting to standard keys used in KiwoomRestClient mock/real.
            self.balance["deposit"] = float(single.get("deposit", 0))
            self.balance["total_asset"] = float(single.get("pres_asset_total", 0))
            self.balance["total_pnl"] = float(single.get("total_eval_profit_loss_amt", 0))
            
            # Daily PnL might need separate calculation or TR
            # For now, assume total_pnl is what we track, or calculate daily diff if needed.
            
            # Update Positions
            new_positions = {}
            for pos in multi:
                code = pos.get("code", "").replace("A", "") # Remove 'A' prefix if exists
                if not code: continue
                
                new_positions[code] = {
                    "name": pos.get("name"),
                    "qty": int(pos.get("qty", 0)),
                    "avg_price": float(pos.get("avg_price", 0)),
                    "current_price": float(pos.get("cur_price", 0)),
                    "eval_amt": float(pos.get("eval_amt", 0)),
                    "earning_rate": float(pos.get("earning_rate", 0))
                }
            
            self.positions = new_positions
            self.logger.debug(f"Balance Updated. Asset: {self.balance['total_asset']:,.0f}, Positions: {len(self.positions)}")
            
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
