import pytest
import sys
import threading
import asyncio
import os
import time
from unittest.mock import MagicMock, patch
from core.exception_handler import ExceptionHandler
from core.event_bus import event_bus

@pytest.fixture
def exception_handler():
    # Reset singleton
    ExceptionHandler._instance = None
    handler = ExceptionHandler()
    # Mock logger to avoid spam
    handler.logger = MagicMock()
    # Use a temp dir for logs
    handler.log_dir = "tests/temp_crash_reports"
    if not os.path.exists(handler.log_dir):
        os.makedirs(handler.log_dir)
    return handler

def test_sys_exception_hook(exception_handler):
    """Test Main Thread Exception Hook."""
    exception_handler.install()
    
    # Simulate an exception
    try:
        raise ValueError("Main Thread Error")
    except ValueError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        # Manually call hook to avoid crashing test runner
        exception_handler.handle_exception(exc_type, exc_value, exc_traceback)
    
    # Verify report created
    files = os.listdir(exception_handler.log_dir)
    assert len(files) > 0
    assert "MainThread" in files[0]
    
    # Verify EventBus notification
    # We need to mock publish or subscribe to verify
    # Since EventBus is singleton, we can subscribe
    # But test is sync, so we can't easily await async publish if it was async
    # But publish is fire-and-forget.
    # Let's mock event_bus.publish
    from unittest.mock import ANY
    with patch.object(event_bus, 'publish') as mock_publish:
        exception_handler.handle_exception(exc_type, exc_value, exc_traceback)
        mock_publish.assert_called_with("CRITICAL_ERROR", ANY)

def test_threading_exception_hook(exception_handler):
    """Test Threading Exception Hook."""
    exception_handler.install()
    
    # Create a dummy thread args object
    try:
        raise RuntimeError("Thread Error")
    except RuntimeError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
    args = threading.ExceptHookArgs([exc_type, exc_value, exc_traceback, threading.current_thread()])
    
    exception_handler.handle_thread_exception(args)
    
    files = os.listdir(exception_handler.log_dir)
    # Should have at least one file (maybe from previous test if not cleaned)
    # We should clean up in fixture but let's just check existence
    assert any("Thread" in f for f in files)

@pytest.mark.asyncio
async def test_asyncio_exception_hook(exception_handler):
    """Test Asyncio Exception Hook."""
    # We need a running loop
    loop = asyncio.get_running_loop()
    
    # Install hook
    loop.set_exception_handler(exception_handler.handle_async_exception)
    
    # Create a task that fails
    async def failing_task():
        raise IndexError("Async Error")
        
    # We need to run task and let loop handle exception
    # asyncio.create_task(failing_task())
    # But pytest-asyncio might catch it?
    # Let's manually call the handler to verify logic
    
    context = {
        "message": "Task exception was never retrieved",
        "exception": IndexError("Async Error"),
        "future": asyncio.Future()
    }
    
    exception_handler.handle_async_exception(loop, context)
    
    files = os.listdir(exception_handler.log_dir)
    assert any("Asyncio" in f for f in files)

def test_install_edge_cases(exception_handler):
    """Test install edge cases."""
    # 1. No loop
    with patch('asyncio.get_running_loop', side_effect=RuntimeError):
        exception_handler.install()
        # Should warn but not crash
    
    # 2. Already installed
    exception_handler._installed = True
    exception_handler.install()
    # Should return early

def test_keyboard_interrupt(exception_handler):
    """Test KeyboardInterrupt handling."""
    # Main Thread
    with patch('sys.__excepthook__') as mock_hook:
        exception_handler.handle_exception(KeyboardInterrupt, KeyboardInterrupt(), None)
        mock_hook.assert_called()
        
    # Thread
    args = threading.ExceptHookArgs([KeyboardInterrupt, KeyboardInterrupt(), None, threading.current_thread()])
    exception_handler.handle_thread_exception(args)
    # Should just return

def test_asyncio_cancelled(exception_handler):
    """Test Asyncio CancelledError."""
    context = {"exception": asyncio.CancelledError()}
    exception_handler.handle_async_exception(None, context)
    # Should return early

def test_report_failure(exception_handler):
    """Test report generation failure."""
    with patch('builtins.open', side_effect=OSError("Disk Full")):
        path = exception_handler._save_report(ValueError, ValueError("Test"), None, "Test")
        assert path == ""

def test_report_no_exc_info(exception_handler):
    """Test report with no exception info."""
    path = exception_handler._save_report(None, None, None, "Test")
    assert os.path.exists(path)
    with open(path, 'r') as f:
        content = f.read()
        assert "No exception info available" in content

def teardown_module(module):
    # Clean up temp logs
    import shutil
    if os.path.exists("tests/temp_crash_reports"):
        shutil.rmtree("tests/temp_crash_reports")
