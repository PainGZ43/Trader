from PyQt6.QtWidgets import QMainWindow, QDockWidget, QLabel, QStatusBar, QToolBar
from PyQt6.QtCore import Qt, pyqtSignal
from ui.log_viewer import LogViewer
from ui.header_bar import HeaderBar
from ui.dashboard import Dashboard
from data.data_collector import data_collector

class MainWindow(QMainWindow):
    status_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PainTrader - AI Auto Trading System")
        self.resize(1280, 800)
        
        self.status_received.connect(self.update_status_bar)
        
        self.init_ui()

    def init_ui(self):
        # ... (existing init_ui code) ...
        # 1. Header Bar (Top)
        self.header_bar = HeaderBar()
        
        from PyQt6.QtWidgets import QToolBar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.addWidget(self.header_bar)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        # 2. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("System Ready")

        # 3. Dock Manager
        self.setDockOptions(QMainWindow.DockOption.AllowTabbedDocks | QMainWindow.DockOption.AnimatedDocks)

        # 4. Central Widget (Dashboard)
        self.dashboard = Dashboard()
        self.setCentralWidget(self.dashboard)
        
        # Connect DataCollector to Dashboard
        data_collector.add_observer(self.dashboard.on_data_received)
        # Connect DataCollector to MainWindow (for Status Bar)
        data_collector.add_observer(self.on_data_received)

        # 5. Log Viewer Dock (Bottom)
        self.log_dock = QDockWidget("System Logs", self)
        self.log_viewer = LogViewer()
        self.log_dock.setWidget(self.log_viewer)
        self.log_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock)

        # 6. Control Panel Dock (Right) - Placeholder
        self.control_dock = QDockWidget("Control Panel", self)
        self.control_label = QLabel("Strategy & Account Info")
        self.control_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.control_dock.setWidget(self.control_label)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.control_dock)

        # Apply Dark Theme (Basic)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QDockWidget {
                color: white;
                font-weight: bold;
            }
            QDockWidget::title {
                background: #3c3c3c;
                padding-left: 5px;
            }
        """)
        
        # Delayed initialization for Account Info & Expiration Check
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, self.initialize_account_and_check_expiry)

    def initialize_account_and_check_expiry(self):
        """
        Fetch active key info, update header, and check expiration.
        """
        from data.key_manager import key_manager
        from PyQt6.QtWidgets import QMessageBox
        
        # 1. Get Active Key Info
        # We need full info including masked account no, so we use get_keys and find active
        keys = key_manager.get_keys()
        active_key = next((k for k in keys if k["is_active"]), None)
        
        if active_key:
            # Update Header Bar
            self.header_bar.update_account_info(active_key)
            
            # 2. Check Expiration (Active Only)
            warning = key_manager.check_active_key_expiration()
            if warning:
                QMessageBox.warning(self, "API 키 만료 경고", warning)
        else:
            self.header_bar.update_account_info(None)

    def on_data_received(self, data):
        """
        Handle DataCollector events.
        """
        if data.get("type") == "STATUS":
            self.status_received.emit(data)

    def update_status_bar(self, data):
        """
        Update Status Bar UI.
        """
        is_open = data.get("market_open", False)
        is_connected = data.get("api_connected", False)
        
        market_text = "Market: OPEN" if is_open else "Market: CLOSED"
        api_text = "API: Connected" if is_connected else "API: Disconnected"
        
        self.status_bar.showMessage(f"{api_text} | {market_text}")
