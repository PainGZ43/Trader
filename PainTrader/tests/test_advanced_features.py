import pytest
import asyncio
import time
from datetime import datetime, time as dtime
from unittest.mock import patch, MagicMock, AsyncMock
from data.rate_limiter import RateLimiter
from data.market_schedule import MarketSchedule
from data.data_collector import DataCollector

# --- Rate Limiter Tests ---

@pytest.mark.asyncio
async def test_rate_limiter_acquire():
    """Test that rate limiter allows requests within limit."""
    limiter = RateLimiter(max_tokens=5, refill_rate=10)
    start = time.monotonic()
    
    # Acquire 5 tokens (should be immediate)
    for _ in range(5):
        await limiter.acquire()
        
    duration = time.monotonic() - start
    assert duration < 0.1 # Should be very fast

@pytest.mark.asyncio
async def test_rate_limiter_throttling():
    """Test that rate limiter throttles requests exceeding limit."""
    # 1 token per second
    limiter = RateLimiter(max_tokens=1, refill_rate=1)
    
    # First acquire (immediate)
    await limiter.acquire()
    
    start = time.monotonic()
    # Second acquire (should wait ~1 second)
    await limiter.acquire()
    duration = time.monotonic() - start
    
    assert duration >= 0.9 # Allow small margin

# --- Market Schedule Tests ---

def test_market_schedule_open():
    """Test market open status."""
    schedule = MarketSchedule()
    
    # Mock datetime.now() to be 10:00 AM
    with patch('data.market_schedule.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2023, 1, 1, 10, 0, 0)
        assert schedule.check_market_status() is True
        assert schedule.is_market_open is True

def test_market_schedule_closed_before_9():
    """Test market closed before 9:00."""
    schedule = MarketSchedule()
    
    with patch('data.market_schedule.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2023, 1, 1, 8, 59, 0)
        assert schedule.check_market_status() is False
        assert schedule.is_market_open is False

def test_market_schedule_closed_after_1530():
    """Test market closed after 15:30."""
    schedule = MarketSchedule()
    
    with patch('data.market_schedule.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2023, 1, 1, 15, 31, 0)
        assert schedule.check_market_status() is False

# --- Data Gap Filling Tests (Re-verification) ---

@pytest.mark.asyncio
async def test_gap_filling_logic():
    """Verify Gap Filling is triggered on time gap."""
    # We mock DataCollector dependencies
    with patch('data.data_collector.ws_client'), \
         patch('data.data_collector.kiwoom_client'), \
         patch('data.data_collector.db') as mock_db:
        
        # Configure AsyncMock for db methods
        mock_db.execute = AsyncMock()
        mock_db.connect = AsyncMock()
    
        collector = DataCollector()
        collector.market_schedule.check_market_status = MagicMock(return_value=True)
        collector.fill_gap = AsyncMock() # Mock the actual filling logic
        
        symbol = "005930"
        
        # 1. Initial Data
        from datetime import timedelta
        now = datetime.now()
        collector.last_update_time[symbol] = now - timedelta(seconds=70) # 70s ago
        
        # 2. New Data arrives
        data = {"code": symbol, "price": 100}
        await collector.on_realtime_data(data)
        
        # 3. Verify fill_gap called
        collector.fill_gap.assert_called_once()
