import sys
import threading
import traceback
import asyncio
import os
import time
from datetime import datetime
from typing import Optional
from core.logger import get_logger
from core.event_bus import event_bus

class ExceptionHandler:
    """
    Global Exception Handler (Singleton).
    Catches unhandled exceptions from Main Thread, Background Threads, and Asyncio Tasks.
    Generates crash reports and notifies via EventBus.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ExceptionHandler, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.logger = get_logger("ExceptionHandler")
        self.log_dir = "logs/crash_reports"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self._installed = False

    def install(self):
        """
        Install global exception hooks.
        """
        if self._installed:
            return

        # 1. Main Thread Hook
        sys.excepthook = self.handle_exception

        # 2. Threading Hook
        threading.excepthook = self.handle_thread_exception

        # 3. Asyncio Hook (Must be set on the running loop)
        try:
            loop = asyncio.get_running_loop()
            loop.set_exception_handler(self.handle_async_exception)
        except RuntimeError:
            self.logger.warning("No running event loop found. Asyncio exception handler not installed yet.")

        self._installed = True
        self.logger.info("Global Exception Handler Installed")

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Handle uncaught exceptions from the Main Thread.
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        self.logger.critical("Uncaught Exception in Main Thread", exc_info=(exc_type, exc_value, exc_traceback))
        self._process_error(exc_type, exc_value, exc_traceback, source="MainThread")

    def handle_thread_exception(self, args):
        """
        Handle uncaught exceptions from Background Threads.
        """
        if issubclass(args.exc_type, KeyboardInterrupt):
            return

        self.logger.critical(f"Uncaught Exception in Thread: {args.thread.name}", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
        self._process_error(args.exc_type, args.exc_value, args.exc_traceback, source=f"Thread-{args.thread.name}")

    def handle_async_exception(self, loop, context):
        """
        Handle uncaught exceptions from Asyncio Tasks.
        """
        msg = context.get("message")
        exception = context.get("exception")
        
        # Filter out benign asyncio cancellations if necessary
        if isinstance(exception, asyncio.CancelledError):
            return

        self.logger.critical(f"Asyncio Exception: {msg}", exc_info=exception)
        
        # Extract traceback if available
        tb = exception.__traceback__ if exception else None
        exc_type = type(exception) if exception else None
        
        self._process_error(exc_type, exception, tb, source="Asyncio", extra_context=context)

    def _process_error(self, exc_type, exc_value, exc_traceback, source: str, extra_context: Optional[dict] = None):
        """
        Common error processing: Save Report -> Notify -> (Optional) Exit
        """
        # 1. Generate Crash Report
        report_path = self._save_report(exc_type, exc_value, exc_traceback, source, extra_context)
        
        # 2. Notify System
        error_data = {
            "source": source,
            "type": str(exc_type.__name__) if exc_type else "Unknown",
            "message": str(exc_value),
            "report_path": report_path
        }
        event_bus.publish("CRITICAL_ERROR", error_data)

    def _save_report(self, exc_type, exc_value, exc_traceback, source: str, extra_context: Optional[dict] = None) -> str:
        """
        Save detailed crash report to file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crash_{timestamp}_{source}.log"
        filepath = os.path.join(self.log_dir, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"CRASH REPORT - {datetime.now()}\n")
                f.write(f"Source: {source}\n")
                f.write("="*50 + "\n\n")
                
                f.write("Exception Info:\n")
                if exc_type and exc_value:
                    traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
                else:
                    f.write("No exception info available.\n")
                
                if extra_context:
                    f.write("\nExtra Context:\n")
                    for k, v in extra_context.items():
                        f.write(f"{k}: {v}\n")
                
                f.write("\n" + "="*50 + "\n")
                f.write("System Info:\n")
                f.write(f"Python: {sys.version}\n")
                f.write(f"Platform: {sys.platform}\n")
                
            self.logger.info(f"Crash report saved to: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to save crash report: {e}")
            return ""

exception_handler = ExceptionHandler()
