import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import MagicMock, AsyncMock
from core.event_bus import Event
from data.data_collector import DataCollector

async def verify_watchlist_subscription():
    print("Verifying Watchlist Subscription Logic...")
    
    # Mock Dependencies
    mock_ws_client = MagicMock()
    mock_ws_client.subscribe = AsyncMock()
    mock_ws_client.add_callback = MagicMock()
    
    # Patch DataCollector's ws_client
    # We need to patch it before instantiation or replace it after
    # Since DataCollector imports ws_client from data.websocket_client, we need to patch that module
    
    import data.data_collector
    data.data_collector.ws_client = mock_ws_client
    
    # Re-instantiate DataCollector to use mock
    collector = DataCollector()
    
    # Mock Event
    codes = ["005930", "000660", "035420"]
    event = Event("watchlist.updated", {"codes": codes})
    
    # Trigger Handler
    await collector._on_watchlist_updated(event)
    
    # Verify Subscription
    # Should be called with joined string
    expected_tr_key = "005930;000660;035420"
    mock_ws_client.subscribe.assert_called_with("H0STCNT0", expected_tr_key)
    
    print("[OK] Subscription called with correct codes.")
    
    # Verify Chunking (Test with > 50 codes)
    many_codes = [f"{i:06d}" for i in range(60)]
    event_many = Event("watchlist.updated", {"codes": many_codes})
    
    mock_ws_client.subscribe.reset_mock()
    await collector._on_watchlist_updated(event_many)
    
    # Should be called twice
    assert mock_ws_client.subscribe.call_count == 2
    print("[OK] Chunking logic verified (2 calls for 60 codes).")

if __name__ == "__main__":
    asyncio.run(verify_watchlist_subscription())
