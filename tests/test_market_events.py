import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from execution.engine import ExecutionEngine
from data.market_schedule import MarketSchedule

@pytest.mark.asyncio
async def test_market_event_flow():
    # Mock Dependencies
    mock_kiwoom = MagicMock()
    mock_kiwoom.get_account_balance.return_value = {"deposit": 100, "total_asset": 100}
    
    engine = ExecutionEngine(mock_kiwoom, mode="PAPER")
    engine.notification_manager = AsyncMock()
    engine.notification_manager.send_message = AsyncMock()
    
    # Mock Scheduler to run immediately/manually
    engine.scheduler = MagicMock()
    engine.scheduler.register_interval = MagicMock()
    
    # Test Open Event
    with patch("data.market_schedule.market_schedule") as mock_schedule:
        # Configure Scheduler inside patch to capture mock
        engine._configure_scheduler()
        
        # Extract callback again
        call_args = engine.scheduler.register_interval.call_args_list
        market_monitor_callback = None
        for call in call_args:
            if call[0][2] == "MarketMonitor":
                market_monitor_callback = call[0][1]
                break
        
        # Initial state: Closed
        mock_schedule.is_market_open = False
        # Check status returns Open
        mock_schedule.check_market_status.return_value = True
        
        await market_monitor_callback()
        
        engine.notification_manager.send_message.assert_called_with(
            "🔔 [장 시작] 정규장이 시작되었습니다. 트레이딩을 개시합니다.", level="INFO"
        )
        
        # Test Close Event
        # Initial state: Open
        mock_schedule.is_market_open = True
        # Check status returns Closed
        mock_schedule.check_market_status.return_value = False
        
        engine.notification_manager.send_message.reset_mock()
        await market_monitor_callback()
        
        engine.notification_manager.send_message.assert_called_with(
            "🔔 [장 마감] 정규장이 종료되었습니다. 미체결 주문을 취소합니다.", level="INFO"
        )
