import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from execution.notification import NotificationManager

@pytest.mark.asyncio
async def test_notification_flow():
    # Mock Config
    with patch("execution.notification.config") as mock_config:
        mock_config.get.return_value = "TEST_TOKEN"
        
        manager = NotificationManager()
        manager.rate_limit_delay = 0.01 # Speed up for test
        manager._send_kakao = AsyncMock() # Mock API call
        
        # 1. Start
        await manager.start()
        assert manager._running is True
        
        # Wait for startup message
        await asyncio.sleep(0.1)
        # manager._send_kakao.assert_called_with("🤖 [시스템] 트레이딩 서버 시작")
        manager._send_kakao.reset_mock()
        
        # 2. Send Message
        await manager.send_message("Test Message 1")
        
        # Wait for worker to process
        await asyncio.sleep(0.1)
        manager._send_kakao.assert_called_with("Test Message 1")
        
        # 3. Test Duplicate Prevention
        manager._send_kakao.reset_mock()
        await manager.send_message("Duplicate Message")
        await manager.send_message("Duplicate Message") # Should be ignored
        
        await asyncio.sleep(0.1)
        assert manager._send_kakao.call_count == 1
        
        # 4. Test Rate Limiting
        # Set delay to 0.5s
        manager.rate_limit_delay = 0.2
        manager._send_kakao.reset_mock()
        
        await manager.send_message("Msg A") # New message
        await manager.send_message("Msg B") # New message
        
        # Immediately check: Should have processed A, but B might be waiting
        await asyncio.sleep(0.05)
        # Depending on timing, A might be sent. B is queued.
        
        await asyncio.sleep(0.3) # Wait enough for B
        assert manager._send_kakao.call_count >= 2
        
        # 6. Test Notify Level
        manager.notify_level = "ERROR_ONLY"
        manager._send_kakao.reset_mock()
        
        await manager.send_message("Info Msg", level="INFO")
        await asyncio.sleep(0.05)
        manager._send_kakao.assert_not_called() # Should be filtered
        
        await manager.send_message("Error Msg", level="ERROR")
        await asyncio.sleep(0.05)
        manager._send_kakao.assert_called() # Should be sent
        
        # 7. Test Daily Report
        manager.rate_limit_delay = 0.01 # Reset speed
        manager.notify_level = "ALL"
        manager._send_kakao.reset_mock()
        summary = {
            "balance": {"total_asset": 10000000, "daily_pnl": 500000},
            "positions": {"005930": {}}
        }
        await manager.send_daily_report(summary)
        await asyncio.sleep(0.3)
        manager._send_kakao.assert_called()
        args = manager._send_kakao.call_args[0][0]
        assert "일일 리포트" in args
        assert "500,000원" in args
        
        # 5. Stop
        await manager.stop()
        assert manager._running is False
