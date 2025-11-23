import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from datetime import datetime, timedelta
from data.kiwoom_rest_client import KiwoomRestClient
from data.websocket_client import WebSocketClient

class TestAPICompliance(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    @patch('data.kiwoom_rest_client.config')
    @patch('data.kiwoom_rest_client.secure_storage')
    @patch('aiohttp.ClientSession')
    def test_rest_api_request_format(self, mock_session_cls, mock_storage, mock_config):
        # Setup
        mock_config.get.side_effect = lambda k, d=None: {
            "KIWOOM_API_URL": "https://api.kiwoom.com",
            "MOCK_MODE": False
        }.get(k, d)
        mock_storage.get.return_value = "test_key"
        
        client = KiwoomRestClient()
        client.access_token = "test_token"
        client.token_expiry = datetime.now() + timedelta(hours=1) # Valid token
        
        # Mock Session and Request
        mock_session = AsyncMock()
        mock_session_cls.return_value = mock_session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"result": "ok"}
        mock_session.request.return_value.__aenter__.return_value = mock_response
        
        # Execute
        # We need to mock get_token to avoid actual call if token is missing, 
        # but here we set access_token so it should skip.
        
        self.loop.run_until_complete(client.get_current_price("005930"))
        
        # Verify
        # Check URL
        args, kwargs = mock_session.request.call_args
        method, url = args
        self.assertEqual(method, "POST")
        self.assertEqual(url, "https://api.kiwoom.com/api/dostk/mrkcond")
        
        # Check Headers
        headers = kwargs['headers']
        self.assertEqual(headers['api-id'], 'ka10004')
        self.assertEqual(headers['appkey'], 'test_key')
        self.assertEqual(headers['appsecret'], 'test_key')
        self.assertIn("Bearer test_token", headers['Authorization'])
        
        # Check Payload
        data = kwargs['json']
        self.assertEqual(data['stk_cd'], "005930")
        
        print("REST API Compliance Test: PASS")

    @patch('data.websocket_client.config')
    @patch('data.websocket_client.secure_storage')
    @patch('data.kiwoom_rest_client.kiwoom_client') # Patch where it is defined, since it's imported inside method
    @patch('websockets.connect')
    def test_websocket_connection_format(self, mock_ws_connect, mock_kiwoom, mock_storage, mock_config):
        # Setup
        mock_config.get.side_effect = lambda k, d=None: {
            "KIWOOM_WS_URL": "wss://api.kiwoom.com:10000/api/dostk/websocket",
            "MOCK_MODE": False
        }.get(k, d)
        mock_storage.get.return_value = "test_key"
        mock_kiwoom.get_token = AsyncMock(return_value="test_token")
        
        client = WebSocketClient()
        
        # Mock WS Connect
        mock_ws_connect.return_value = AsyncMock()
        
        # Execute
        self.loop.run_until_complete(client.connect())
        
        # Verify
        args, kwargs = mock_ws_connect.call_args
        url = args[0]
        self.assertEqual(url, "wss://api.kiwoom.com:10000/api/dostk/websocket")
        
        # Check Headers (extra_headers)
        headers = kwargs['extra_headers']
        self.assertIn("Bearer test_token", headers['Authorization'])
        self.assertEqual(headers['Content-Type'], "application/json; charset=utf-8")
        
        print("WebSocket Compliance Test: PASS")

if __name__ == '__main__':
    from datetime import datetime, timedelta
    unittest.main()
