from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QFrame
from PyQt6.QtCore import Qt, QTimer, QTime

class HeaderBar(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_timer()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 1. System Title / Logo Area
        title_label = QLabel("PainTrader")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00d2d3;")
        layout.addWidget(title_label)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # 2. Market Info (Macro) - Placeholder
        self.kospi_label = QLabel("KOSPI: -")
        self.kosdaq_label = QLabel("KOSDAQ: -")
        self.usd_label = QLabel("USD/KRW: -")
        
        for lbl in [self.kospi_label, self.kosdaq_label, self.usd_label]:
            lbl.setStyleSheet("color: #bdc3c7; margin-right: 10px;")
            layout.addWidget(lbl)

        layout.addStretch()

        # 3. Account Info (Active Key)
        self.account_info_widget = QWidget()
        acc_layout = QHBoxLayout(self.account_info_widget)
        acc_layout.setContentsMargins(0, 0, 20, 0)
        
        self.acc_owner_label = QLabel("")
        self.acc_owner_label.setStyleSheet("color: #ecf0f1; font-weight: bold; margin-right: 10px;")
        
        self.acc_no_label = QLabel("")
        self.acc_no_label.setStyleSheet("color: #bdc3c7; margin-right: 10px;")
        
        self.acc_type_label = QLabel("") # MOCK/REAL
        self.acc_type_label.setStyleSheet("color: #f1c40f; font-weight: bold; border: 1px solid #f1c40f; padding: 2px 5px; border-radius: 3px;")
        
        acc_layout.addWidget(self.acc_owner_label)
        acc_layout.addWidget(self.acc_no_label)
        acc_layout.addWidget(self.acc_type_label)
        
        layout.addWidget(self.account_info_widget)

        # 4. System Status (Time & Connection)
        self.time_label = QLabel("00:00:00")
        self.time_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-right: 15px;")
        layout.addWidget(self.time_label)

        self.status_indicator = QLabel("● DISCONNECTED")
        self.status_indicator.setStyleSheet("color: #ff6b6b; font-weight: bold;") # Red initially
        layout.addWidget(self.status_indicator)

        # 4. Global Controls
        self.btn_start = QPushButton("START")
        self.btn_start.setCheckable(True)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71; color: white; font-weight: bold; padding: 5px 15px; border-radius: 3px;
            }
            QPushButton:checked {
                background-color: #e74c3c; text-align: center;
            }
        """)
        self.btn_start.toggled.connect(self.on_start_toggled)
        layout.addWidget(self.btn_start)

        self.btn_settings = QPushButton("SETTINGS")
        self.btn_settings.setStyleSheet("background-color: #34495e; color: white; padding: 5px 10px; border-radius: 3px;")
        self.btn_settings.clicked.connect(self.open_settings)
        layout.addWidget(self.btn_settings)

    def open_settings(self):
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec()

        # Background Style
        self.setStyleSheet("background-color: #2c3e50; border-bottom: 1px solid #34495e;")
        self.setFixedHeight(50)

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()

    def update_time(self):
        current_time = QTime.currentTime().toString("HH:mm:ss")
        self.time_label.setText(current_time)

    def on_start_toggled(self, checked):
        if checked:
            self.btn_start.setText("STOP")
            self.btn_start.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 5px 15px; border-radius: 3px;")
        else:
            self.btn_start.setText("START")
            self.btn_start.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 5px 15px; border-radius: 3px;")

    def set_connection_status(self, connected: bool):
        if connected:
            self.status_indicator.setText("● CONNECTED")
            self.status_indicator.setStyleSheet("color: #2ecc71; font-weight: bold;") # Green
        else:
            self.status_indicator.setText("● DISCONNECTED")
            self.status_indicator.setStyleSheet("color: #ff6b6b; font-weight: bold;") # Red

    def update_account_info(self, info: dict):
        """
        Update account info labels.
        info: {
            "owner": str,
            "account_no": str, # Masked
            "type": str, # MOCK/REAL
            "expiry_date": str
        }
        """
        if not info:
            self.acc_owner_label.setText("")
            self.acc_no_label.setText("")
            self.acc_type_label.setText("")
            self.acc_type_label.hide()
            return

        self.acc_owner_label.setText(info.get("owner", ""))
        self.acc_no_label.setText(info.get("masked_account_no", ""))
        
        key_type = info.get("type", "MOCK")
        self.acc_type_label.setText(key_type)
        self.acc_type_label.show()
        
        if key_type == "REAL":
            self.acc_type_label.setStyleSheet("color: #e74c3c; font-weight: bold; border: 1px solid #e74c3c; padding: 2px 5px; border-radius: 3px;")
        else:
            self.acc_type_label.setStyleSheet("color: #f1c40f; font-weight: bold; border: 1px solid #f1c40f; padding: 2px 5px; border-radius: 3px;")
