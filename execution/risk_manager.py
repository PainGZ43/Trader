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

    async def _fire_alert(self, msg: str):
        """Fire and forget alert."""
        if self.notification_manager:
            try:
                # If we are in an async context, we can just await if the caller awaits check_risk.
                # But check_risk is currently sync in signature?
                # The prompt said check_risk is sync.
                # "def check_risk(self, signal: Signal, account_info: Dict[str, Any]) -> bool:"
                # So we need to schedule it.
                loop = asyncio.get_running_loop()
                loop.create_task(self.notification_manager.send_message(msg, level="WARNING"))
            except RuntimeError:
                pass 

    def check_risk(self, signal: Signal, account_info: Dict[str, Any]) -> bool:
        """
        Check if the signal can be executed based on risk rules.
        """
        # 1. Order Count Limit
        now = datetime.now()
        self._clean_order_window(now)
        if len(self.order_count_window) >= self.config["max_order_count_per_min"]:
            msg_content = "분당 주문 횟수 초과"
            self.logger.warning(msg_content)
            # Fire alert (fire and forget)
            try:
                msg = (
                    f"⚠️ [리스크 경고]\n"
                    f"{msg_content}\n\n"
                    f"• 제한: {self.config['max_order_count_per_min']}회/분\n"
                    f"• 현재: {len(self.order_count_window)}회\n"
                    f"• 조치: 주문 거부"
                )
                loop = asyncio.get_running_loop()
                loop.create_task(self._fire_alert(msg))
            except:
                pass
            return False

        # 2. Daily Loss Limit
        daily_pnl = float(account_info.get("daily_pnl", 0))
        total_asset = float(account_info.get("total_asset", 1))
        
        loss_rate = -daily_pnl / total_asset
        if loss_rate > self.config["max_daily_loss_rate"]:
            # Only block entry (BUY), allow exit (SELL)
            if signal.type == "BUY":
                msg_content = "일일 손실 한도 초과"
                self.logger.warning(msg_content)
                try:
                    msg = (
                        f"⚠️ [리스크 경고]\n"
                        f"{msg_content}\n\n"
                        f"• 제한: {self.config['max_daily_loss_rate']*100:.1f}%\n"
                        f"• 현재: {loss_rate*100:.2f}%\n"
                        f"• 조치: 매수 금지"
                    )
                    loop = asyncio.get_running_loop()
                    loop.create_task(self._fire_alert(msg))
                except:
                    pass
                return False

        # 3. Portfolio Exposure Limit (For BUY)
        if signal.type == "BUY":
            current_cash = float(account_info.get("deposit", 0))
            if current_cash < 0: 
                return False
                
            # Exposure = (Total Asset - Cash) / Total Asset
            exposure = (total_asset - current_cash) / total_asset
            if exposure > self.config["max_portfolio_exposure"]:
                msg_content = "포트폴리오 비중 한도 초과"
                self.logger.warning(msg_content)
                try:
                    msg = (
                        f"⚠️ [리스크 경고]\n"
                        f"{msg_content}\n\n"
                        f"• 제한: {self.config['max_portfolio_exposure']*100:.1f}%\n"
                        f"• 현재: {exposure*100:.2f}%\n"
                        f"• 조치: 매수 금지"
                    )
                    loop = asyncio.get_running_loop()
                    loop.create_task(self._fire_alert(msg))
                except:
                    pass
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
