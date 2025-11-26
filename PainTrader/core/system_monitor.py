import asyncio
import psutil
import os
import socket
import time
from typing import Dict, Any
from core.logger import get_logger
from core.event_bus import event_bus

class SystemMonitor:
    """
    Monitors System Resources (CPU, Memory, Disk), Process Health, and Network Connectivity.
    Publishes 'SYSTEM_WARNING' events if thresholds are exceeded.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemMonitor, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.logger = get_logger("SystemMonitor")
        self.running = False
        self.task = None
        
        # Thresholds (Configurable)
        self.cpu_threshold = 80.0  # %
        self.memory_threshold = 85.0  # %
        self.disk_threshold = 90.0  # %
        self.process_memory_threshold_mb = 1024.0 # 1GB
        
        # State
        self.process = psutil.Process(os.getpid())

    async def start(self, interval: int = 60):
        """
        Start the monitoring loop.
        """
        if self.running:
            return
        
        self.running = True
        self.logger.info(f"System Monitor started (Interval: {interval}s)")
        self.task = asyncio.create_task(self._monitor_loop(interval))

    async def stop(self):
        """
        Stop the monitoring loop.
        """
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.logger.info("System Monitor stopped")

    async def _monitor_loop(self, interval: int):
        while self.running:
            try:
                await self.check_resources()
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
            
            await asyncio.sleep(interval)

    async def check_resources(self):
        """
        Perform all checks.
        """
        # 1. System Resources
        self._check_system_resources()
        
        # 2. Process Resources
        self._check_process_resources()
        
        # 3. Network Connectivity
        await self._check_network()

    def _check_system_resources(self):
        # CPU
        cpu_percent = psutil.cpu_percent(interval=None)
        if cpu_percent > self.cpu_threshold:
            self._publish_warning("High CPU Usage", f"CPU usage is at {cpu_percent}%")

        # Memory
        mem = psutil.virtual_memory()
        if mem.percent > self.memory_threshold:
            self._publish_warning("High Memory Usage", f"System memory usage is at {mem.percent}%")

        # Disk
        # Check the drive where the current script is running
        drive = os.path.splitdrive(os.getcwd())[0]
        if not drive:
            drive = "/" # Unix fallback
        else:
            drive = drive + "\\" # Windows format e.g. C:\

        try:
            disk = psutil.disk_usage(drive)
            if disk.percent > self.disk_threshold:
                self._publish_warning("Low Disk Space", f"Disk {drive} usage is at {disk.percent}%")
        except Exception as e:
            self.logger.warning(f"Failed to check disk usage: {e}")

    def _check_process_resources(self):
        try:
            # RSS: Resident Set Size (Physical Memory)
            mem_info = self.process.memory_info()
            rss_mb = mem_info.rss / 1024 / 1024
            
            if rss_mb > self.process_memory_threshold_mb:
                self._publish_warning("Memory Leak Suspected", f"Process memory usage is {rss_mb:.2f} MB")
        except Exception as e:
            self.logger.error(f"Failed to check process resources: {e}")

    async def _check_network(self):
        """
        Check connectivity to a reliable external server (Google DNS).
        """
        def check_connection():
            try:
                # Connect to 8.8.8.8 on port 53 (DNS) - fast and reliable
                socket.create_connection(("8.8.8.8", 53), timeout=3)
                return True
            except OSError:
                return False

        loop = asyncio.get_running_loop()
        is_connected = await loop.run_in_executor(None, check_connection)
        
        if not is_connected:
            self._publish_warning("Network Disconnected", "Failed to connect to external network (8.8.8.8)")

    def _publish_warning(self, title: str, message: str):
        self.logger.warning(f"SYSTEM WARNING: {title} - {message}")
        event_bus.publish("SYSTEM_WARNING", {
            "title": title,
            "message": message,
            "timestamp": time.time()
        })

system_monitor = SystemMonitor()
