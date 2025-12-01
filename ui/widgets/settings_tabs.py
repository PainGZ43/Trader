import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QMessageBox, QGroupBox, QFormLayout, QCheckBox, QSpinBox, 
                             QComboBox, QAbstractItemView, QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal
from core.config import config
from core.secure_storage import secure_storage
from data.key_manager import key_manager
from core.language import language_manager

class AccountSettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_keys()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Key Management Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Active", "Owner", "Type", "Account No", "Expiry"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Key")
        self.btn_add.clicked.connect(self.add_key_dialog)
        self.btn_del = QPushButton("Delete Key")
        self.btn_del.clicked.connect(self.delete_key)
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.load_keys)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_del)
        btn_layout.addWidget(self.btn_refresh)
        layout.addLayout(btn_layout)
        
        # Auto Login Option
        self.chk_auto_login = QCheckBox("Auto Login with Active Key on Startup")
        self.chk_auto_login.setChecked(key_manager.is_auto_login_enabled())
        self.chk_auto_login.toggled.connect(lambda c: key_manager.set_auto_login_enabled(c))
        layout.addWidget(self.chk_auto_login)

    def load_keys(self):
        self.table.setRowCount(0)
        keys = key_manager.get_keys()
        for row, k in enumerate(keys):
            self.table.insertRow(row)
            
            # Active Radio
            radio_widget = QWidget()
            r_layout = QHBoxLayout(radio_widget)
            r_layout.setContentsMargins(0,0,0,0)
            r_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            radio = QRadioButton()
            if k["is_active"]: radio.setChecked(True)
            radio.clicked.connect(lambda c, uuid=k["uuid"]: self.set_active_key(uuid))
            r_layout.addWidget(radio)
            self.table.setCellWidget(row, 0, radio_widget)
            
            self.table.setItem(row, 1, QTableWidgetItem(k["owner"]))
            self.table.setItem(row, 2, QTableWidgetItem(k["type"]))
            self.table.setItem(row, 3, QTableWidgetItem(k["masked_account_no"]))
            self.table.setItem(row, 4, QTableWidgetItem(k["expiry_date"]))
            
            # Store UUID
            self.table.item(row, 1).setData(Qt.ItemDataRole.UserRole, k["uuid"])

    def set_active_key(self, uuid):
        key_manager.set_active_key(uuid)
        self.load_keys()

    def delete_key(self):
        row = self.table.currentRow()
        if row < 0: return
        uuid = self.table.item(row, 1).data(Qt.ItemDataRole.UserRole)
        if key_manager.delete_key(uuid):
            self.load_keys()

    def add_key_dialog(self):
        try:
            from ui.key_settings_dialog import AddKeyDialog
            dialog = AddKeyDialog(self)
            if dialog.exec():
                self.load_keys()
        except ImportError:
            QMessageBox.warning(self, "Error", "Key Settings Dialog not found.")

    def save_settings(self):
        # Auto-login is saved on toggle, so nothing explicit here
        return False

class StrategySettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # Strategy List
        self.strategy_list = QTableWidget()
        self.strategy_list.setColumnCount(1)
        self.strategy_list.setHorizontalHeaderLabels(["Strategies"])
        self.strategy_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Dummy data
        self.strategy_list.setRowCount(2)
        self.strategy_list.setItem(0, 0, QTableWidgetItem("HybridStrategy"))
        self.strategy_list.setItem(1, 0, QTableWidgetItem("ScalpingStrategy"))
        layout.addWidget(self.strategy_list, 1)
        
        # Parameter Editor
        self.param_group = QGroupBox("Parameters")
        self.param_layout = QFormLayout()
        self.param_group.setLayout(self.param_layout)
        layout.addWidget(self.param_group, 2)
        
        self.strategy_list.itemClicked.connect(self.load_parameters)
        
        # Store widgets to retrieve values later
        self.param_widgets = {}

    def load_parameters(self, item):
        # Clear existing
        while self.param_layout.count():
            child = self.param_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        self.param_widgets = {}
            
        strategy_name = item.text()
        # Mock Schema Loading
        schema = self.get_mock_schema(strategy_name)
        
        for key, meta in schema.items():
            label = QLabel(meta.get("desc", key))
            widget = None
            
            # Load current value from config if exists
            current_val = config.get(f"strategy.{strategy_name}.{key}", meta.get("default"))
            
            if meta["type"] == "int":
                widget = QSpinBox()
                widget.setRange(meta.get("min", 0), meta.get("max", 100))
                widget.setValue(int(current_val))
            elif meta["type"] == "float":
                widget = QSpinBox() # Simplified
                widget.setRange(0, 1000)
                widget.setValue(int(current_val)) # Mock
            elif meta["type"] == "enum":
                widget = QComboBox()
                widget.addItems(meta.get("options", []))
                widget.setCurrentText(str(current_val))
                
            if widget:
                self.param_layout.addRow(label, widget)
                self.param_widgets[key] = widget

    def get_mock_schema(self, name):
        if name == "HybridStrategy":
            return {
                "rsi_period": {"type": "int", "min": 5, "max": 30, "default": 14, "desc": "RSI Period"},
                "ma_type": {"type": "enum", "options": ["SMA", "EMA"], "default": "SMA", "desc": "MA Type"}
            }
        return {}

    def save_settings(self):
        # Save parameters for currently selected strategy
        current_item = self.strategy_list.currentItem()
        if current_item:
            strategy_name = current_item.text()
            for key, widget in self.param_widgets.items():
                val = None
                if isinstance(widget, QSpinBox):
                    val = widget.value()
                elif isinstance(widget, QComboBox):
                    val = widget.currentText()
                
                if val is not None:
                    config.set(f"strategy.{strategy_name}.{key}", val)
        return False

class RiskSettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)
        
        self.max_loss = QSpinBox()
        self.max_loss.setRange(0, 100)
        self.max_loss.setSuffix("%")
        self.max_loss.setValue(config.get("risk.max_loss_pct", 3))
        layout.addRow("Max Daily Loss:", self.max_loss)
        
        self.max_pos = QSpinBox()
        self.max_pos.setRange(0, 100)
        self.max_pos.setSuffix("%")
        self.max_pos.setValue(config.get("risk.max_position_pct", 10))
        layout.addRow("Max Position Size:", self.max_pos)
        
        layout.addRow(QLabel("<b>Notifications</b>"))
        
        self.kakao_token = QLineEdit()
        # Load from SecureStorage
        token = secure_storage.get("kakao_token")
        if token:
            self.kakao_token.setText(token)
            
        self.kakao_token.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Kakao Token:", self.kakao_token)
        
        self.btn_test_msg = QPushButton("Test Message")
        layout.addRow("", self.btn_test_msg)

    def save_settings(self):
        config.set("risk.max_loss_pct", self.max_loss.value())
        config.set("risk.max_position_pct", self.max_pos.value())
        
        # Save to SecureStorage
        token = self.kakao_token.text()
        if token:
            secure_storage.save("kakao_token", token)
        else:
            secure_storage.delete("kakao_token")
            
        return False

class SystemSettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout(self)
        
        # Language Selection
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("한국어 (Korean)", "ko")
        self.lang_combo.addItem("English", "en")
        
        # Set current selection
        current_lang = language_manager.current_lang
        index = self.lang_combo.findData(current_lang)
        if index >= 0:
            self.lang_combo.setCurrentIndex(index)
            
        layout.addRow(language_manager.get_text("lbl_language"), self.lang_combo)

        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level.setCurrentText(config.get("system.log_level", "INFO"))
        layout.addRow(language_manager.get_text("lbl_loglevel"), self.log_level)
        
        # Simulation Mode
        self.sim_mode = QCheckBox(language_manager.get_text("chk_sim_mode"))
        self.sim_mode.setChecked(config.get("system.simulation_mode", True))
        self.sim_mode.setStyleSheet("color: #feca57; font-weight: bold;")
        layout.addRow(language_manager.get_text("lbl_sim_mode"), self.sim_mode)
        
        self.db_path = QLabel("trade.db (15 MB)")
        layout.addRow("Database:", self.db_path)
        
        self.btn_vacuum = QPushButton("Optimize DB (Vacuum)")
        layout.addRow("", self.btn_vacuum)
        
        layout.addRow(QLabel(""))
        self.btn_reset = QPushButton("Factory Reset")
        self.btn_reset.setStyleSheet("background-color: #c0392b; color: white;")
        layout.addRow("Danger Zone:", self.btn_reset)

    def save_settings(self):
        """Save system settings."""
        restart_required = False
        
        # 1. Language
        selected_lang = self.lang_combo.currentData()
        if selected_lang != language_manager.current_lang:
            language_manager.set_language(selected_lang)
            restart_required = True
            
        # 2. Other Settings
        config.set("system.log_level", self.log_level.currentText())
        config.set("system.simulation_mode", self.sim_mode.isChecked())
        
        return restart_required
