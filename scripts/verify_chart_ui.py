import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui.main_window import MainWindow
from core.logger import get_logger

def verify_ui_launch():
    logger = get_logger("VerifyUI")
    logger.info("Starting UI Verification...")
    
    app = QApplication(sys.argv)
    
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
            
        # Close after 3 seconds
        def close_app():
            logger.info("Closing application...")
            window.close()
            app.quit()
            
        QTimer.singleShot(3000, close_app)
        
        app.exec()
        logger.info("UI Verification Completed Successfully.")
        
    except Exception as e:
        logger.error(f"UI Verification Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_ui_launch()
