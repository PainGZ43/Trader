import asyncio
from typing import Dict, Any
from execution.risk_manager import RiskManager
from execution.order_manager import OrderManager
from strategy.base_strategy import Signal
from data.kiwoom_rest_client import KiwoomRestClient
from core.logger import get_logger

class ExecutionEngine:
    """
    Orchestrates execution: Signal -> Risk Check -> Order.
    """
    def __init__(self, kiwoom: KiwoomRestClient, mode: str = "REAL", config: Dict[str, Any] = None):
        self.logger = get_logger("ExecutionEngine")
        self.kiwoom = kiwoom
        self.mode = mode
        self.config = config or {}
        
        self.risk_manager = RiskManager()
        # self.risk_manager.configure(self.config.get("risk", {})) # Moved to initialize or after notification init
        
        self.order_manager = OrderManager(kiwoom)
        self.account_num = "" # Set externally if needed, or from key manager
        
        if self.mode == "PAPER":
            from execution.paper_exchange import PaperExchange
            self.exchange = PaperExchange(self.config.get("paper_capital", 100_000_000))
            # OrderManager needs to use this exchange
            self.order_manager.kiwoom = self.exchange
            self.logger.info("Execution Engine initialized in PAPER TRADING mode")
        else:
            self.exchange = self.kiwoom
            self.order_manager.kiwoom = self.kiwoom
            self.logger.info("Execution Engine initialized in REAL TRADING mode")
            
        # Initialize Account Manager
        from execution.account_manager import AccountManager
        self.account_manager = AccountManager(self.exchange)

        # Initialize Notification Manager
        from execution.notification import NotificationManager
        self.notification_manager = NotificationManager()
        
        # Configure Risk Manager with Notification
        self.risk_manager.configure(self.config.get("risk", {}), self.notification_manager)

        # Strategies
        self.strategies: Dict[str, Any] = {}

        # Initialize Scheduler
        from execution.scheduler import Scheduler
        self.scheduler = Scheduler()
        self._configure_scheduler()

    def register_strategy(self, strategy):
        """Register a strategy instance."""
        self.strategies[strategy.strategy_id] = strategy
        self.logger.info(f"Registered Strategy: {strategy.strategy_id}")

    async def on_realtime_data(self, data: Dict[str, Any]):
        """
        Dispatch real-time data to all registered strategies.
        """
        if not self.is_running:
            return

        # Dispatch to strategies
        for strategy_id, strategy in self.strategies.items():
            # Check if strategy is interested in this symbol
            # Assuming strategy.symbol matches data['code']
            if strategy.symbol == data.get('code'):
                signal = await strategy.on_realtime_data(data)
                if signal:
                    # Execute Signal
                    # Determine quantity (Position Sizing)
                    # For now, fixed quantity or based on config
                    quantity = 1 # Default
                    if hasattr(strategy, 'position_sizer') and strategy.position_sizer:
                         quantity = strategy.position_sizer.calculate(signal)
                    
                    await self.execute_signal(signal, quantity)
        
        # Emit Event for UI
        from core.event_bus import event_bus
        event_bus.publish("market.data.tick", data)

    def _configure_scheduler(self):
        """Register scheduled tasks."""
        # 1. Watchdog (Every 1 hour)
        async def watchdog_job():
            await self.notification_manager.send_message("🤖 [시스템] 정상 작동 중 (Watchdog)", level="INFO")
        
        self.scheduler.register_interval(3600, watchdog_job, "Watchdog")
        
        # 2. Daily Report (15:40)
        async def daily_report_job():
            summary = self.account_manager.get_summary()
            await self.notification_manager.send_daily_report(summary)
            
        self.scheduler.register_cron(15, 40, daily_report_job, "DailyReport")
        
        # 3. Market Status Monitor (Every 1 minute)
        from data.market_schedule import market_schedule
        
        async def check_market_event():
            # Check if status changed
            was_open = market_schedule.is_market_open
            is_open = market_schedule.check_market_status()
            
            if not was_open and is_open:
                await self._on_market_open()
            elif was_open and not is_open:
                await self._on_market_close()
                
        self.scheduler.register_interval(60, check_market_event, "MarketMonitor")

    async def _on_market_open(self):
        """Handle Market Open Event."""
        self.logger.info("Market Opened.")
        await self.notification_manager.send_message("🔔 [장 시작] 정규장이 시작되었습니다. 트레이딩을 개시합니다.", level="INFO")
        # Resume strategy if needed

    async def _on_market_close(self):
        """Handle Market Close Event."""
        self.logger.info("Market Closed.")
        await self.notification_manager.send_message("🔔 [장 마감] 정규장이 종료되었습니다. 미체결 주문을 취소합니다.", level="INFO")
        
        # Cancel all active orders
        await self.order_manager.cancel_all_orders()
        
        # Daily Report will be sent at 15:40 by Cron task

    async def stop_trading(self, panic: bool = False):
        """
        Stop trading activities.
        panic: If True, cancel all orders immediately.
        """
        self.logger.warning(f"Stopping Trading Engine (Panic: {panic})")
        
        # 1. Stop Scheduler
        if self.scheduler:
            # self.scheduler.stop() # Scheduler doesn't have stop? It should.
            # Assuming we just stop adding new tasks or ignore signals.
            pass
            
        # 2. Cancel All Orders & Liquidate
        if panic:
            await self.order_manager.cancel_all_orders()
            await self.order_manager.close_all_positions()
            await self.notification_manager.send_message("🚨 [긴급 정지] 모든 주문 취소 및 전량 청산을 시도합니다.", level="WARNING")
        else:
            await self.notification_manager.send_message("🛑 [시스템] 트레이딩을 중단합니다.", level="INFO")

        # 3. Set State
        # We need a state flag
        self.is_running = False

    async def start_trading(self):
        """
        Resume trading activities.
        """
        if not self.is_running:
            self.is_running = True
            self.logger.info("Trading Engine Resumed.")
            await self.notification_manager.send_message("▶ [시스템] 트레이딩을 재개합니다.", level="INFO")

    def get_state(self) -> Dict[str, Any]:
        """
        Return current engine state for UI.
        """
        summary = self.account_manager.get_summary()
        active_orders_count = len(self.order_manager.active_orders)
        
        return {
            "is_running": getattr(self, "is_running", True),
            "mode": self.mode,
            "account": self.account_num,
            "market_status": "OPEN" if self.scheduler else "CLOSED", # Simplified
            "total_asset": summary["balance"].get("total_asset", 0),
            "daily_pnl": summary["balance"].get("daily_pnl", 0),
            "deposit": summary["balance"].get("deposit", 0),
            "active_orders_count": active_orders_count
        }

    async def initialize(self):
        """Async initialization."""
        self.is_running = True
        
        # Initial Sync
        await self.account_manager.update_balance()
        # Start Background Sync
        await self.account_manager.start()
        # Start Notification Worker
        await self.notification_manager.start()
        # Start Scheduler
        await self.scheduler.start()
            
        # Initialize Order Manager (Create Tables)
        await self.order_manager.initialize()

        # Start background tasks
        asyncio.create_task(self.order_manager.monitor_unfilled_orders())

    async def execute_signal(self, signal: Signal, quantity: int):
        """
        Execute a trading signal.
        """
        if not getattr(self, "is_running", True):
            self.logger.warning("Signal ignored: Trading is stopped.")
            return

        self.logger.info(f"Received Signal: {signal}")
        
        # 1. Get Account Info (from AccountManager)
        summary = self.account_manager.get_summary()
        account_info = {
            "deposit": summary["balance"]["deposit"],
            "total_asset": summary["balance"]["total_asset"],
            "daily_pnl": summary["balance"]["daily_pnl"]
        }
        
        # 2. Risk Check
        # 2.1. AccountManager Buying Power Check (for BUY)
        if signal.type == "BUY":
            # Estimate cost (Price * Qty)
            estimated_cost = signal.price * quantity
            if not self.account_manager.check_buying_power(estimated_cost):
                self.logger.warning("Signal rejected by Account Manager (Buying Power)")
                return
 
        # 2.2. RiskManager Check
        if not self.risk_manager.check_risk(signal, account_info):
            self.logger.warning("Signal rejected by Risk Manager")
            return
 
        # 3. Send Order
        order_id = await self.order_manager.send_order(signal, quantity, self.account_num)
        
        if order_id:
            self.risk_manager.record_order()
            self.logger.info(f"Signal Executed. Order ID: {order_id}")
            
            # Send Notification
            # Premium Spec:
            # 🚀 [주문 접수]
            # 종목명 (종목코드)
            #
            # • 주문: 매수 10주 @ 60,000원
            # • 전략: 변동성돌파
            total_amt = quantity * signal.price
            msg = (
                f"🚀 [주문 접수]\n"
                f"{signal.symbol} ({signal.symbol})\n\n"
                f"• 주문: {signal.type} {quantity}주 @ {signal.price:,.0f}원\n"
                f"• 총액: {total_amt:,.0f}원\n"
                f"• 전략: {signal.strategy_id if hasattr(signal, 'strategy_id') else 'Unknown'}"
            )
            await self.notification_manager.send_message(msg)
        else:
            self.logger.error("Signal Execution Failed")
            await self.notification_manager.send_message(f"⚠️ [오류] 주문 실패: {signal.symbol}", level="ERROR")


