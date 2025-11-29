import pytest
import asyncio
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Core
from core.config import config
from core.database import db
from core.event_bus import event_bus
from core.logger import get_logger

# Data
from data.data_collector import data_collector
from data.kiwoom_rest_client import kiwoom_client
from data.websocket_client import ws_client

# Strategy
from strategy.base_strategy import BaseStrategy, StrategyInterface
from strategy.strategies import VolatilityBreakoutStrategy
from strategy.persistence import StrategyStateDAO

# Execution
from execution.engine import ExecutionEngine
from execution.risk_manager import RiskManager
from execution.order_manager import OrderManager
from execution.account_manager import AccountManager
from execution.notification import NotificationManager

# Test Strategy Wrapper to expose signals
class MockStrategy(VolatilityBreakoutStrategy):
    def __init__(self, strategy_id, symbol):
        super().__init__(strategy_id, symbol)
        self.signals_generated = []

    async def on_realtime_data(self, data):
        signal = await super().on_realtime_data(data)
        if signal:
            self.signals_generated.append(signal)
        return signal

@pytest.mark.asyncio
class TestFullSystemIntegration:
    """
    End-to-End Integration Test for the entire trading system.
    """

    async def _setup_system(self):
        # --- Setup ---
        # 1. Config Setup
        config.set("MOCK_MODE", True)
        config.set("DB_PATH", ":memory:") 
        config.set("KAKAO_APP_KEY", "test_key")
        config.set("KAKAO_ACCESS_TOKEN", "test_token")
        
        # 2. DB Init
        await db.connect()
        
        # 3. Mock External APIs
        self.mock_kiwoom = AsyncMock()
        self.mock_kiwoom.get_token = AsyncMock(return_value="mock_token")
        self.mock_kiwoom.get_account_balance = AsyncMock(return_value={
            "deposit": 10000000,
            "positions": []
        })
        self.mock_kiwoom.send_order = AsyncMock(return_value={"order_id": "ORDER_123"})
        
        ws_client.connect = AsyncMock()
        ws_client.subscribe = AsyncMock()
        
        # 4. Initialize Components & Dependency Injection
        self.notification_manager = NotificationManager()
        self.notification_manager.send_message = AsyncMock()
        
        self.risk_manager = RiskManager()
        self.risk_manager.configure({}, self.notification_manager)
        
        self.order_manager = OrderManager(self.mock_kiwoom)
        self.account_manager = AccountManager(self.mock_kiwoom)
        
        self.engine = ExecutionEngine(self.mock_kiwoom, mode="PAPER", config={"paper_capital": 10000000})
        
        # Swap out NotificationManager
        self.engine.notification_manager = self.notification_manager
        self.engine.risk_manager.notification_manager = self.notification_manager
        
        # Initialize them
        await self.engine.initialize()

    async def _teardown_system(self):
        await db.close()

    async def test_full_trading_flow(self):
        """
        Scenario:
        1. Start System
        2. Strategy Warm-up
        3. Receive Real-time Data (Price goes up)
        4. Trigger Buy Signal
        5. Execute Order (Paper)
        6. Verify Position & Notification
        """
        await self._setup_system()
        
        try:
            logger = get_logger("TestIntegration")
            logger.info("Starting Full Integration Test...")

            # --- Step 1: Register Strategy ---
            strategy_id = "TEST_STRATEGY"
            symbol = "005930"
            strategy_config = {
                "k": 0.5,
                "lookback": 1
            }
            
            test_strategy = MockStrategy(strategy_id, symbol)
            test_strategy.initialize(strategy_config)
            
            self.engine.register_strategy(test_strategy)
            
            # --- Step 2: Warm-up Strategy ---
            mock_history = pd.DataFrame([{
                "timestamp": datetime.now() - timedelta(days=1),
                "open": 10000, "high": 11000, "low": 9000, "close": 10500, "volume": 1000
            }])
            test_strategy.update_market_data(mock_history)
            
            # --- Step 3: Start Execution Engine ---
            await self.engine.start_trading()
            assert self.engine.is_running is True
            
            # --- Step 4: Simulate Real-time Data (Breakout) ---
            # Target = 10000 + (2000 * 0.5) = 11000
            
            # 4-1. Tick below target
            tick_data_1 = {
                "code": "005930",
                "price": 10500, 
                "open": 10000,
                "volume": 10,
                "timestamp": datetime.now()
            }
            await self.engine.on_realtime_data(tick_data_1)
            assert len(test_strategy.signals_generated) == 0
            
            # 4-2. Tick above target (Breakout!)
            tick_data_2 = {
                "code": "005930",
                "price": 11200, 
                "open": 10000,
                "volume": 100,
                "timestamp": datetime.now()
            }
            
            # Process Data
            await self.engine.on_realtime_data(tick_data_2)
            
            # --- Step 5: Verify Execution ---
            
            # 1. Signal Generated?
            assert len(test_strategy.signals_generated) == 1
            signal = test_strategy.signals_generated[0]
            assert signal.type == "BUY"
            
            # 2. Order Sent?
            await asyncio.sleep(0.1)
            active_orders = self.engine.order_manager.active_orders
            assert len(active_orders) > 0
            
            # 3. Notification Sent?
            assert self.notification_manager.send_message.called
            call_args = self.notification_manager.send_message.call_args[0]
            assert "매수" in call_args[0] or "BUY" in call_args[0]
            
            logger.info("Full Integration Test Passed!")
            
        finally:
            await self._teardown_system()

import pandas as pd
