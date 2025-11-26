import pytest
import asyncio
import threading
from core.event_bus import EventBus, Event

@pytest.fixture
def event_bus():
    # Reset singleton
    EventBus._instance = None
    bus = EventBus()
    return bus

@pytest.mark.asyncio
async def test_subscribe_publish_async(event_bus):
    """Test async subscription and publishing."""
    received_events = []

    async def callback(event: Event):
        received_events.append(event)

    event_bus.subscribe("test_topic", callback)
    event_bus.publish("test_topic", "test_data")
    
    # Wait for async dispatch
    await asyncio.sleep(0.1)
    
    assert len(received_events) == 1
    assert received_events[0].topic == "test_topic"
    assert received_events[0].data == "test_data"

@pytest.mark.asyncio
async def test_subscribe_publish_sync(event_bus):
    """Test sync subscription and publishing."""
    received_events = []

    def callback(event: Event):
        received_events.append(event)

    event_bus.subscribe("test_topic", callback)
    event_bus.publish("test_topic", "test_data")
    
    await asyncio.sleep(0.1)
    
    assert len(received_events) == 1
    assert received_events[0].data == "test_data"

@pytest.mark.asyncio
async def test_unsubscribe(event_bus):
    """Test unsubscribe functionality."""
    received_events = []

    async def callback(event: Event):
        received_events.append(event)

    sub_id = event_bus.subscribe("test_topic", callback)
    event_bus.publish("test_topic", "data1")
    await asyncio.sleep(0.1)
    assert len(received_events) == 1
    
    event_bus.unsubscribe(sub_id)
    event_bus.publish("test_topic", "data2")
    await asyncio.sleep(0.1)
    assert len(received_events) == 1 # Should not receive data2

@pytest.mark.asyncio
async def test_error_isolation(event_bus):
    """Test that one subscriber failure doesn't stop others."""
    results = []

    def failing_callback(event):
        raise ValueError("Oops")

    def success_callback(event):
        results.append("Success")

    event_bus.subscribe("topic", failing_callback)
    event_bus.subscribe("topic", success_callback)
    
    event_bus.publish("topic", "data")
    await asyncio.sleep(0.1)
    
    assert len(results) == 1
    assert results[0] == "Success"

@pytest.mark.asyncio
async def test_thread_safe_publish(event_bus):
    """Test publishing from a separate thread using standard publish."""
    # Ensure loop is captured by subscribing first
    received_events = []
    
    async def callback(event):
        received_events.append(event)
        
    event_bus.subscribe("thread_topic", callback)
    
    def thread_target():
        # Simulate calling from a thread using standard publish
        # It should automatically use the captured loop
        event_bus.publish("thread_topic", "thread_data")
        
    t = threading.Thread(target=thread_target)
    t.start()
    t.join()
    
    await asyncio.sleep(0.1)
    assert len(received_events) == 1
    assert received_events[0].data == "thread_data"

@pytest.mark.asyncio
async def test_unsubscribe_failure(event_bus):
    """Test unsubscribing with invalid ID."""
    # Should log warning but not crash
    event_bus.unsubscribe("invalid_id")
