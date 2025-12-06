import sys
import os
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.backtest_dialog import BacktestDialog, HAS_WEBENGINE, WEBENGINE_ERROR

def verify_dialog():
    print(f"Python Executable: {sys.executable}")
    print(f"HAS_WEBENGINE: {HAS_WEBENGINE}")
    print(f"WEBENGINE_ERROR: {WEBENGINE_ERROR}")
    
    if not HAS_WEBENGINE:
        print("Attempting manual import to debug...")
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            print("Manual import SUCCESS (Strange...)")
        except ImportError as e:
            print(f"Manual import FAILED: {e}")
        except Exception as e:
            print(f"Manual import ERROR: {e}")

    app = QApplication(sys.argv)
    
    print("Initializing BacktestDialog...")
    try:
        dialog = BacktestDialog()
        print("BacktestDialog initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize BacktestDialog: {e}")
        return

    # Check if thread is running
    if hasattr(dialog, 'update_thread'):
        print("DataUpdateThread created.")
        if dialog.update_thread.isRunning():
            print("DataUpdateThread is running.")
        else:
            print("DataUpdateThread is NOT running (might have finished quickly).")
    else:
        print("DataUpdateThread NOT found.")

    # Wait for thread to finish (simulate event loop)
    def check_thread():
        if dialog.update_thread.isFinished():
            print("DataUpdateThread finished.")
            app.quit()
        else:
            print("Waiting for DataUpdateThread...")

    timer = QTimer()
    timer.timeout.connect(check_thread)
    timer.start(1000) # Check every 1 second

    # Timeout after 10 seconds
    QTimer.singleShot(10000, app.quit)
    
    app.exec()
    print("Verification finished.")

if __name__ == "__main__":
    verify_dialog()
