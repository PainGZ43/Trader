import sys
import os
import unittest
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.key_manager import key_manager

class TestKeyManagerMethods(unittest.TestCase):
    def test_get_keys(self):
        print("\n[TEST] Testing get_keys...")
        keys = key_manager.get_keys()
        self.assertIsInstance(keys, list)
        print(f"Keys found: {len(keys)}")
        for k in keys:
            self.assertIn("masked_account_no", k)
            self.assertIn("is_active", k)
            self.assertIn("is_valid", k)
            print(f" - {k['owner']}: {k['masked_account_no']} (Active: {k['is_active']})")

    def test_expiry_alert_settings(self):
        print("\n[TEST] Testing expiry alert settings...")
        original_days = key_manager.get_expiry_alert_days()
        print(f"Original alert days: {original_days}")
        
        test_days = 14
        key_manager.set_expiry_alert_days(test_days)
        self.assertEqual(key_manager.get_expiry_alert_days(), test_days)
        print(f"Set alert days to: {test_days}")
        
        # Restore original
        key_manager.set_expiry_alert_days(original_days)
        self.assertEqual(key_manager.get_expiry_alert_days(), original_days)
        print(f"Restored alert days to: {original_days}")

    def test_check_expiration(self):
        print("\n[TEST] Testing check_expiration...")
        # We can't easily add a fake expiring key without modifying the file, 
        # so we'll just check if the method runs without error and returns a list.
        warnings = key_manager.check_expiration()
        self.assertIsInstance(warnings, list)
        print(f"Expiration warnings: {warnings}")

if __name__ == '__main__':
    unittest.main()
