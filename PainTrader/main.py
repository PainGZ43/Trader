import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop
from ui.main_window import MainWindow
from core.logger import get_logger
from core.config import config

# Install qasync if not present (it allows asyncio with PyQt)
# pip install qasync

def main():
    # Initialize Logger
    logger = get_logger("Main")
    logger.info("Starting PainTrader Application...")

    # Create Qt Application
    app = QApplication(sys.argv)
    
    # Create Event Loop for Asyncio integration
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Create Main Window
    window = MainWindow()
    window.show()

    logger.info("Main Window Displayed")

    # Run Event Loop
    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
