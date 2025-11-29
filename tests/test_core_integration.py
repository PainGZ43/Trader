import pytest
import pytest_asyncio
import asyncio
import logging
import os
import threading
from unittest.mock import patch, MagicMock
from core.config import ConfigLoader
from core.logger import Logger, get_logger
from core.event_bus import EventBus, Event
from core.database import Database
from core.exception_handler import ExceptionHandler
from core.system_monitor import SystemMonitor

# Helper to reset singletons
def reset_singletons():
    ConfigLoader._instance = None
    Logger._instance = None
    Logger._loggers = {}
    EventBus._instance = None
    Database._instance = None
    ExceptionHandler._instance = None
    SystemMonitor._instance = None

@pytest_asyncio.fixture
async def integration_setup():
    reset_singletons()
    
    # Setup Config
    with patch.dict(os.environ, {"MOCK_MODE": "True", "DB_PATH": ":memory:"}):
        ConfigLoader._instance = None
        mock_config = ConfigLoader()
        
    # Patch config in Database module
    with patch('core.database.config', mock_config):
        # Setup Logger
        logger = Logger()
        
        # Setup EventBus
        event_bus = EventBus()
        
        # Setup Database
        db = Database()
        await db.connect()
        await db.execute("CREATE TABLE IF NOT EXISTS integration_logs (id INTEGER PRIMARY KEY, message TEXT)")
        
        # Setup ExceptionHandler
        exception_handler = ExceptionHandler()
        # We don't fully install hooks to avoid messing up pytest, but we test the logic
        
        # Setup SystemMonitor
        system_monitor = SystemMonitor()
        
        yield {
            "config": mock_config,
            "logger": logger,
            "event_bus": event_bus,
            "db": db,
            "exception_handler": exception_handler,
            "system_monitor": system_monitor
        }
    
    await system_monitor.stop()
    await db.close()
    reset_singletons()

@pytest.mark.asyncio
async def test_core_integration_flow(integration_setup):
    """
    Integration Scenario:
    1. SystemMonitor detects high CPU -> Publishes SYSTEM_WARNING
    2. Subscriber receives warning -> Writes to DB
    3. Exception occurs -> ExceptionHandler catches -> Publishes CRITICAL_ERROR
    4. Subscriber receives error -> Verifies
    """
    components = integration_setup
    event_bus = components["event_bus"]
    db = components["db"]
    system_monitor = components["system_monitor"]
    exception_handler = components["exception_handler"]
    
    # Track events
    received_warnings = []
    received_errors = []
    
    async def on_warning(event: Event):
        received_warnings.append(event)
        # Simulate DB write on warning
        await db.execute("INSERT INTO integration_logs (message) VALUES (?)", (f"Warning: {event.data}",))
        
    async def on_error(event: Event):
        received_errors.append(event)

    event_bus.subscribe("SYSTEM_WARNING", on_warning)
    event_bus.subscribe("CRITICAL_ERROR", on_error)

    # Patch the module-level event_bus instances to use our test instance
    with patch('core.system_monitor.event_bus', event_bus), \
         patch('core.exception_handler.event_bus', event_bus):

        # 1. Trigger System Warning (Mock High CPU)
        # Mock psutil to return high usage
        with patch('psutil.cpu_percent', return_value=95.0), \
             patch('psutil.virtual_memory') as mock_mem, \
             patch('psutil.disk_usage') as mock_disk:
        
            mock_mem.return_value.percent = 50.0
            mock_disk.return_value.percent = 50.0
            
            # Manually trigger check to avoid waiting for loop
            system_monitor._check_system_resources()
            
            # Wait for event processing (async dispatch)
            await asyncio.sleep(0.1)
            
            assert len(received_warnings) > 0
            assert "High CPU" in str(received_warnings[0].data)
            
            # Verify DB write
            rows = await db.fetch_all("SELECT * FROM integration_logs")
            assert len(rows) == 1, f"Expected 1 row, got {len(rows)}. Rows: {[dict(r) for r in rows]}"
            assert "High CPU" in rows[0]['message']

        # 2. Trigger Exception (Simulate)
        # We call handle_exception directly to simulate an uncaught exception reaching the hook
        try:
            raise ValueError("Integration Test Error")
        except ValueError as e:
            # Simulate what the hook does
            # We need to mock _save_report to avoid file creation or just let it run (it uses temp dir in tests usually?)
            # ExceptionHandler uses 'logs/crash_reports' by default.
            # Let's patch _save_report to return a dummy path
            with patch.object(exception_handler, '_save_report', return_value="dummy_report.txt"):
                exception_handler.handle_exception(ValueError, e, None)
            
        await asyncio.sleep(0.1)
        
        assert len(received_errors) > 0
        assert "Integration Test Error" in str(received_errors[0].data['message'])

    print("Core Integration Test: PASS")
