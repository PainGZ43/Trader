import asyncio
from datetime import datetime, time, timedelta
from typing import List, Dict, Any, Callable, Awaitable
from core.logger import get_logger
from data.market_schedule import market_schedule

class Scheduler:
    """
    Asyncio-based lightweight scheduler.
    Handles:
    - Interval tasks (every N seconds)
    - Cron-like tasks (at HH:MM)
    - Market Event monitoring
    """
    def __init__(self):
        self.logger = get_logger("Scheduler")
        self._running = False
        self._task = None
        
        self.interval_tasks: List[Dict[str, Any]] = []
        self.cron_tasks: List[Dict[str, Any]] = []
        
        # State for cron tasks to avoid double execution in the same minute
        self.last_cron_run = {} # task_id -> date_str
        
        self.loop_sleep_time = 1.0 # Configurable for testing

    async def start(self):
        """Start the scheduler loop."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._loop())
            self.logger.info("Scheduler Started")

    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.logger.info("Scheduler Stopped")

    def register_interval(self, interval_seconds: int, callback: Callable[[], Awaitable[None]], name: str = "Task"):
        """Register a task to run every N seconds."""
        self.interval_tasks.append({
            "interval": interval_seconds,
            "callback": callback,
            "name": name,
            "last_run": 0 # timestamp
        })
        self.logger.info(f"Registered Interval Task: {name} (every {interval_seconds}s)")

    def register_cron(self, hour: int, minute: int, callback: Callable[[], Awaitable[None]], name: str = "Task"):
        """Register a task to run daily at HH:MM."""
        task_id = f"{name}_{hour}_{minute}"
        self.cron_tasks.append({
            "hour": hour,
            "minute": minute,
            "callback": callback,
            "name": name,
            "id": task_id
        })
        self.logger.info(f"Registered Cron Task: {name} (at {hour:02d}:{minute:02d})")

    async def _loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                now = datetime.now()
                now_ts = now.timestamp()
                
                # 1. Process Interval Tasks
                for task in self.interval_tasks:
                    if now_ts - task["last_run"] >= task["interval"]:
                        # Run task
                        asyncio.create_task(self._safe_execute(task["callback"], task["name"]))
                        task["last_run"] = now_ts

                # 2. Process Cron Tasks
                for task in self.cron_tasks:
                    if now.hour == task["hour"] and now.minute == task["minute"]:
                        today_str = now.strftime("%Y-%m-%d")
                        # Check if already ran today
                        if self.last_cron_run.get(task["id"]) != today_str:
                            asyncio.create_task(self._safe_execute(task["callback"], task["name"]))
                            self.last_cron_run[task["id"]] = today_str
                
                # 3. Market Status Check (Optional, if needed here or handled by interval task)
                # For now, we assume MarketSchedule is checked via interval task if needed.
                
                await asyncio.sleep(self.loop_sleep_time) # Check every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Scheduler Loop Error: {e}")
                await asyncio.sleep(5) # Backoff on error

    async def _safe_execute(self, callback, name):
        """Execute callback with exception handling."""
        try:
            await callback()
        except Exception as e:
            self.logger.error(f"Task '{name}' Failed: {e}")
