import sys
import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

# Mock dependencies before importing UI
with patch('core.database.db') as mock_db:
    mock_db.connect = AsyncMock()
    mock_db.execute = AsyncMock()
    
    from ui.main_window import MainWindow
    from data.data_collector import data_collector

class TestUIIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create QApplication instance if not exists
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_dashboard_update(self):
        async def run_test():
            # 1. Setup Mocks
            data_collector.ws_client = MagicMock()
            data_collector.ws_client.connect = AsyncMock()
            data_collector.ws_client.subscribe = AsyncMock()
            
            data_collector.market_schedule = MagicMock()
            data_collector.market_schedule.check_market_status.return_value = True
            
            # Mock DB (since on_realtime_data calls save_to_db)
            # We need to patch the 'db' imported in data_collector, or just mock save_to_db
            data_collector.save_to_db = AsyncMock()

            # 2. Initialize MainWindow
            window = MainWindow()
            dashboard = window.dashboard
            
            # 3. Simulate Data Reception
            test_data = {
                "code": "005930",
                "price": 80000,
                "change": "+2.5%",
                "volume": 15000000
            }
            
            # Call the callback directly (as if WS client called it)
            await data_collector.on_realtime_data(test_data)
            
            # Process events to allow signal to propagate
            # In a real app, signal emission is immediate but slot execution depends on loop.
            # Since we are in async test, we might need to yield.
            await asyncio.sleep(0.1)
            
            # 4. Verify Dashboard Update (Realtime)
            # Check if row exists
            row_count = dashboard.table.rowCount()
            found = False
            for r in range(row_count):
                item = dashboard.table.item(r, 0)
                if item and item.text() == "005930":
                    price_item = dashboard.table.item(r, 2)
                    self.assertEqual(price_item.text(), "80000")
                    found = True
                    break
            
            self.assertTrue(found, "Dashboard table should contain updated symbol")
            
            # 5. Verify Status Bar Update (STATUS event)
            status_event = {
                "type": "STATUS",
                "market_open": True,
                "api_connected": True
            }
            await data_collector.notify_observers(status_event)
            # Wait for signal
            await asyncio.sleep(0.1)
            
            # Check Status Bar Text
            status_text = window.status_bar.currentMessage()
            self.assertIn("API: Connected", status_text)
            self.assertIn("Market: OPEN", status_text)
            
            # 6. Verify Macro Update (MACRO event)
            macro_event = {
                "type": "MACRO",
                "indices": {"KOSPI": 2600.5, "KOSDAQ": 900.2},
                "exchange_rate": 1350.0
            }
            await data_collector.notify_observers(macro_event)
            await asyncio.sleep(0.1)
            
            # Check Labels
            self.assertIn("2600.5", dashboard.kospi_label.text())
            self.assertIn("900.2", dashboard.kosdaq_label.text())
            self.assertIn("1350.0", dashboard.usd_label.text())
            
            print("UI Integration Test (Full): PASS")

        # Run async test
        loop = QEventLoop(self.app)
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_test())

if __name__ == '__main__':
    unittest.main()
