from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
import qtawesome as qta
import psutil
from core.language import language_manager

class HeaderBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HeaderBar")
        self.setFixedHeight(50)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.layout.setSpacing(15)
        
        self._init_ui()
        self.latency = 0
        self._start_monitoring()

    def _init_ui(self):
        # 1. Logo Area
        logo_icon = qta.icon('fa5s.robot', color='#007acc')
        self.logo_btn = QPushButton()
        self.logo_btn.setIcon(logo_icon)
        self.logo_btn.setFlat(True)
        self.logo_btn.setStyleSheet("border: none; background: transparent;")
        
        self.logo_btn.setStyleSheet("border: none; background: transparent;")
        
        self.title_label = QLabel(language_manager.get_text("header_title"))
        self.title_label.setObjectName("LogoLabel")
        
        self.layout.addWidget(self.logo_btn)
        self.layout.addWidget(self.title_label)
        
        self.layout.addStretch(1)
        
        # 2. Macro Indicators (Placeholders)
        self.kospi_label = self._create_macro_label("KOSPI", "2,500.00", "+0.5%")
        self.kosdaq_label = self._create_macro_label("KOSDAQ", "850.00", "-0.2%")
        self.usd_label = self._create_macro_label("USD/KRW", "1,300.0", "+1.5")
        
        self.layout.addWidget(self.kospi_label)
        self.layout.addWidget(self.kosdaq_label)
        self.layout.addWidget(self.usd_label)
        
        self.layout.addStretch(1)
        
        # 3. System Status
        self.api_status = self._create_status_indicator("API", "fa5s.circle", "gray")
        self.db_status = self._create_status_indicator("DB", "fa5s.database", "green")
        self.socket_status = self._create_status_indicator("WS", "fa5s.bolt", "gray")
        
        self.layout.addWidget(self.api_status)
        self.layout.addWidget(self.db_status)
        self.layout.addWidget(self.socket_status)
        
        # CPU/Mem/Latency Monitor
        self.resource_label = QLabel("CPU: 0% | MEM: 0% | LAT: -ms")
        self.resource_label.setStyleSheet("color: #888; font-size: 11px;")
        self.layout.addWidget(self.resource_label)
        
        # 4. Global Controls
        self.start_btn = QPushButton(language_manager.get_text("btn_start"))
        self.start_btn.setIcon(qta.icon('fa5s.play', color='#4caf50'))
        
        self.stop_btn = QPushButton(language_manager.get_text("btn_stop"))
        self.stop_btn.setIcon(qta.icon('fa5s.stop', color='#f44336'))
        
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(qta.icon('fa5s.cog', color='white'))
        
        self.layout.addWidget(self.start_btn)
        self.layout.addWidget(self.stop_btn)
        self.layout.addWidget(self.settings_btn)

    def _create_macro_label(self, name, value, change):
        lbl = QLabel(f"{name} {value} ({change})")
        # Color logic based on change
        if "+" in change:
            lbl.setStyleSheet("color: #ff5252; font-weight: bold;") # Red for up (KR market)
        elif "-" in change:
            lbl.setStyleSheet("color: #448aff; font-weight: bold;") # Blue for down
        else:
            lbl.setStyleSheet("color: white;")
        return lbl

    def update_macro(self, data):
        """Update macro indicators."""
        indices = data.get("indices", {})
        rate = data.get("exchange_rate", 0.0)
        
        # Helper to update label text and color
        def update_lbl(lbl, name, val, change):
            lbl.setText(f"{name} {val} ({change})")
            if "+" in str(change):
                lbl.setStyleSheet("color: #ff5252; font-weight: bold;")
            elif "-" in str(change):
                lbl.setStyleSheet("color: #448aff; font-weight: bold;")
            else:
                lbl.setStyleSheet("color: white;")

        # Parse data (Assuming data comes in as raw values, we might need change calc or data includes it)
        # For now, assuming data includes 'change' or we just show value.
        # Let's assume data structure: {'KOSPI': {'value': '2500', 'change': '+0.5%'}, ...}
        # Or simple: {'indices': {'KOSPI': '2500'}, 'exchange_rate': '1300'}
        # The current Dashboard logic was: KOSPI: {indices.get('KOSPI')}
        
        # Let's adapt to what Dashboard was doing but make it better if possible.
        # Dashboard: self.kospi_label.setText(f"KOSPI: {indices.get('KOSPI', '-')}")
        
        k_val = indices.get('KOSPI', '-')
        kq_val = indices.get('KOSDAQ', '-')
        
        # We don't have change data in the simple dict passed to dashboard. 
        # We will just update the text for now.
        self.kospi_label.setText(f"KOSPI {k_val}")
        self.kosdaq_label.setText(f"KOSDAQ {kq_val}")
        self.usd_label.setText(f"USD/KRW {rate}")

    def _create_status_indicator(self, text, icon_name, color):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        icon = QLabel()
        icon.setPixmap(qta.icon(icon_name, color=color).pixmap(16, 16))
        
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 11px; color: #ccc;")
        
        layout.addWidget(icon)
        layout.addWidget(lbl)
        return widget

    def _start_monitoring(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_resources)
        self.timer.start(2000) # Every 2 sec
        
        # Heartbeat Blink Timer
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self._blink_heartbeat)
        self.blink_timer.start(500)
        self.blink_state = False

    def _update_resources(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        # Latency would be updated via a separate method called by MainWindow
        self.resource_label.setText(f"{language_manager.get_text('cpu')}: {cpu}% | {language_manager.get_text('mem')}: {mem}% | {language_manager.get_text('lat')}: {self.latency}ms")
        
        # Warning color
        if cpu > 80 or mem > 80:
            self.resource_label.setStyleSheet("color: #ff5252; font-weight: bold; font-size: 11px;")
        else:
            self.resource_label.setStyleSheet("color: #888; font-size: 11px;")

    def update_latency(self, ms):
        self.latency = ms
        # Immediate update or wait for timer? Timer is better for stability.
        # Just store it.
        
    def _blink_heartbeat(self):
        # Blink WS icon if connected
        if hasattr(self, 'ws_connected') and self.ws_connected:
            self.blink_state = not self.blink_state
            color = "#4caf50" if self.blink_state else "#2ecc71" # Blink Green/LightGreen
            icon_label = self.socket_status.findChild(QLabel)
            if icon_label:
                icon_label.setPixmap(qta.icon("fa5s.bolt", color=color).pixmap(16, 16))

    def update_status(self, target: str, status: bool):
        """Update status icons (API, DB, WS)."""
        color = "#4caf50" if status else "#f44336" # Green / Red
        icon_map = {
            "API": ("fa5s.circle", self.api_status),
            "DB": ("fa5s.database", self.db_status),
            "WS": ("fa5s.bolt", self.socket_status)
        }
        
        if target == "WS":
            self.ws_connected = status
        
        if target in icon_map:
            icon_name, widget = icon_map[target]
            icon_label = widget.findChild(QLabel) # First label is icon
            if icon_label:
                icon_label.setPixmap(qta.icon(icon_name, color=color).pixmap(16, 16))
