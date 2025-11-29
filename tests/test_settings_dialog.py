import sys
import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QDialog

# Mock SecureStorage and Config
with patch('core.secure_storage.secure_storage') as mock_storage, \
     patch('core.config.config') as mock_config:
    
    from ui.settings_dialog import SettingsDialog

class TestSettingsDialog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_load_settings(self):
        # Setup Mocks
        with patch('ui.settings_dialog.secure_storage') as mock_storage, \
             patch('ui.settings_dialog.config') as mock_config:
            
            mock_storage.get.side_effect = lambda k: {"KIWOOM_APP_KEY": "secure_app", "KIWOOM_SECRET_KEY": "secure_secret"}.get(k)
            mock_config.get.return_value = "config_value"
            
            dialog = SettingsDialog()
            
            # Verify Load
            self.assertEqual(dialog.app_key_input.text(), "secure_app")
            self.assertEqual(dialog.secret_key_input.text(), "secure_secret")
            # Account No not in secure mock, should fall back to config (but secure_storage.get returns None if not found, 
            # and our lambda returns None for unknown keys)
            # Wait, lambda returns None for ACCOUNT_NO.
            # Code: secure_storage.get(...) or config.get(...)
            # So it should call config.get("ACCOUNT_NO")
            # mock_config.get("ACCOUNT_NO") -> "config_value"
            self.assertEqual(dialog.account_input.text(), "config_value")
            
            print("Settings Load Test: PASS")

    def test_save_settings(self):
        with patch('ui.settings_dialog.secure_storage') as mock_storage, \
             patch('ui.settings_dialog.config') as mock_config, \
             patch('PyQt6.QtWidgets.QMessageBox.information') as mock_info:
            
            # Configure Mocks for init load
            mock_storage.get.return_value = ""
            mock_config.get.return_value = ""
            
            dialog = SettingsDialog()
            
            # Set Inputs
            dialog.app_key_input.setText("new_app_key")
            dialog.secret_key_input.setText("new_secret_key")
            dialog.account_input.setText("new_account")
            
            # Save
            dialog.save_settings()
            
            # Verify Save calls
            mock_storage.save.assert_any_call("KIWOOM_APP_KEY", "new_app_key")
            mock_storage.save.assert_any_call("KIWOOM_SECRET_KEY", "new_secret_key")
            mock_storage.save.assert_any_call("ACCOUNT_NO", "new_account")
            
            mock_config.set.assert_any_call("KIWOOM_APP_KEY", "new_app_key")
            
            print("Settings Save Test: PASS")

if __name__ == '__main__':
    unittest.main()
