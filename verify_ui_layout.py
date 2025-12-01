import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QDockWidget
from ui.main_window import MainWindow

def verify_layout():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    print("Verifying UI Layout...")
    
    # 1. Check Central Widget (Dashboard)
    dashboard = window.centralWidget()
    if dashboard and dashboard.isVisible():
        print(f"[PASS] Dashboard is set as Central Widget. Size: {dashboard.size()}")
    else:
        print("[FAIL] Dashboard is missing or hidden.")

    # 2. Check Header
    header = window.menuWidget()
    if header and header.isVisible():
        print(f"[PASS] HeaderBar is set as Menu Widget. Size: {header.size()}")
    else:
        print("[FAIL] HeaderBar is missing or hidden.")

    # 3. Check Docks
    docks = window.findChildren(QDockWidget)
    expected_docks = ["Strategy & Account", "Execution", "Logs & History"]
    found_docks = [d.windowTitle() for d in docks if d.isVisible()]
    
    for expected in expected_docks:
        if expected in found_docks:
            print(f"[PASS] Dock '{expected}' is visible.")
        else:
            print(f"[FAIL] Dock '{expected}' is missing or hidden.")

    # 4. Check Panels inside Docks
    if window.control_panel and window.control_panel.isVisible():
        print(f"[PASS] ControlPanel is visible inside Dock.")
    else:
        print("[FAIL] ControlPanel is not visible.")
        
    if window.order_panel and window.order_panel.isVisible():
        print(f"[PASS] OrderPanel is visible inside Dock.")
    else:
        print("[FAIL] OrderPanel is not visible.")

    if window.log_viewer and window.log_viewer.isVisible():
        print(f"[PASS] LogViewer is visible inside Dock.")
    else:
        print("[FAIL] LogViewer is not visible.")

    print("Layout Verification Complete.")
    app.quit()

if __name__ == "__main__":
    verify_layout()
