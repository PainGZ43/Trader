import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestMacroData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
            
        # Force Language to English for consistent assertions
        from core.language import language_manager
        language_manager.set_language("en")

    @patch('data.macro_collector.event_bus')
    @patch('aiohttp.ClientSession.get')
    def test_fetch_global_indices(self, mock_get, mock_event_bus):
        """Test fetching global indices and publishing event."""
        from data.macro_collector import macro_collector
        
        # Mock Response
        mock_response = MagicMock()
        mock_response.status = 200
        
        # Make json() return an awaitable that resolves to the dict
        f = asyncio.Future()
        f.set_result({
            "chart": {
                "result": [{
                    "meta": {
                        "regularMarketPrice": 15000.0,
                        "chartPreviousClose": 14900.0
                    }
                }]
            }
        })
        mock_response.json.return_value = f
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Run Async Method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(macro_collector.update_global_indices())
        
        self.assertEqual(macro_collector.indices["NASDAQ"], 15000.0)
        self.assertIn("+0.67%", macro_collector.changes["NASDAQ"]) 
        
        print("\n[TEST] MacroCollector fetched global indices and calculated change successfully.")
        loop.close()

    @patch('data.macro_collector.event_bus')
    def test_on_realtime_data(self, mock_event_bus):
        """Test handling real-time index data."""
        from data.macro_collector import macro_collector
        
        # Mock Data
        data = {
            "type": "JISU",
            "code": "001", # KOSPI
            "price": "2600.50",
            "change_pct": "+1.23%"
        }
        
        # Run Async Method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(macro_collector.on_realtime_data(data))
        
        self.assertEqual(macro_collector.indices["KOSPI"], 2600.50)
        self.assertEqual(macro_collector.changes["KOSPI"], "+1.23%")
        
        # Verify Event Published
        mock_event_bus.publish.assert_called()
        args, _ = mock_event_bus.publish.call_args
        self.assertEqual(args[0], "market.data.macro")
        self.assertEqual(args[1]["indices"]["KOSPI"], 2600.50)
        
        print("\n[TEST] MacroCollector processed real-time index data successfully.")
        loop.close()

    def test_header_bar_update(self):
        """Test HeaderBar UI update with changes."""
        from ui.widgets.header_bar import HeaderBar
        
        header = HeaderBar()
        
        data = {
            "indices": {
                "KOSPI": 2600.0,
                "KOSDAQ": 900.0,
                "NASDAQ": 15000.0,
                "S&P500": 4500.0,
                "DowJones": 35000.0,
                "VIX": 15.0
            },
            "changes": {
                "KOSPI": "+0.5%",
                "KOSDAQ": "-0.2%",
                "NASDAQ": "+1.2%",
                "S&P500": "+0.8%",
                "DowJones": "+0.3%",
                "VIX": "-5.0%"
            },
            "exchange_rate": 1300.0
        }
        
        header.update_macro(data)
        
        # Verify Labels
        self.assertIn("KOSPI 2,600.00 (+0.5%)", header.kospi_label.text())
        self.assertIn("KOSDAQ 900.00 (-0.2%)", header.kosdaq_label.text())
        self.assertIn("NASDAQ 15,000.00 (+1.2%)", header.nasdaq_label.text())
        
        # Verify Color (Red for +)
        style = header.kospi_label.styleSheet()
        self.assertIn("#ff5252", style)
        
        # Verify Color (Blue for -)
        style = header.kosdaq_label.styleSheet()
        self.assertIn("#448aff", style)
        
    def test_header_bar_no_data(self):
        """Test HeaderBar UI update with missing data (0.0)."""
        from ui.widgets.header_bar import HeaderBar
        
        header = HeaderBar()
        
        data = {
            "indices": {
                "KOSPI": 0.0,
                "KOSDAQ": 0.0,
                "NASDAQ": 0.0,
                "S&P500": 0.0,
                "DowJones": 0.0,
                "VIX": 0.0
            },
            "changes": {},
            "exchange_rate": 0.0
        }
        
        header.update_macro(data)
        
        # Verify Labels show "--"
        self.assertIn("KOSPI --", header.kospi_label.text())
        self.assertIn("KOSDAQ --", header.kosdaq_label.text())
        
        # Verify Color (Grey)
        style = header.kospi_label.styleSheet()
        self.assertIn("#888", style)
        
        print("\n[TEST] HeaderBar correctly displays '--' for missing data.")

if __name__ == '__main__':
    unittest.main()
