import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from data.kiwoom_rest_client import KiwoomRestClient
from data.websocket_client import WebSocketClient

@pytest.mark.asyncio
async def test_rest_api_request_format():
    with patch('data.kiwoom_rest_client.config') as mock_config, \
         patch('data.kiwoom_rest_client.secure_storage') as mock_storage, \
         patch('aiohttp.ClientSession') as mock_session_cls:
         
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
        await client.get_current_price("005930")
        
        # Verify
        # Check URL
        args, kwargs = mock_session.request.call_args
        method, url = args
        assert method == "POST"
        assert url == "https://api.kiwoom.com/api/dostk/mrkcond"
        
        # Check Headers
        headers = kwargs['headers']
        assert headers['api-id'] == 'ka10004'
        assert headers['appkey'] == 'test_key'
        assert headers['appsecret'] == 'test_key'
        assert "Bearer test_token" in headers['Authorization']
        
        # Check Payload
        data = kwargs['json']
        assert data['stk_cd'] == "005930"

@pytest.mark.asyncio
async def test_websocket_connection_format():
    with patch('data.websocket_client.config') as mock_config, \
         patch('data.websocket_client.secure_storage') as mock_storage, \
         patch('data.kiwoom_rest_client.kiwoom_client') as mock_kiwoom, \
         patch('websockets.connect') as mock_ws_connect:
         
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
        
        # Mock background tasks to avoid infinite loops
        with patch.object(client, '_listen', new_callable=AsyncMock), \
             patch.object(client, '_monitor_connection', new_callable=AsyncMock):
            
            # Execute
            await client.connect()
            
            # Verify
            args, kwargs = mock_ws_connect.call_args
            url = args[0]
            assert url == "wss://api.kiwoom.com:10000/api/dostk/websocket"
            
            # Check Headers (extra_headers)
            headers = kwargs['extra_headers']
            assert "Bearer test_token" in headers['Authorization']
            assert headers['Content-Type'] == "application/json;charset=UTF-8"
