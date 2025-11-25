from PyQt6.QtWidgets import QMainWindow, QDockWidget, QLabel, QStatusBar, QToolBar, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from ui.log_viewer import LogViewer
from ui.header_bar import HeaderBar
from ui.dashboard import Dashboard
from data.data_collector import data_collector
from data.key_manager import key_manager
from ui.key_settings_dialog import KeySettingsDialog

class MainWindow(QMainWindow):
    status_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PainTrader - AI Auto Trading System")
        self.resize(1280, 800)
        
        self.status_received.connect(self.update_status_bar)
        
        self.init_ui()

    def init_ui(self):
        # 1. Header Bar (Top)
        self.header_bar = HeaderBar()
        
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.addWidget(self.header_bar)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        # 2. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("System Ready")
        
        # 3. Menu Bar
        self.setup_menu()

        # 4. Dock Manager
        self.setDockOptions(QMainWindow.DockOption.AllowTabbedDocks | QMainWindow.DockOption.AnimatedDocks)

        # 5. Central Widget (Dashboard)
        self.dashboard = Dashboard()
        self.setCentralWidget(self.dashboard)
        
        # Connect DataCollector to Dashboard
        data_collector.add_observer(self.dashboard.on_data_received)
        # Connect DataCollector to MainWindow (for Status Bar)
        data_collector.add_observer(self.on_data_received)

        # 6. Log Viewer Dock (Bottom)
        self.log_dock = QDockWidget("System Logs", self)
        self.log_viewer = LogViewer()
        self.log_dock.setWidget(self.log_viewer)
        self.log_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock)

        # 7. Control Panel Dock (Right) - Placeholder
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
        
        # Delayed initialization for Account Info & Expiration Check (Startup)
        QTimer.singleShot(500, lambda: self.initialize_account_and_check_expiry(startup=True))

    def setup_menu(self):
        from PyQt6.QtGui import QAction
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu('파일')
        exit_action = QAction('종료', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings Menu
        settings_menu = menubar.addMenu('설정')
        
        # API Key Management Action
        key_action = QAction('API 키 관리', self)
        key_action.triggered.connect(self.open_key_settings)
        settings_menu.addAction(key_action)

    def open_key_settings(self):
        dialog = KeySettingsDialog(self)
        dialog.exec()
        
        # Refresh Account Info after dialog closes (Not startup)
        self.initialize_account_and_check_expiry(startup=False)

    def initialize_account_and_check_expiry(self, startup=False):
        """
        Fetch active key info, update header, and check expiration.
        """
        # Check Auto-Login on Startup
        if startup and not key_manager.is_auto_login_enabled():
            self.header_bar.update_account_info(None)
            return

        # 1. Get Active Key Info
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
