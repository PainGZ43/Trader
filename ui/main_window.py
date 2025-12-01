import os
from PyQt6.QtWidgets import QMainWindow, QDockWidget, QWidget, QTextEdit, QLabel, QMessageBox
from PyQt6.QtCore import Qt, QSettings, pyqtSignal
from PyQt6.QtGui import QIcon
import qtawesome as qta

from ui.widgets.header_bar import HeaderBar
from ui.dashboard import Dashboard
from core.logger import get_logger

from ui.widgets.control_panel import ControlPanel
from ui.widgets.order_panel import OrderPanel
from ui.settings_dialog import SettingsDialog
from ui.log_viewer import LogViewer
from ui.log_viewer import LogViewer
from core.event_bus import event_bus
from core.language import language_manager

class MainWindow(QMainWindow):
    # Backend -> UI Signals
    update_macro_signal = pyqtSignal(dict)
    update_tick_signal = pyqtSignal(dict)
    update_orderbook_signal = pyqtSignal(dict)
    update_account_signal = pyqtSignal(dict)
    update_portfolio_signal = pyqtSignal(list)
    system_error_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.logger = get_logger("MainWindow")
        self.setWindowTitle(language_manager.get_text("window_title"))
        self.resize(1600, 900)
        
        # Load Styles
        self._load_stylesheet()
        
        # Setup UI
        self._init_ui()
        
        # Connect Signals (EventBus <-> UI)
        self._connect_signals()
        
        # Restore State
        self._restore_state()

    def _load_stylesheet(self):
        try:
            style_path = os.path.join(os.path.dirname(__file__), "styles.qss")
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            self.logger.error(f"Failed to load stylesheet: {e}")

    def _init_ui(self):
        # 1. Header Bar
        self.header = HeaderBar(self)
        self.header.settings_btn.clicked.connect(self.open_settings)
        self.setMenuWidget(self.header) # Use setMenuWidget to place it at top
        
        # 2. Central Widget (Dashboard)
        self.dashboard = Dashboard()
        self.setCentralWidget(self.dashboard)
        
        # 3. Dock Widgets
        self._create_dock_widgets()

    def _create_dock_widgets(self):
        # Left Panel (Strategy & Account)
        self.dock_left = self._create_dock(language_manager.get_text("dock_strategy"), Qt.DockWidgetArea.LeftDockWidgetArea)
        self.control_panel = ControlPanel()
        self.dock_left.setWidget(self.control_panel)
        
        # Right Panel (Order Book & Execution)
        self.dock_right = self._create_dock(language_manager.get_text("dock_execution"), Qt.DockWidgetArea.RightDockWidgetArea)
        self.order_panel = OrderPanel()
        self.dock_right.setWidget(self.order_panel)
        
        # Bottom Panel (Logs & History)
        self.dock_bottom = self._create_dock(language_manager.get_text("dock_logs"), Qt.DockWidgetArea.BottomDockWidgetArea)
        self.log_viewer = LogViewer()
        self.dock_bottom.setWidget(self.log_viewer)

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def _create_dock(self, title, area):
        dock = QDockWidget(title, self)
        dock.setObjectName(title) # Required for saveState
        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.addDockWidget(area, dock)
        return dock

    def _connect_signals(self):
        """Connect EventBus events to UI signals and UI actions to EventBus."""
        # 1. Subscribe to Backend Events (Background Thread -> Main Thread via Signal)
        event_bus.subscribe("market.data.macro", lambda e: self.update_macro_signal.emit(e.data))
        event_bus.subscribe("market.data.tick", lambda e: self.update_tick_signal.emit(e.data))
        event_bus.subscribe("market.data.orderbook", lambda e: self.update_orderbook_signal.emit(e.data))
        event_bus.subscribe("account.summary", lambda e: self.update_account_signal.emit(e.data))
        event_bus.subscribe("account.portfolio", lambda e: self.update_portfolio_signal.emit(e.data))
        event_bus.subscribe("system.error", lambda e: self.system_error_signal.emit(e.data))
        
        # 2. Connect Signals to UI Slots
        self.update_macro_signal.connect(self.header.update_macro)
        self.update_tick_signal.connect(lambda d: self.dashboard.process_data({"type": "REALTIME", **d}))
        self.update_orderbook_signal.connect(lambda d: self.dashboard.process_data({"type": "ORDERBOOK", **d}))
        
        self.update_account_signal.connect(lambda d: self.control_panel.update_account_summary(
            d.get("total_asset", 0), d.get("deposit", 0), d.get("total_pnl", 0), d.get("pnl_pct", 0)
        ))
        self.update_portfolio_signal.connect(self.control_panel.update_portfolio)
        
        self.system_error_signal.connect(self._on_system_error)
        
        # 3. Connect UI Actions to Backend (Main Thread -> EventBus)
        self.order_panel.send_order_signal.connect(lambda order: event_bus.publish("order.create", order))
        self.order_panel.panic_signal.connect(lambda action: event_bus.publish("system.panic", {"action": action}))
        self.control_panel.close_position_signal.connect(lambda code: event_bus.publish("order.close", {"code": code}))

    def _on_system_error(self, data):
        level = data.get("level", "WARNING")
        msg = data.get("message", "Unknown Error")
        if level == "CRITICAL":
            QMessageBox.critical(self, "Critical Error", msg)
        else:
            self.statusBar().showMessage(f"Error: {msg}", 5000)

    def closeEvent(self, event):
        """Save state and shutdown gracefully."""
        self._save_state()
        
        # Trigger Graceful Shutdown
        event_bus.publish("system.shutdown")
        
        # Wait a bit? (In a real app, we might want to wait for a 'shutdown.complete' signal)
        # For now, we just proceed.
        super().closeEvent(event)

    def _save_state(self):
        settings = QSettings("PainTrader", "MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        self.logger.info("Window state saved.")

    def _restore_state(self):
        settings = QSettings("PainTrader", "MainWindow")
        if settings.value("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.value("windowState"):
            self.restoreState(settings.value("windowState"))
        self.logger.info("Window state restored.")
