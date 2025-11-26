import asyncio
import uuid
import time
import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Union
from core.logger import get_logger

@dataclass
class Event:
    """
    Standard Event Data Holder.
    """
    topic: str
    data: Any = None
    timestamp: float = field(default_factory=time.time)

class EventBus:
    """
    Asynchronous Event Bus (Singleton).
    Supports Pub/Sub pattern with async/sync callbacks.
    Thread-safe publishing.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.logger = get_logger("EventBus")
        # Storage: {topic: {sub_id: callback}}
        self._subscribers: Dict[str, Dict[str, Callable]] = {}
        self._loop = None

    def _get_loop(self):
        """
        Get the running event loop.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        return loop

    def subscribe(self, topic: str, callback: Callable) -> str:
        """
        Subscribe to a topic.
        Returns a subscription ID (str) for unsubscribing.
        """
        # Capture the main loop if not already set
        if self._loop is None:
            self._loop = self._get_loop()

        if topic not in self._subscribers:
            self._subscribers[topic] = {}
        
        sub_id = str(uuid.uuid4())
        self._subscribers[topic][sub_id] = callback
        self.logger.debug(f"Subscribed to '{topic}' (ID: {sub_id})")
        return sub_id

    def unsubscribe(self, sub_id: str):
        """
        Unsubscribe using subscription ID.
        """
        for topic, subs in self._subscribers.items():
            if sub_id in subs:
                del subs[sub_id]
                self.logger.debug(f"Unsubscribed ID: {sub_id} from '{topic}'")
                return
        self.logger.warning(f"Unsubscribe failed: ID {sub_id} not found.")

    def publish(self, topic: str, data: Any = None):
        """
        Publish an event to a topic.
        Thread-safe: Automatically detects if called from thread and schedules on main loop.
        """
        event = Event(topic, data)
        
        # 1. Try to get current running loop
        current_loop = self._get_loop()

        if current_loop and current_loop.is_running():
            # We are in an event loop (likely main), schedule directly
            asyncio.create_task(self._dispatch(event))
        elif self._loop and self._loop.is_running():
            # We are in a thread, but have reference to main loop
            self._loop.call_soon_threadsafe(lambda: asyncio.create_task(self._dispatch(event)))
        else:
            # No loop available
            self.logger.error(f"Cannot publish event '{topic}': No active event loop found.")

    async def _dispatch(self, event: Event):
        """
        Internal dispatch logic.
        """
        if event.topic not in self._subscribers:
            return

        # Copy to avoid modification during iteration
        callbacks = list(self._subscribers[event.topic].values())
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                self.logger.error(f"Error handling event '{event.topic}': {e}")

event_bus = EventBus()
