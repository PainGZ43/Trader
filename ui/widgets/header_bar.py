from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
import qtawesome as qta
import psutil
from core.language import language_manager

class MacroWidget(QWidget):
    """
    Custom Widget for Macro Indicators (Naver Style).
    [ Title ]
    [ Value (Large) ]
    [ Icon Change (Small) ]
    """
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 2, 5, 2)
        self.layout.setSpacing(0)
        
        # Title
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("color: #888; font-size: 11px; font-weight: bold;")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Value
        self.value_lbl = QLabel("--")
        self.value_lbl.setStyleSheet("color: #e0e0e0; font-size: 16px; font-weight: bold;")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Change Container
        change_widget = QWidget()
        change_layout = QHBoxLayout(change_widget)
        change_layout.setContentsMargins(0, 0, 0, 0)
        change_layout.setSpacing(4)
        
        self.icon_lbl = QLabel()
        self.change_lbl = QLabel("-")
        self.change_lbl.setStyleSheet("font-size: 11px;")
        
        change_layout.addWidget(self.icon_lbl)
        change_layout.addWidget(self.change_lbl)
        change_layout.addStretch(1)
        
        self.layout.addWidget(self.title_lbl)
        self.layout.addWidget(self.value_lbl)
        self.layout.addWidget(change_widget)
        
        # Fixed Width for consistency
        self.setFixedWidth(120)

    def update_data(self, value, change_amt="-", change_pct="-"):
        # Value
        if isinstance(value, float):
            self.value_lbl.setText(f"{value:,.2f}")
        else:
            self.value_lbl.setText(str(value))
            
        # Change Logic
        # change_amt might be string with sign or float
        # change_pct might be string "0.5%" or float
        
        try:
            # Determine direction
            is_up = False
            is_down = False
            
            if isinstance(change_amt, (int, float)):
                if change_amt > 0: is_up = True
                elif change_amt < 0: is_down = True
            elif isinstance(change_amt, str):
                if "+" in change_amt or (change_amt.replace(".", "").isdigit() and float(change_amt) > 0):
                    is_up = True
                elif "-" in change_amt:
                    is_down = True
            
            # Set Style
            if is_up:
                color = "#ff6b6b"
                icon = qta.icon('fa5s.caret-up', color=color)
                self.value_lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
                self.change_lbl.setStyleSheet(f"color: {color}; font-size: 11px;")
            elif is_down:
                color = "#54a0ff"
                icon = qta.icon('fa5s.caret-down', color=color)
                self.value_lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
                self.change_lbl.setStyleSheet(f"color: {color}; font-size: 11px;")
            else:
                color = "#e0e0e0"
                icon = qta.icon('fa5s.minus', color=color)
                self.value_lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
                self.change_lbl.setStyleSheet(f"color: {color}; font-size: 11px;")
                
            self.icon_lbl.setPixmap(icon.pixmap(10, 10))
            self.change_lbl.setText(f"{change_amt} ({change_pct})")
            
        except Exception as e:
            print(f"MacroWidget Error: {e}")


class HeaderBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HeaderBar")
        self.setFixedHeight(60) # Increased height for new widget
        
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
        self.logo_btn.setIconSize(qta.QtCore.QSize(24, 24))
        self.logo_btn.setFlat(True)
        self.logo_btn.setStyleSheet("border: none; background: transparent;")
        
        self.title_label = QLabel(language_manager.get_text("header_title"))
        self.title_label.setObjectName("LogoLabel")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #0098ff;")
        
        self.layout.addWidget(self.logo_btn)
        self.layout.addWidget(self.title_label)
        
        self.layout.addStretch(1)
        
        # 2. Macro Indicators (Naver Style)
        self.kospi_widget = MacroWidget("KOSPI")
        self.kosdaq_widget = MacroWidget("KOSDAQ")
        self.usd_widget = MacroWidget("USD/KRW")
        
        self.layout.addWidget(self.kospi_widget)
        self.layout.addWidget(self.kosdaq_widget)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #3e3e42;")
        self.layout.addWidget(line)
        
        self.layout.addWidget(self.usd_widget)
        
        self.layout.addStretch(1)
        
        # 2.5 Account Info (Keep simple for now, or upgrade later)
        self.asset_label = QLabel(f"{language_manager.get_text('total_asset')} --")
        self.asset_label.setStyleSheet("color: #ccc; font-weight: bold;")
        self.layout.addWidget(self.asset_label)
        
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
        
        self.btn_backtest = QPushButton("Backtest")
        self.btn_backtest.setIcon(qta.icon('fa5s.flask', color='#f1c40f'))
        self.layout.addWidget(self.btn_backtest)

        self.layout.addWidget(self.start_btn)
        self.layout.addWidget(self.stop_btn)
        self.layout.addWidget(self.settings_btn)

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
        
    def _blink_heartbeat(self):
        # Blink WS icon if connected
        if hasattr(self, 'ws_connected') and self.ws_connected:
            self.blink_state = not self.blink_state
            color = "#4caf50" if self.blink_state else "#2ecc71" # Blink Green/LightGreen
            icon_label = self.socket_status.findChild(QLabel)
            if icon_label:
                icon_label.setPixmap(qta.icon("fa5s.bolt", color=color).pixmap(16, 16))

    def update_macro(self, data):
        """Update macro indicators."""
        indices = data.get("indices", {})
        changes = data.get("changes", {})
        rate = data.get("exchange_rate", 0.0)
        
        # Helper to parse "Amt (Pct%)"
        def parse_change(change_str):
            amt, pct = "-", "-"
            if "(" in str(change_str):
                try:
                    parts = str(change_str).split("(")
                    amt = parts[0].strip()
                    pct = parts[1].replace(")", "").replace("%", "") + "%"
                except:
                    amt = change_str
            else:
                amt = change_str
            return amt, pct

        # Update KOSPI
        k_amt, k_pct = parse_change(changes.get('KOSPI', '-'))
        self.kospi_widget.update_data(indices.get('KOSPI', 0.0), k_amt, k_pct)
        
        # Update KOSDAQ
        kq_amt, kq_pct = parse_change(changes.get('KOSDAQ', '-'))
        self.kosdaq_widget.update_data(indices.get('KOSDAQ', 0.0), kq_amt, kq_pct)
        
        # Update USD/KRW
        u_amt, u_pct = parse_change(changes.get('USD/KRW', '-'))
        self.usd_widget.update_data(rate, u_amt, u_pct)

    def update_account_info(self, data):
        """Update account info labels."""
        balance = data.get("balance", {})
        total_asset = balance.get("total_asset", 0)
        
        def fmt(val):
            return f"{val:,.0f}" if val else "0"
            
        self.asset_label.setText(f"{language_manager.get_text('total_asset')} {fmt(total_asset)}")

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

    def update_status(self, target: str, status: bool):
        """Update status icons (API, DB, WS)."""
        color = "#4ec9b0" if status else "#f14c4c" # Green / Red (Premium)
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
