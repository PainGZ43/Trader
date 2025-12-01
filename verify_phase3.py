import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.widgets.control_panel import ControlPanel
from ui.widgets.order_panel import OrderPanel

def verify_phase3():
    app = QApplication(sys.argv)
    
    print("Initializing MainWindow...")
    try:
        window = MainWindow()
        window.show()
        print("MainWindow initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize MainWindow: {e}")
        return

    print("Checking Dock Widgets...")
    control_panel = window.findChild(ControlPanel)
    order_panel = window.findChild(OrderPanel)
    
    if control_panel:
        print("ControlPanel found in Dock.")
    else:
        print("ERROR: ControlPanel not found.")
        
    if order_panel:
        print("OrderPanel found in Dock.")
    else:
        print("ERROR: OrderPanel not found.")
        
    print("Verification complete. Closing in 3 seconds...")
    # QTimer.singleShot(3000, app.quit)
    # app.exec()

if __name__ == "__main__":
    verify_phase3()
