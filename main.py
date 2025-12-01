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

    # Run Event Loop
    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
