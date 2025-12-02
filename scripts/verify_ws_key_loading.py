import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestWSKeyLoading(unittest.TestCase):
    @patch('data.key_manager.key_manager.get_active_key')
    @patch('core.secure_storage.secure_storage.get')
    def test_ws_client_key_loading(self, mock_secure_get, mock_get_active_key):
        """Test that WebSocketClient uses KeyManager and NOT SecureStorage for Kiwoom keys."""
        
        # Mock KeyManager to return a key
        mock_get_active_key.return_value = {
            "app_key": "TEST_APP_KEY",
            "secret_key": "TEST_SECRET_KEY",
            "type": "MOCK"
        }
        
        # Initialize WebSocketClient
        from data.websocket_client import WebSocketClient
        ws = WebSocketClient()
        
        # Verify keys are loaded from KeyManager
        self.assertEqual(ws.app_key, "TEST_APP_KEY")
        self.assertEqual(ws.secret_key, "TEST_SECRET_KEY")
        
        # Verify SecureStorage was NOT called for Kiwoom keys
        # It might be called for other things if any, but let's check args
        for call in mock_secure_get.call_args_list:
            args, _ = call
            self.assertNotIn("KIWOOM_APP_KEY", args)
            self.assertNotIn("KIWOOM_SECRET_KEY", args)
            
        print("\n[TEST] WebSocketClient loaded keys from KeyManager correctly.")

if __name__ == '__main__':
    unittest.main()
