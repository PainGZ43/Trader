import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from data.websocket_client import WebSocketClient
import websockets

@pytest.fixture
def ws_client():
    client = WebSocketClient()
    client.mock_mode = False
    client.ws_url = "ws://test.url"
    return client

@pytest.mark.asyncio
async def test_connect_success(ws_client):
    with patch('websockets.connect', new_callable=AsyncMock) as mock_connect, \
         patch('data.kiwoom_rest_client.kiwoom_client.get_token', new_callable=AsyncMock) as mock_token:
        
        mock_token.return_value = "test_token"
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws
        
        # Mock _listen to return immediately
        with patch.object(ws_client, '_listen', new_callable=AsyncMock), \
             patch.object(ws_client, '_monitor_connection', new_callable=AsyncMock):
            
            await ws_client.connect()
            
            assert ws_client.is_connected
            mock_connect.assert_called_once()

@pytest.mark.asyncio
async def test_reconnect_on_failure(ws_client):
    """Test that reconnect is called when initial connection fails."""
    with patch('websockets.connect', side_effect=Exception("Connection Failed")), \
         patch('data.kiwoom_rest_client.kiwoom_client.get_token', new_callable=AsyncMock) as mock_token, \
         patch.object(ws_client, '_reconnect', new_callable=AsyncMock) as mock_reconnect:
        
        mock_token.return_value = "test_token"
        
        await ws_client.connect()
        
        assert not ws_client.is_connected
        mock_reconnect.assert_called_once()

@pytest.mark.asyncio
async def test_watchdog_trigger(ws_client):
    """Test that watchdog triggers reconnect when no data received."""
    ws_client.is_connected = True
    ws_client.last_msg_time = asyncio.get_event_loop().time() - 70 # 70s ago
    ws_client.websocket = AsyncMock()
    
    with patch.object(ws_client, '_reconnect', new_callable=AsyncMock) as mock_reconnect:
        # Run monitor for a short time
        task = asyncio.create_task(ws_client._monitor_connection())
        await asyncio.sleep(0.1)
        ws_client._stop_event.set()
        await task
        
        assert not ws_client.is_connected
        mock_reconnect.assert_called_once()
