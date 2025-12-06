import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Add project root
sys.path.append(os.getcwd())

from ui.backtest_dialog import BacktestDialog

def main():
    app = QApplication(sys.argv)
    
    dialog = BacktestDialog()
    dialog.show()
    
    # Auto-close after 5 seconds for automated testing, or keep open for manual
    # QTimer.singleShot(5000, dialog.close)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
