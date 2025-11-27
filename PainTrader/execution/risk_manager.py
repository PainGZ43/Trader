from typing import Dict, Any
from datetime import datetime
from strategy.base_strategy import Signal
from core.logger import get_logger

class RiskManager:
    """
    Manages account and portfolio level risks.
    """
    def __init__(self):
        self.logger = get_logger("RiskManager")
        self.config = {
            "max_daily_loss_rate": 0.03, # 3%
            "max_order_count_per_min": 10,
            "max_portfolio_exposure": 0.95 # 95%
        }
        self.daily_loss = 0.0
        self.order_count_window = [] # Timestamps of orders
        self.notification_manager = None

    def configure(self, config: Dict[str, Any], notification_manager=None):
        self.config.update(config)
        if notification_manager:
            self.notification_manager = notification_manager

    async def _send_alert(self, msg: str):
        if self.notification_manager:
            await self.notification_manager.send_message(msg, level="WARNING")

    def check_risk(self, signal: Signal, account_info: Dict[str, Any]) -> bool:
        """
        Check if the signal can be executed based on risk rules.
        """
        # 1. Order Count Limit
        now = datetime.now()
        self._clean_order_window(now)
        if len(self.order_count_window) >= self.config["max_order_count_per_min"]:
            msg = "Risk Check Failed: Max order count per minute exceeded."
            self.logger.warning(msg)
            # Async call in sync method? RiskManager.check_risk is sync.
            # We can't await here. We might need to fire and forget or change check_risk to async.
            # For now, just log. Or if notification_manager has a sync wrapper or we use asyncio.create_task if loop exists.
            # But check_risk is called from async execute_signal, so we should make check_risk async or use create_task.
            # Let's use create_task if loop is running.
            self._fire_alert(msg)
            return False

        # 2. Daily Loss Limit
        # Assuming account_info has 'daily_pnL' (Realized + Unrealized)
        daily_pnl = float(account_info.get("daily_pnl", 0))
        total_asset = float(account_info.get("total_asset", 1))
        
        loss_rate = -daily_pnl / total_asset
        if loss_rate > self.config["max_daily_loss_rate"]:
            # Only block entry (BUY), allow exit (SELL)
            if signal.type == "BUY":
                msg = f"Risk Check Failed: Daily loss limit exceeded ({loss_rate*100:.2f}% > {self.config['max_daily_loss_rate']*100:.2f}%)"
                self.logger.warning(msg)
                self._fire_alert(f"🚨 [리스크 경고] {msg}")
                return False
                
    def _fire_alert(self, msg: str):
        """Fire and forget alert."""
        if self.notification_manager:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.notification_manager.send_message(msg, level="WARNING"))
            except RuntimeError:
                pass # No loop running

        # 3. Portfolio Exposure Limit (For BUY)
        if signal.type == "BUY":
            current_cash = float(account_info.get("deposit", 0))
            if current_cash < 0: # Should not happen
                return False
                
            # Check if we have enough cash is done in PositionSizer/OrderManager usually,
            # but here we check if we are already too exposed.
            # Exposure = (Total Asset - Cash) / Total Asset
            exposure = (total_asset - current_cash) / total_asset
            if exposure > self.config["max_portfolio_exposure"]:
                self.logger.warning(f"Risk Check Failed: Max portfolio exposure reached ({exposure*100:.2f}%)")
                return False

        return True

    def record_order(self):
        """
        Call this when an order is actually sent.
        """
        self.order_count_window.append(datetime.now())

    def _clean_order_window(self, now: datetime):
        """
        Remove orders older than 1 minute.
        """
        cutoff = now.timestamp() - 60
        self.order_count_window = [t for t in self.order_count_window if t.timestamp() > cutoff]
