import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from execution.account_manager import AccountManager

class TestAccountManagerCoverage(unittest.TestCase):
    def setUp(self):
        self.mock_exchange = MagicMock()
        self.am = AccountManager(self.mock_exchange)
        # Suppress logging during tests
        self.am.logger = MagicMock()

    def async_run(self, coro):
        return asyncio.run(coro)

    def test_update_balance_success_real_format(self):
        """Test successful update with Real API flat format."""
        mock_data = {
            "prsm_dpst_aset_amt": "10000000",
            "tot_evlt_amt": "5000000",
            "tot_evlt_pl": "500000",
            "tot_pur_amt": "4500000",
            "tot_prft_rt": "11.11",
            "deposit": "5000000",
            "acnt_evlt_remn_indv_tot": [
                {
                    "stk_cd": "A005930",
                    "stk_nm": "Samsung",
                    "rmnd_qty": "10",
                    "pur_pric": "60000",
                    "cur_prc": "70000",
                    "evlt_amt": "700000",
                    "prft_rt": "16.66"
                }
            ]
        }
        self.mock_exchange.get_account_balance = AsyncMock(return_value=mock_data)
        
        self.async_run(self.am.update_balance())
        
        self.assertEqual(self.am.balance["total_asset"], 10000000.0)
        self.assertEqual(self.am.balance["total_eval"], 5000000.0)
        self.assertEqual(self.am.balance["total_pnl"], 500000.0)
        self.assertEqual(self.am.balance["total_purchase"], 4500000.0)
        self.assertEqual(self.am.balance["total_return"], 11.11)
        self.assertEqual(len(self.am.positions), 1)
        self.assertEqual(self.am.positions["005930"]["name"], "Samsung")

    def test_update_balance_mock_format(self):
        """Test successful update with Mock API wrapped format."""
        mock_data = {
            "output": {
                "prsm_dpst_aset_amt": "2000",
                "tot_evlt_amt": "1000",
                "tot_evlt_pl_amt": "100", # Note: key diff
                "tot_pur_amt": "900",
                "tot_earning_rate": "10.0", # Note: key diff
                "deposit": "1000",
                "output_list": [] # Note: key diff
            }
        }
        self.mock_exchange.get_account_balance = AsyncMock(return_value=mock_data)
        
        self.async_run(self.am.update_balance())
        
        self.assertEqual(self.am.balance["total_asset"], 2000.0)
        self.assertEqual(self.am.balance["total_pnl"], 100.0)
        self.assertEqual(self.am.balance["total_return"], 10.0)
        self.assertEqual(len(self.am.positions), 0)

    def test_update_balance_api_error(self):
        """Test handling of API error (None response)."""
        self.mock_exchange.get_account_balance = AsyncMock(return_value=None)
        
        self.async_run(self.am.update_balance())
        
        # Should log warning and not crash
        self.am.logger.warning.assert_called()
        # Balance should remain default
        self.assertEqual(self.am.balance["total_asset"], 0.0)

    def test_update_balance_missing_fields(self):
        """Test handling of missing fields (partial data)."""
        mock_data = {
            "prsm_dpst_aset_amt": "5000"
            # Missing other fields
        }
        self.mock_exchange.get_account_balance = AsyncMock(return_value=mock_data)
        
        self.async_run(self.am.update_balance())
        
        self.assertEqual(self.am.balance["total_asset"], 5000.0)
        self.assertEqual(self.am.balance["total_pnl"], 0.0) # Default
        self.assertEqual(self.am.balance["total_purchase"], 0.0) # Default

    def test_update_balance_cash_estimation(self):
        """Test cash estimation logic when deposit is 0 but asset > 0."""
        mock_data = {
            "prsm_dpst_aset_amt": "10000",
            "tot_evlt_amt": "8000",
            "deposit": "0" # Explicit 0
        }
        self.mock_exchange.get_account_balance = AsyncMock(return_value=mock_data)
        
        self.async_run(self.am.update_balance())
        
        # Cash = Asset (10000) - Stock (8000) = 2000
        self.assertEqual(self.am.balance["deposit"], 2000.0)

    def test_check_buying_power(self):
        """Test check_buying_power logic."""
        self.am.balance["deposit"] = 10000
        self.am.balance["total_asset"] = 100000
        self.am.min_cash_ratio = 0.1 # 10%
        
        # 1. Enough cash, Ratio OK (10%)
        self.assertTrue(self.am.check_buying_power(5000))
        
        # 2. Not enough cash
        self.assertFalse(self.am.check_buying_power(15000))
        
        # 3. Low Cash Ratio
        self.am.balance["deposit"] = 5000 # 5% ratio
        self.assertFalse(self.am.check_buying_power(1000)) # Should fail due to ratio check

if __name__ == '__main__':
    unittest.main()
