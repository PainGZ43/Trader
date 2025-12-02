import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestKeyLoading(unittest.TestCase):
    
    @patch('data.key_manager.key_manager')
    def test_kiwoom_client_key_loading(self, mock_key_manager):
        """Test that KiwoomRestClient loads keys from KeyManager."""
        from data.kiwoom_rest_client import KiwoomRestClient
        
        # Setup Mock
        mock_key_manager.get_active_key.return_value = {
            "app_key": "test_app_key",
            "secret_key": "test_secret_key",
            "type": "MOCK",
            "account_no": "12345678"
        }
        
        client = KiwoomRestClient()
        
        # We need to run async method get_token
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Mock _get_session to avoid actual network call
        client._get_session = MagicMock()
        client.session = MagicMock()
        client.session.post.return_value.__aenter__.return_value.status = 200
        client.session.post.return_value.__aenter__.return_value.json.return_value = {"access_token": "new_token"}
        
        token = loop.run_until_complete(client.get_token())
        
        # Verify KeyManager was called
        mock_key_manager.get_active_key.assert_called_once()
        
        print("\n[TEST] KiwoomRestClient loaded key from KeyManager successfully.")
        loop.close()

    @patch('core.secure_storage.secure_storage')
    @patch('core.config.config')
    def test_notification_manager_key_loading(self, mock_config, mock_storage):
        """Test that NotificationManager loads keys from SecureStorage."""
        from execution.notification import NotificationManager
        
        # Setup Mock
        mock_storage.get.side_effect = lambda k: {
            "kakao_app_key": "k_app_key",
            "kakao_access_token": "k_acc_token",
            "kakao_refresh_token": "k_ref_token"
        }.get(k)
        
        mock_config.get.return_value = None
        
        manager = NotificationManager()
        
        self.assertEqual(manager.kakao_app_key, "k_app_key")
        self.assertEqual(manager.kakao_token, "k_acc_token")
        self.assertEqual(manager.refresh_token, "k_ref_token")
        
        print("\n[TEST] NotificationManager loaded keys from SecureStorage successfully.")

if __name__ == '__main__':
    unittest.main()
