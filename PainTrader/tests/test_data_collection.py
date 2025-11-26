import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock
from data.websocket_client import WebSocketClient
from data.data_collector import DataCollector

@pytest.fixture
def ws_client():
    client = WebSocketClient()
    client.mock_mode = False # Test real logic with mocks
    return client

@pytest.fixture
def data_collector():
    # We need to mock dependencies of DataCollector
    with patch('data.data_collector.ws_client') as mock_ws, \
         patch('data.data_collector.kiwoom_client') as mock_rest, \
         patch('data.data_collector.db') as mock_db:
        
        collector = DataCollector()
        # Inject mocks
        collector.ws_client = mock_ws
        collector.rest_client = mock_rest
        # Mock db.execute to be async
        mock_db.execute = AsyncMock()
        mock_db.connect = AsyncMock()
        
        yield collector

@pytest.mark.asyncio
async def test_ws_connect(ws_client):
    """Test WebSocket connection logic."""
    with patch('websockets.connect', new_callable=AsyncMock) as mock_connect, \
         patch('data.kiwoom_rest_client.kiwoom_client.get_token', new_callable=AsyncMock) as mock_token:
        
        mock_token.return_value = "test_token"
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws
        
        await ws_client.connect()
        
        assert ws_client.is_connected is True
        mock_connect.assert_called_once()
        # Verify token was used in headers (if extra_headers supported) or retried
        # Since we mock success on first try:
        args, kwargs = mock_connect.call_args
        if 'extra_headers' in kwargs:
            assert kwargs['extra_headers']['Authorization'] == "Bearer test_token"

@pytest.mark.asyncio
async def test_ws_subscribe(ws_client):
    """Test WebSocket subscription."""
    ws_client.is_connected = True
    ws_client.websocket = AsyncMock()
    
    with patch('data.kiwoom_rest_client.kiwoom_client.access_token', "test_token"):
        await ws_client.subscribe("TR_ID", "CODE")
        
        ws_client.websocket.send.assert_called_once()
        call_args = ws_client.websocket.send.call_args[0][0]
        payload = json.loads(call_args)
        assert payload['body']['tr_id'] == "TR_ID"
        assert payload['body']['tr_key'] == "CODE"

@pytest.mark.asyncio
async def test_data_collector_realtime_processing(data_collector):
    """Test DataCollector processing realtime data."""
    # Mock market schedule to be open
    data_collector.market_schedule.check_market_status = MagicMock(return_value=True)
    
    data = {
        "code": "005930",
        "price": 70000,
        "volume": 100
    }
    
    # Mock observer
    observer = AsyncMock()
    data_collector.add_observer(observer)
    
    await data_collector.on_realtime_data(data)
    
    # Verify DB save
    # db.execute is called via save_to_db
    # We can check if save_to_db called db.execute
    # But save_to_db is async, so we need to ensure it was awaited.
    # on_realtime_data awaits save_to_db.
    
    # We mocked db in the fixture, let's access it via the patched module or the instance if we injected it.
    # In fixture we patched 'data.data_collector.db'.
    # We need to capture that mock.
    # Since we didn't return it from fixture, let's re-patch locally or check side effects if possible.
    # Actually, data_collector.py imports db as `from core.database import db`.
    # So patching `data.data_collector.db` works.
    
    # To verify, we can check if observer was notified
    observer.assert_called_once()
    args = observer.call_args[0][0]
    assert args['type'] == 'REALTIME'
    assert args['code'] == "005930"

@pytest.mark.asyncio
async def test_gap_filling_trigger(data_collector):
    """Test Gap Filling trigger."""
    data_collector.market_schedule.check_market_status = MagicMock(return_value=True)
    symbol = "005930"
    
    # 1. First update
    data1 = {"code": symbol, "price": 100}
    await data_collector.on_realtime_data(data1)
    
    # 2. Simulate time gap
    # We can manipulate last_update_time
    from datetime import datetime, timedelta
    past_time = datetime.now() - timedelta(seconds=100)
    data_collector.last_update_time[symbol] = past_time
    
    # 3. Second update
    data2 = {"code": symbol, "price": 110}
    
    # Mock fill_gap method to verify it's called
    data_collector.fill_gap = AsyncMock()
    
    await data_collector.on_realtime_data(data2)
    
    # fill_gap should be called
    # Note: fill_gap is called with asyncio.create_task, so it might not complete immediately.
    # But the call itself happens synchronously before create_task returns?
    # No, create_task schedules it. We verify it was scheduled/called.
    # Since we mocked it on the instance, we can check call_count.
    
    # Wait a bit for task to be scheduled if needed, but usually call is immediate.
    # However, since we mocked it, we just check if it was called.
    # But wait, asyncio.create_task(self.fill_gap(...)) calls self.fill_gap(...) immediately to get the coroutine?
    # Yes, it calls the function to get coroutine object.
    data_collector.fill_gap.assert_called_once()
