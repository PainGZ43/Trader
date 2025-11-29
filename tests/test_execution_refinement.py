import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from execution.risk_manager import RiskManager
from execution.order_manager import OrderManager
from strategy.base_strategy import Signal
from core.database import Database

class TestExecutionRefinement(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self):
        self.db = Database()
        self.db.db_path = ":memory:"
        await self.db.connect()
        
        # Patch db in order_manager
        # We need to patch 'execution.order_manager.db' to point to our test db
        # But since we can't easily patch global variable in imported module if it's already imported,
        # we will rely on the fact that core.database.db is a singleton instance.
        # We can just use the real db instance but connect it to memory.
        # However, core.database.db is instantiated in core.database.
        # Let's try to set the global db instance's conn.
        from core.database import db as global_db
        global_db.conn = self.db.conn
        global_db.db_path = ":memory:"

    async def asyncTearDown(self):
        await self.db.close()

    async def test_risk_manager_structure(self):
        """Test RiskManager checks including Portfolio Exposure."""
        rm = RiskManager()
        rm.config["max_portfolio_exposure"] = 0.5
        
        # Mock Notification
        rm.notification_manager = AsyncMock()
        
        signal = Signal("005930", "BUY", 1000, datetime.now(), "Test")
        
        # Case 1: Safe
        # Total Asset: 1000, Deposit: 600 -> Exposure: 400/1000 = 0.4 < 0.5 (OK)
        account_info = {"total_asset": 1000, "deposit": 600, "daily_pnl": 0}
        self.assertTrue(rm.check_risk(signal, account_info))
        
        # Case 2: Exposure Limit Exceeded
        # Total Asset: 1000, Deposit: 400 -> Exposure: 600/1000 = 0.6 > 0.5 (Fail)
        account_info = {"total_asset": 1000, "deposit": 400, "daily_pnl": 0}
        self.assertFalse(rm.check_risk(signal, account_info))
        
        # Case 3: Daily Loss Limit
        rm.config["max_daily_loss_rate"] = 0.03
        # Loss 40 on 1000 -> 4% > 3% (Fail)
        account_info = {"total_asset": 1000, "deposit": 600, "daily_pnl": -40}
        self.assertFalse(rm.check_risk(signal, account_info))

    async def test_order_persistence(self):
        """Test OrderManager saves and loads orders."""
        kiwoom_mock = AsyncMock()
        om = OrderManager(kiwoom_mock)
        
        # Initialize DB
        await om.initialize()
        
        # 1. Send Order -> Should save to DB
        kiwoom_mock.send_order.return_value = {"rt_cd": "0", "output": {"order_no": "ORD1"}}
        signal = Signal("005930", "BUY", 1000, datetime.now(), "Test")
        
        await om.send_order(signal, 10, "ACC1")
        
        # Check Memory
        self.assertIn("ORD1", om.active_orders)
        
        # Check DB
        rows = await self.db.fetch_all("SELECT * FROM active_orders WHERE order_id='ORD1'")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "005930") # Symbol
        
        # 2. Restart (Create new OrderManager)
        om2 = OrderManager(kiwoom_mock)
        await om2.initialize() # Should load from DB
        
        self.assertIn("ORD1", om2.active_orders)
        self.assertEqual(om2.active_orders["ORD1"]["symbol"], "005930")
        
        # 3. Fill Order -> Should remove from DB
        event_data = {
            "order_no": "ORD1",
            "status": "FILLED",
            "exec_qty": 10,
            "qty": 10
        }
        await om2.on_order_event(event_data)
        
        self.assertNotIn("ORD1", om2.active_orders)
        rows = await self.db.fetch_all("SELECT * FROM active_orders WHERE order_id='ORD1'")
        self.assertEqual(len(rows), 0)

if __name__ == "__main__":
    unittest.main()
