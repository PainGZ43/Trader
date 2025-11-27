import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from execution.scheduler import Scheduler

@pytest.mark.asyncio
async def test_scheduler_interval():
    scheduler = Scheduler()
    scheduler.loop_sleep_time = 0.01 # Speed up loop
    callback = AsyncMock()
    
    # Register interval 0.1s
    scheduler.register_interval(0.1, callback, "TestInterval")
    
    await scheduler.start()
    
    # Wait for 0.25s -> Should run at least 2 times
    await asyncio.sleep(0.25)
    
    await scheduler.stop()
    
    assert callback.call_count >= 2

@pytest.mark.asyncio
async def test_scheduler_cron():
    scheduler = Scheduler()
    scheduler.loop_sleep_time = 0.01 # Speed up loop
    callback = AsyncMock()
    
    # Mock datetime to control time
    with patch("execution.scheduler.datetime") as mock_datetime:
        # 1. Set time to 15:39:59
        mock_datetime.now.return_value = datetime(2024, 11, 27, 15, 39, 59)
        
        scheduler.register_cron(15, 40, callback, "TestCron")
        await scheduler.start()
        
        # Wait a bit, time hasn't changed yet
        await asyncio.sleep(0.1)
        callback.assert_not_called()
        
        # 2. Set time to 15:40:00
        mock_datetime.now.return_value = datetime(2024, 11, 27, 15, 40, 0)
        
        # Wait for loop to pick it up
        await asyncio.sleep(0.05) # Scheduler loop sleeps 0.01s
        
        callback.assert_called_once()
        
        # 3. Set time to 15:40:01 (Same minute)
        mock_datetime.now.return_value = datetime(2024, 11, 27, 15, 40, 1)
        callback.reset_mock()
        
        await asyncio.sleep(0.05)
        callback.assert_not_called() # Should not run again in same minute
        
        await scheduler.stop()

@pytest.mark.asyncio
async def test_scheduler_error_handling():
    scheduler = Scheduler()
    
    async def bad_callback():
        raise ValueError("Boom")
        
    scheduler.register_interval(0.1, bad_callback, "BadTask")
    
    await scheduler.start()
    await asyncio.sleep(0.2) # Should run and fail, but scheduler keeps running
    
    assert scheduler._running is True
    await scheduler.stop()
