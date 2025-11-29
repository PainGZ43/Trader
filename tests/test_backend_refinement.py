import unittest
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

# Import modules to test
from execution.order_manager import OrderManager
from execution.engine import ExecutionEngine
from data.data_collector import DataCollector
from execution.account_manager import AccountManager
from core.logger import Logger
from core.event_bus import EventBus
from strategy.base_strategy import Signal

class TestBackendRefinement(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self):
        # Mocks
        self.mock_kiwoom = AsyncMock()
        self.mock_kiwoom.send_order.return_value = {
            "rt_cd": "0",
            "output": {"order_no": "ORDER_123"}
        }
        self.mock_kiwoom.cancel_order.return_value = True
        self.mock_kiwoom.get_account_balance.return_value = {
            "output": {
                "single": [{"pres_asset_total": "10000000", "deposit": "5000000"}],
                "multi": []
            }
        }
        
        # OrderManager
        self.order_manager = OrderManager(self.mock_kiwoom)
        
        # ExecutionEngine
        self.engine = ExecutionEngine(self.mock_kiwoom, mode="REAL")
        self.engine.notification_manager = AsyncMock() # Mock notification
        self.engine.order_manager = self.order_manager # Inject mocked order manager
        self.engine.is_running = True # Simulate initialized state
        
        # DataCollector
        self.data_collector = DataCollector()
        self.data_collector.rest_client = self.mock_kiwoom
        self.data_collector.ws_client = AsyncMock()
        
        # AccountManager
        self.account_manager = AccountManager(self.mock_kiwoom)
        
        # Logger
        self.logger = Logger()

    async def test_order_manager_manual_order(self):
        """Test send_manual_order and source tracking."""
        # send_manual_order(symbol, type, price, quantity)
        order_id = await self.order_manager.send_manual_order("005930", "BUY", 70000, 10)
        
        self.assertEqual(order_id, "ORDER_123")
        self.assertIn("ORDER_123", self.order_manager.active_orders)
        self.assertEqual(self.order_manager.active_orders["ORDER_123"]["source"], "MANUAL")
        
        # Verify API call: send_order(symbol, type, qty, price, quote_type)
        self.mock_kiwoom.send_order.assert_called_with("005930", 1, 10, 70000, "00")

    async def test_order_manager_cancel_all(self):
        """Test cancel_all_orders."""
        # Setup active orders
        self.order_manager.active_orders = {
            "ORD1": {"symbol": "005930", "qty": 10, "source": "STRATEGY"},
            "ORD2": {"symbol": "000660", "qty": 5, "source": "MANUAL"}
        }
        
        await self.order_manager.cancel_all_orders()
        
        # Should call cancel for both
        self.assertEqual(self.mock_kiwoom.cancel_order.call_count, 2)
        # Active orders should be cleared (optimistically or by event - here we check calls)

    async def test_execution_engine_control(self):
        """Test stop_trading, start_trading, and get_state."""
        # Initial state
        self.assertTrue(self.engine.is_running)
        
        # Stop
        await self.engine.stop_trading()
        self.assertFalse(self.engine.is_running)
        
        # Try to execute signal while stopped
        signal = Signal("005930", "BUY", 70000, datetime.now(), "Test")
        await self.engine.execute_signal(signal, 10)
        self.mock_kiwoom.send_order.assert_not_called()
        
        # Resume
        await self.engine.start_trading()
        self.assertTrue(self.engine.is_running)
        
        # Get State
        state = self.engine.get_state()
        self.assertTrue(state["is_running"])
        self.assertIn("total_asset", state)
        self.assertIn("active_orders_count", state)

    async def test_data_collector_conditions(self):
        """Test condition subscription and event handling."""
        # Subscribe
        await self.data_collector.subscribe_condition("001", "Golden Cross")
        self.mock_kiwoom.send_condition.assert_called_with("1000", "Golden Cross", "001", "0")
        
        # Unsubscribe
        await self.data_collector.unsubscribe_condition("001", "Golden Cross")
        self.mock_kiwoom.stop_condition.assert_called_with("1000", "Golden Cross", "001")
        
        # Event Handling
        event_data = {
            "condition_index": "001",
            "condition_name": "Golden Cross",
            "code": "005930",
            "type": "I" # Insert
        }
        
        # Mock EventBus publish
        with patch("core.event_bus.EventBus.publish") as mock_publish:
            await self.data_collector._on_condition_event(event_data)
            mock_publish.assert_called()
            args = mock_publish.call_args[0]
            self.assertEqual(args[0], "CONDITION_MATCH")
            self.assertEqual(args[1]["symbol"], "005930")
            self.assertEqual(args[1]["type"], "I")

    async def test_account_manager_event(self):
        """Test ACCOUNT_UPDATE event publishing."""
        with patch("core.event_bus.EventBus.publish") as mock_publish:
            await self.account_manager.update_balance()
            
            mock_publish.assert_called()
            args = mock_publish.call_args[0]
            self.assertEqual(args[0], "ACCOUNT_UPDATE")
            self.assertIn("balance", args[1])
            self.assertEqual(args[1]["balance"]["total_asset"], 10000000.0)

    def test_logger_callback(self):
        """Test Logger callback handler."""
        mock_callback = MagicMock()
        self.logger.add_callback(mock_callback)
        
        log = self.logger.get_logger("TestLogger")
        log.info("Test Message")
        
        mock_callback.assert_called()
        call_args = mock_callback.call_args[0]
        self.assertEqual(call_args[0], logging.INFO) # Level
        self.assertIn("Test Message", call_args[1]) # Message

if __name__ == "__main__":
    unittest.main()
