import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop
from ui.main_window import MainWindow
from core.logger import get_logger
from data.data_collector import data_collector

def main():
    # Initialize Logger
    logger = get_logger("Main")
    logger.info("Starting PainTrader Application...")

    # Global Exception Handler
    from core.exception_handler import exception_handler
    sys.excepthook = exception_handler.handle_exception

    # Pre-import QtWebEngineWidgets to avoid "must be imported before QCoreApplication" error
    # This is required because we lazy-load BacktestDialog which uses WebEngine
    try:
        from PyQt6.QtWebEngineWidgets import QWebEngineView
    except ImportError:
        pass

    # Create Qt Application
    app = QApplication(sys.argv)
    
    # Create Event Loop for Asyncio integration
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Create Main Window
    window = MainWindow()
    window.show()

    logger.info("Main Window Displayed")
    
    # Start Data Collector
    loop.create_task(data_collector.start())

    # Initialize Execution Engine
    from data.kiwoom_rest_client import kiwoom_client
    from execution.engine import ExecutionEngine
    from core.config import config
    
    # Determine Mode (PAPER vs REAL) - Default to REAL (which includes Kiwoom Mock Server)
    # If we want internal Paper Trading, we would set this to PAPER.
    # For now, we assume Kiwoom (Real/Mock) usage.
    exec_engine = ExecutionEngine(kiwoom_client, mode="REAL", config=config._config)
    loop.create_task(exec_engine.initialize())

    # Run Event Loop
    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
