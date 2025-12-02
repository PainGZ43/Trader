import sys
import os
import asyncio
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import qasync

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui.main_window import MainWindow
from core.logger import get_logger

async def main():
    logger = get_logger("VerifyUI")
    logger.info("Starting UI Verification (Async)...")
    
    try:
        window = MainWindow()
        window.show()
        
        logger.info("MainWindow instantiated and shown.")
        
        # Check if logger attribute exists
        if hasattr(window, 'logger'):
            logger.info("[OK] MainWindow.logger exists.")
        else:
            logger.error("[FAIL] MainWindow.logger MISSING!")
            sys.exit(1)
            
        # Wait a bit
        await asyncio.sleep(3)
        
        logger.info("Closing application...")
        window.close()
        
    except Exception as e:
        logger.error(f"UI Verification Failed: {e}")
        sys.exit(1)

def verify_ui_launch():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    with loop:
        loop.run_until_complete(main())
    
    print("UI Verification Completed Successfully.")

if __name__ == "__main__":
    verify_ui_launch()
