import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QMessageBox

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.main_window import MainWindow

class TestApiKeyCheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create QApplication if it doesn't exist
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
            
        # Force Language to English for consistent assertions
        from core.language import language_manager
        language_manager.set_language("en")

    @patch('ui.main_window.QMessageBox')
    @patch('ui.main_window.SettingsDialog')
    @patch('data.key_manager.key_manager')
    def test_check_api_keys_missing(self, mock_key_manager, mock_settings_dialog, mock_msgbox):
        """Test that missing keys trigger a warning and open settings."""
        
        # Setup Mocks
        mock_key_manager.get_active_key.return_value = None # No active key
        
        # Mock QMessageBox.warning to return Yes
        mock_msgbox.warning.return_value = QMessageBox.StandardButton.Yes
        mock_msgbox.StandardButton = QMessageBox.StandardButton # Restore enum
        
        # Initialize MainWindow
        window = MainWindow()
        
        # Call check_api_keys directly (bypassing QTimer for test)
        window.check_api_keys()
        
        # Verify Warning was shown
        mock_msgbox.warning.assert_called_once()
        args, _ = mock_msgbox.warning.call_args
        self.assertIn("API Key Missing", args[1]) # Title check
        
        # Verify SettingsDialog was opened
        mock_settings_dialog.assert_called_once()
        instance = mock_settings_dialog.return_value
        instance.exec.assert_called_once()
        
        print("\n[TEST] API Key Check Logic Verified: Warning shown and Settings requested.")

    @patch('ui.main_window.QMessageBox')
    @patch('data.key_manager.key_manager')
    def test_check_api_keys_present(self, mock_key_manager, mock_msgbox):
        """Test that present keys do NOT trigger a warning."""
        
        # Setup Mocks
        mock_key_manager.get_active_key.return_value = {"uuid": "123", "app_key": "abc"} # Active key exists
        
        # Initialize MainWindow
        window = MainWindow()
        
        # Call check_api_keys
        window.check_api_keys()
        
        # Verify Warning was NOT shown
        mock_msgbox.warning.assert_not_called()
        
        print("\n[TEST] API Key Check Logic Verified: No warning when keys exist.")

if __name__ == '__main__':
    unittest.main()
