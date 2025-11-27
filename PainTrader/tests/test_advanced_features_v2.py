import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from data.market_schedule import MarketSchedule
from data.data_collector import DataCollector
from core.database import Database

@pytest.mark.asyncio
async def test_market_schedule_holidays():
    """Test MarketSchedule holiday check using holidays package."""
    schedule = MarketSchedule()
    
    # Mock datetime to a known holiday (e.g., Christmas 2024)
    # Note: holidays package should have 2024-12-25 as holiday
    with patch('data.market_schedule.datetime') as mock_dt:
        # Mock now() to return a specific datetime
        # Since we are patching the class, we need to make sure side_effect or return_value works as expected.
        # However, datetime is immutable. Usually we patch the module where it is imported.
        # In market_schedule.py: from datetime import datetime
        # So patching 'data.market_schedule.datetime' is correct.
        
        # 1. Holiday (Christmas)
        mock_dt.now.return_value = datetime(2024, 12, 25, 10, 0)
        # We don't need to mock weekday() or strftime() because return_value is a real datetime object
        assert schedule.is_business_day() is False

        # 2. Business Day (Thursday)
        mock_dt.now.return_value = datetime(2024, 12, 26, 10, 0)
        assert schedule.is_business_day() is True

@pytest.mark.asyncio
async def test_candle_aggregation():
    """Test DataCollector 1-minute candle aggregation."""
    # Setup DataCollector with mocks
    with patch('data.data_collector.db') as mock_db, \
         patch('core.event_bus.event_bus') as mock_event_bus:
        
        mock_db.execute = AsyncMock()
        mock_event_bus.publish = MagicMock()
        
        collector = DataCollector()
        collector.market_schedule.check_market_status = MagicMock(return_value=True)
        collector.save_to_db = AsyncMock() # Mock internal save to avoid DB calls
        
        symbol = "005930"
        
        # 1. First Tick (09:00:05)
        t1 = datetime(2024, 1, 1, 9, 0, 5)
        with patch('data.data_collector.datetime') as mock_dt:
            mock_dt.now.return_value = t1
            await collector.on_realtime_data({"code": symbol, "price": 100, "volume": 10})
            
        # Buffer should be initialized
        assert symbol in collector.realtime_buffer
        assert collector.realtime_buffer[symbol]["open"] == 100
        assert collector.realtime_buffer[symbol]["volume"] == 10
        
        # 2. Second Tick (09:00:55)
        t2 = datetime(2024, 1, 1, 9, 0, 55)
        with patch('data.data_collector.datetime') as mock_dt:
            mock_dt.now.return_value = t2
            await collector.on_realtime_data({"code": symbol, "price": 110, "volume": 20})
            
        # Buffer updated
        assert collector.realtime_buffer[symbol]["high"] == 110
        assert collector.realtime_buffer[symbol]["volume"] == 30 # 10 + 20
        
        # 3. Third Tick (09:01:05) -> Minute Changed
        t3 = datetime(2024, 1, 1, 9, 1, 5)
        with patch('data.data_collector.datetime') as mock_dt:
            mock_dt.now.return_value = t3
            await collector.on_realtime_data({"code": symbol, "price": 105, "volume": 5})
            
        # Candle Closed Event should be fired for 09:00
        mock_event_bus.publish.assert_called_once()
        args = mock_event_bus.publish.call_args[0]
        assert args[0] == "CANDLE_CLOSED"
        payload = args[1]
        assert payload["symbol"] == symbol
        assert payload["close"] == 110
        assert payload["volume"] == 30
        assert payload["timestamp"] == datetime(2024, 1, 1, 9, 0, 0)

@pytest.mark.asyncio
async def test_db_cleanup():
    """Test Database cleanup logic."""
    # Use in-memory DB for this test
    import aiosqlite
    async with aiosqlite.connect(":memory:") as conn:
        db = Database()
        db.conn = conn
        db.logger = MagicMock()
        
        # Create table
        await conn.execute("CREATE TABLE market_data (timestamp DATETIME, interval TEXT)")
        
        # Insert old and new data
        await conn.execute("INSERT INTO market_data VALUES (date('now', '-10 days'), 'tick')") # Old tick
        await conn.execute("INSERT INTO market_data VALUES (date('now', '-1 days'), 'tick')")  # New tick
        await conn.execute("INSERT INTO market_data VALUES (date('now', '-40 days'), '1m')")   # Old candle
        await conn.execute("INSERT INTO market_data VALUES (date('now', '-10 days'), '1m')")   # New candle
        await conn.commit()
        
        # Run Cleanup
        await db.cleanup_old_data(tick_retention_days=7, candle_retention_days=30)
        
        # Verify
        async with conn.execute("SELECT count(*) FROM market_data") as cursor:
            row = await cursor.fetchone()
            assert row[0] == 2 # Only new tick and new candle should remain

@pytest.mark.asyncio
async def test_condition_search_integration():
    """Test Condition Search loading and subscription."""
    with patch('data.data_collector.db') as mock_db, \
         patch('data.data_collector.kiwoom_client') as mock_rest:
        
        mock_db.connect = AsyncMock()
        mock_db.cleanup_old_data = AsyncMock()
        mock_db.execute = AsyncMock()
        
        collector = DataCollector()
        collector.rest_client = mock_rest
        collector.ws_client = AsyncMock()
        collector.sync_symbol_master = AsyncMock()
        
        # Mock Condition Load Response
        mock_rest.get_condition_load = AsyncMock(return_value={
            "output": [{"index": "001", "name": "TestCond"}]
        })
        mock_rest.send_condition = AsyncMock()
        
        # Run start (which calls load_and_subscribe_conditions)
        # We only want to test the condition part, so we can call it directly
        await collector.load_and_subscribe_conditions()
        
        mock_rest.get_condition_load.assert_called_once()
        mock_rest.send_condition.assert_called_once_with("1000", "TestCond", "001", "0")
