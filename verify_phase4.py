import sys
from PyQt6.QtWidgets import QApplication, QTabWidget
from ui.main_window import MainWindow
from ui.settings_dialog import SettingsDialog
from ui.log_viewer import LogViewer

def verify_phase4():
    app = QApplication(sys.argv)
    
    print("Initializing MainWindow...")
    try:
        window = MainWindow()
        window.show()
        print("MainWindow initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize MainWindow: {e}")
        return

    print("Checking LogViewer...")
    log_viewer = window.findChild(LogViewer)
    if log_viewer:
        print("LogViewer found in Dock.")
    else:
        print("ERROR: LogViewer not found.")

    print("Checking SettingsDialog...")
    try:
        dialog = SettingsDialog(window)
        print("SettingsDialog initialized.")
        
        tabs = dialog.findChild(QTabWidget)
        if tabs:
            count = tabs.count()
            print(f"SettingsDialog has {count} tabs.")
            expected_tabs = ["Accounts & API", "Strategy Tuning", "Risk & Notification", "System Health"]
            for i in range(count):
                label = tabs.tabText(i)
                if label in expected_tabs:
                    print(f"  - Tab {i}: {label} (Found)")
                else:
                    print(f"  - Tab {i}: {label} (Unexpected)")
        else:
            print("ERROR: QTabWidget not found in SettingsDialog.")
            
        dialog.close()
    except Exception as e:
        print(f"Failed to initialize SettingsDialog: {e}")

    print("Verification complete. Closing in 3 seconds...")
    # QTimer.singleShot(3000, app.quit)
    # app.exec()

if __name__ == "__main__":
    verify_phase4()
