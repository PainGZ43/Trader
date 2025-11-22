from PyQt6.QtWidgets import QMainWindow, QDockWidget, QLabel, QStatusBar
from PyQt6.QtCore import Qt
from ui.log_viewer import LogViewer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PainTrader - AI Auto Trading System")
        self.resize(1280, 800)
        self.init_ui()

    def init_ui(self):
        # 1. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("System Ready")

        # 2. Dock Manager
        self.setDockOptions(QMainWindow.DockOption.AllowTabbedDocks | QMainWindow.DockOption.AnimatedDocks)

        # 3. Central Widget (Dashboard placeholder)
        # For now, we can use a placeholder or make the chart the central widget later.
        self.central_label = QLabel("Dashboard Area (Chart & OrderBook)")
        self.central_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.central_label.setStyleSheet("background-color: #2d2d2d; color: white; font-size: 20px;")
        self.setCentralWidget(self.central_label)

        # 4. Log Viewer Dock (Bottom)
        self.log_dock = QDockWidget("System Logs", self)
        self.log_viewer = LogViewer()
        self.log_dock.setWidget(self.log_viewer)
        self.log_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock)

        # 5. Control Panel Dock (Right) - Placeholder
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
