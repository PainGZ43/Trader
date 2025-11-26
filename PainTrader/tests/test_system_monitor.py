import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from core.system_monitor import SystemMonitor
from core.event_bus import event_bus

@pytest.fixture
def system_monitor():
    # Reset singleton
    SystemMonitor._instance = None
    monitor = SystemMonitor()
    # Mock logger
    monitor.logger = MagicMock()
    return monitor

@pytest.mark.asyncio
async def test_high_cpu_warning(system_monitor):
    """Test warning when CPU usage is high."""
    # Mock Disk and Memory to be safe
    mock_disk = MagicMock()
    mock_disk.percent = 10.0
    mock_mem = MagicMock()
    mock_mem.percent = 10.0

    with patch('psutil.cpu_percent', return_value=90.0), \
         patch('psutil.virtual_memory', return_value=mock_mem), \
         patch('psutil.disk_usage', return_value=mock_disk), \
         patch.object(event_bus, 'publish') as mock_publish:
        
        system_monitor._check_system_resources()
        
        # Check if ANY call matches, not just the last one
        # But with safe mocks, only CPU should trigger
        mock_publish.assert_called_once()
        args = mock_publish.call_args[0]
        assert args[0] == "SYSTEM_WARNING"
        assert args[1]['title'] == "High CPU Usage"

@pytest.mark.asyncio
async def test_high_memory_warning(system_monitor):
    """Test warning when Memory usage is high."""
    mock_mem = MagicMock()
    mock_mem.percent = 95.0
    mock_disk = MagicMock()
    mock_disk.percent = 10.0
    
    with patch('psutil.virtual_memory', return_value=mock_mem), \
         patch('psutil.cpu_percent', return_value=10.0), \
         patch('psutil.disk_usage', return_value=mock_disk), \
         patch.object(event_bus, 'publish') as mock_publish:
        
        system_monitor._check_system_resources()
        
        mock_publish.assert_called_once()
        assert mock_publish.call_args[0][1]['title'] == "High Memory Usage"

@pytest.mark.asyncio
async def test_process_memory_leak_warning(system_monitor):
    """Test warning when Process Memory is high."""
    # Mock process memory info
    mock_info = MagicMock()
    # 2GB RSS
    mock_info.rss = 2 * 1024 * 1024 * 1024 
    
    system_monitor.process.memory_info = MagicMock(return_value=mock_info)
    
    with patch.object(event_bus, 'publish') as mock_publish:
        system_monitor._check_process_resources()
        
        mock_publish.assert_called()
        assert mock_publish.call_args[0][1]['title'] == "Memory Leak Suspected"

@pytest.mark.asyncio
async def test_network_disconnected_warning(system_monitor):
    """Test warning when Network is down."""
    # Mock socket connection to raise OSError
    with patch('socket.create_connection', side_effect=OSError("Unreachable")), \
         patch.object(event_bus, 'publish') as mock_publish:
        
        await system_monitor._check_network()
        
        mock_publish.assert_called()
        assert mock_publish.call_args[0][1]['title'] == "Network Disconnected"

@pytest.mark.asyncio
async def test_monitor_loop_start_stop(system_monitor):
    """Test start and stop of the monitoring loop."""
    system_monitor.check_resources = AsyncMock()
    
    await system_monitor.start(interval=0.1)
    assert system_monitor.running is True
    assert system_monitor.task is not None
    
    await asyncio.sleep(0.2)
    # Should have called check_resources at least once
    assert system_monitor.check_resources.called
    
    await system_monitor.stop()
    assert system_monitor.running is False
    assert system_monitor.task.cancelled() or system_monitor.task.done()

@pytest.mark.asyncio
async def test_start_idempotency(system_monitor):
    """Test start when already running."""
    system_monitor.running = True
    await system_monitor.start()
    assert system_monitor.task is None # Should not create new task

@pytest.mark.asyncio
async def test_monitor_loop_error(system_monitor):
    """Test error handling in monitor loop."""
    system_monitor.running = True
    
    # Mock check_resources to raise exception
    system_monitor.check_resources = AsyncMock(side_effect=Exception("Loop Error"))
    
    # Run loop for one iteration
    # We can't easily run infinite loop. 
    # But we can mock sleep to stop the loop or raise CancelledError?
    # Or just run it and cancel it quickly.
    
    task = asyncio.create_task(system_monitor._monitor_loop(0.01))
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    # Should have logged error
    system_monitor.logger.error.assert_called()

@pytest.mark.asyncio
async def test_disk_check_failure(system_monitor):
    """Test disk check failure."""
    with patch('psutil.disk_usage', side_effect=Exception("Disk Error")):
        system_monitor._check_system_resources()
        system_monitor.logger.warning.assert_called_with("Failed to check disk usage: Disk Error")

@pytest.mark.asyncio
async def test_process_check_failure(system_monitor):
    """Test process check failure."""
    system_monitor.process.memory_info = MagicMock(side_effect=Exception("Process Error"))
    system_monitor._check_process_resources()
    system_monitor.logger.error.assert_called()

@pytest.mark.asyncio
async def test_check_resources_integration(system_monitor):
    """Test check_resources calls all sub-checks."""
    system_monitor._check_system_resources = MagicMock()
    system_monitor._check_process_resources = MagicMock()
    system_monitor._check_network = AsyncMock()
    
    await system_monitor.check_resources()
    
    system_monitor._check_system_resources.assert_called()
    system_monitor._check_process_resources.assert_called()
    system_monitor._check_network.assert_called()
