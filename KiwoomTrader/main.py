import sys
import asyncio
from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop
from ui.main_window import MainWindow
from logger import logger
import os

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        window = MainWindow()
        window.show()
        
        logger.info("Application Started")
        
        with loop:
            loop.run_forever()
    except Exception as e:
        logger.critical(f"Application Crashed: {e}")
