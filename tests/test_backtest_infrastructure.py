import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import os
import sys
from datetime import datetime, timedelta

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import manage_data
from scripts import run_backtest_with_csv

class TestBacktestInfrastructure(unittest.TestCase):
    
    def setUp(self):
        # Setup dummy data for tests
        self.dummy_ohlcv = pd.DataFrame({
            "Date": [datetime(2023, 1, 1), datetime(2023, 1, 2)],
            "Code": ["005930", "005930"],
            "Name": ["Samsung", "Samsung"],
            "Open": [100, 110],
            "High": [120, 130],
            "Low": [90, 100],
            "Close": [110, 120],
            "Volume": [1000, 2000]
        })
        
    @patch("scripts.manage_data.stock")
    @patch("scripts.manage_data.os.makedirs")
    @patch("scripts.manage_data.pd.DataFrame.to_csv")
    def test_manage_data_download(self, mock_to_csv, mock_makedirs, mock_stock):
        # Mock ticker list
        mock_stock.get_market_ticker_list.return_value = ["005930", "000660"]
        mock_stock.get_market_ticker_name.side_effect = lambda x: "Samsung" if x == "005930" else "Hynix"
        mock_stock.get_etf_ticker_list.return_value = []
        
        # Mock daily OHLCV
        mock_stock.get_market_ohlcv.return_value = pd.DataFrame({
            "Code": ["005930", "000660"],
            "Open": [100, 200],
            "High": [110, 210],
            "Low": [90, 190],
            "Close": [105, 205],
            "Volume": [1000, 2000]
        })
        
        # Run download (limit loop for test speed)
        with patch("scripts.manage_data.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2020, 1, 5)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # We need to mock the range in download_initial_data or just test update_data
            # Testing update_data is enough as download calls it.
            
            # Mock file existence to force create
            with patch("scripts.manage_data.os.path.exists", return_value=False):
                manage_data.download_initial_data(start_year=2020)
                
        # Verify calls
        self.assertTrue(mock_stock.get_market_ticker_list.called)
        self.assertTrue(mock_to_csv.called)

    def test_filter_tickers(self):
        tickers = ["005930", "123450", "999999", "005935"] # Normal, Normal, SPAC, Preferred
        
        with patch("scripts.manage_data.stock") as mock_stock:
            mock_stock.get_etf_ticker_list.return_value = []
            mock_stock.get_market_ticker_name.side_effect = lambda x: "Samsung" if x == "005930" else ("SPAC" if x == "999999" else "Other")
            
            filtered = manage_data.filter_tickers(tickers, "20230101")
            
            # Should keep 005930 and 123450
            # Should remove 999999 (SPAC name) and 005935 (Preferred, ends with 5)
            codes = [f[0] for f in filtered]
            self.assertIn("005930", codes)
            self.assertIn("123450", codes)
            self.assertNotIn("999999", codes)
            self.assertNotIn("005935", codes)

    @patch("scripts.run_backtest_with_csv.pd.read_csv")
    @patch("scripts.run_backtest_with_csv.os.path.exists")
    def test_run_backtest_loader(self, mock_exists, mock_read_csv):
        mock_exists.return_value = True
        mock_read_csv.return_value = self.dummy_ohlcv
        
        df = run_backtest_with_csv.load_data()
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]['Code'], "005930")

    def test_run_single_backtest(self):
        # Prepare args
        ticker = "005930"
        name = "Samsung"
        group_df = self.dummy_ohlcv.copy()
        group_df.columns = ["date", "code", "name", "open", "high", "low", "close", "volume"] # Lowercase expected by some logic?
        # Wait, run_single_backtest expects original columns and lowercases them.
        # My dummy has Title Case.
        
        strategy_name = "VolatilityBreakout"
        index_data = {}
        config = {
            "initial_capital": 10000000,
            "commission_rate": 0.0,
            "slippage_rate": 0.0
        }
        
        args = (ticker, name, self.dummy_ohlcv, strategy_name, index_data, config)
        
        result = run_backtest_with_csv.run_single_backtest(args)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['ticker'], ticker)
        self.assertIn('return', result)
        self.assertIn('trades_count', result)

if __name__ == '__main__':
    unittest.main()
