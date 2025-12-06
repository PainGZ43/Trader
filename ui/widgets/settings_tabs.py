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
        self.table.setHorizontalHeaderLabels(["활성", "소유자", "유형", "계좌번호", "만료일"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("키 추가")
        self.btn_add.clicked.connect(self.add_key_dialog)
        self.btn_del = QPushButton("키 삭제")
        self.btn_del.clicked.connect(self.delete_key)
        self.btn_refresh = QPushButton("새로고침")
        self.btn_refresh.clicked.connect(self.load_keys)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_del)
        btn_layout.addWidget(self.btn_refresh)
        layout.addLayout(btn_layout)
        
        # Auto Login Option
        self.chk_auto_login = QCheckBox("시작 시 활성 키로 자동 로그인")
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

from strategy.registry import StrategyRegistry

class StrategySettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        # Ensure registry is initialized
        StrategyRegistry.initialize()
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # Strategy List
        self.strategy_list = QTableWidget()
        self.strategy_list.setColumnCount(1)
        self.strategy_list.setHorizontalHeaderLabels(["전략 목록"])
        self.strategy_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Available Strategies from Registry
        strategies = StrategyRegistry.get_all_strategies()
        
        self.strategy_list.setRowCount(len(strategies))
        for i, name in enumerate(strategies):
            self.strategy_list.setItem(i, 0, QTableWidgetItem(name))
        layout.addWidget(self.strategy_list, 1)
        
        # Parameter Editor
        self.param_group = QGroupBox("파라미터 설정")
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
        
        # Load Schema from Registry
        schema = StrategyRegistry.get_strategy_schema(strategy_name)
        description = StrategyRegistry.get_strategy_description(strategy_name)
        
        # Add Description Label
        if description:
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: gray; font-style: italic; margin-bottom: 10px;")
            self.param_layout.addRow(desc_label)
        
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
                widget = QSpinBox() # Using DoubleSpinBox for float
                # QSpinBox is for int, need QDoubleSpinBox
                from PyQt6.QtWidgets import QDoubleSpinBox
                widget = QDoubleSpinBox()
                widget.setRange(meta.get("min", 0.0), meta.get("max", 1000.0))
                widget.setSingleStep(0.1)
                widget.setDecimals(2)
                widget.setValue(float(current_val))
            elif meta["type"] == "enum":
                widget = QComboBox()
                widget.addItems(meta.get("options", []))
                widget.setCurrentText(str(current_val))
                
            if widget:
                self.param_layout.addRow(label, widget)
                self.param_widgets[key] = widget

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
                # Handle QDoubleSpinBox
                from PyQt6.QtWidgets import QDoubleSpinBox
                if isinstance(widget, QDoubleSpinBox):
                    val = widget.value()
                
                if val is not None:
                    config.set(f"strategy.{strategy_name}.{key}", val)
        return False

class RiskSettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Risk Parameters Group
        risk_group = QGroupBox("리스크 관리")
        risk_layout = QFormLayout()
        
        self.max_loss = QSpinBox()
        self.max_loss.setRange(0, 100)
        self.max_loss.setSuffix("%")
        self.max_loss.setValue(int(config.get("risk.max_loss_pct", 3)))
        risk_layout.addRow("일일 최대 손실률:", self.max_loss)
        
        self.max_pos = QSpinBox()
        self.max_pos.setRange(0, 100)
        self.max_pos.setSuffix("%")
        self.max_pos.setValue(int(config.get("risk.max_position_pct", 10)))
        risk_layout.addRow("최대 포지션 크기:", self.max_pos)
        
        risk_group.setLayout(risk_layout)
        layout.addWidget(risk_group)
        
        # Kakao Notification Group
        kakao_group = QGroupBox("카카오톡 알림")
        kakao_layout = QFormLayout()
        
        # 1. REST API Key
        self.kakao_app_key = QLineEdit()
        self.kakao_app_key.setEchoMode(QLineEdit.EchoMode.Password)
        app_key = secure_storage.get("kakao_app_key") or config.get("KAKAO_APP_KEY", "")
        self.kakao_app_key.setText(app_key)
        kakao_layout.addRow("REST API 키:", self.kakao_app_key)
        
        # 2. Auth Code Flow
        btn_guide = QPushButton("1. 로그인 및 코드 발급")
        btn_guide.clicked.connect(self.open_kakao_login)
        kakao_layout.addRow("", btn_guide)
        
        self.auth_code = QLineEdit()
        self.auth_code.setPlaceholderText("리다이렉트 URL의 코드를 여기에 붙여넣으세요")
        kakao_layout.addRow("인증 코드:", self.auth_code)
        
        btn_exchange = QPushButton("2. 토큰 생성")
        btn_exchange.clicked.connect(self.exchange_token)
        kakao_layout.addRow("", btn_exchange)
        
        # 3. Tokens
        self.access_token = QLineEdit()
        self.access_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.access_token.setReadOnly(False) # Allow manual paste if needed
        acc_token = secure_storage.get("kakao_access_token") or config.get("KAKAO_ACCESS_TOKEN", "")
        self.access_token.setText(acc_token)
        kakao_layout.addRow("액세스 토큰:", self.access_token)
        
        self.refresh_token = QLineEdit()
        self.refresh_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.refresh_token.setReadOnly(False)
        ref_token = secure_storage.get("kakao_refresh_token") or config.get("KAKAO_REFRESH_TOKEN", "")
        self.refresh_token.setText(ref_token)
        kakao_layout.addRow("리프레시 토큰:", self.refresh_token)
        
        # 4. Test
        self.btn_test_msg = QPushButton("테스트 메시지 전송")
        self.btn_test_msg.clicked.connect(self.send_test_message)
        kakao_layout.addRow("", self.btn_test_msg)
        
        kakao_group.setLayout(kakao_layout)
        layout.addWidget(kakao_group)
        
        layout.addStretch()

    def open_kakao_login(self):
        """Open browser for Kakao Login."""
        app_key = self.kakao_app_key.text().strip()
        if not app_key:
            QMessageBox.warning(self, "Error", "Please enter REST API Key first.")
            return
            
        import webbrowser
        # Using default localhost redirect uri
        url = f"https://kauth.kakao.com/oauth/authorize?client_id={app_key}&redirect_uri=https://localhost:3000&response_type=code"
        webbrowser.open(url)
        QMessageBox.information(self, "Guide", 
            "1. Login in the opened browser.\n"
            "2. When redirected to localhost (page may fail to load), copy the 'code' parameter from the URL bar.\n"
            "3. Paste it into the 'Auth Code' field."
        )

    def exchange_token(self):
        """Exchange Auth Code for Tokens."""
        app_key = self.kakao_app_key.text().strip()
        code = self.auth_code.text().strip()
        
        if not app_key or not code:
            QMessageBox.warning(self, "Error", "REST API Key and Auth Code are required.")
            return
            
        import requests
        url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": app_key,
            "redirect_uri": "https://localhost:3000",
            "code": code
        }
        
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                tokens = response.json()
                self.access_token.setText(tokens.get("access_token"))
                if "refresh_token" in tokens:
                    self.refresh_token.setText(tokens.get("refresh_token"))
                QMessageBox.information(self, "Success", "Tokens generated successfully!")
            else:
                QMessageBox.critical(self, "Error", f"Failed to get tokens: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection Error: {e}")

    def send_test_message(self):
        """Send a test message using current token."""
        token = self.access_token.text().strip()
        if not token:
            QMessageBox.warning(self, "Error", "No Access Token available.")
            return
            
        import requests
        url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "template_object": '{"object_type":"text","text":"🔔 [Test] Kakao Notification Test Message","link":{"web_url":"https://www.kakao.com","mobile_web_url":"https://www.kakao.com"}}'
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Test message sent!")
            else:
                QMessageBox.warning(self, "Failed", f"Failed to send: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection Error: {e}")

    def save_settings(self):
        config.set("risk.max_loss_pct", self.max_loss.value())
        config.set("risk.max_position_pct", self.max_pos.value())
        
        # Save Kakao Keys to SecureStorage
        secure_storage.save("kakao_app_key", self.kakao_app_key.text().strip())
        secure_storage.save("kakao_access_token", self.access_token.text().strip())
        secure_storage.save("kakao_refresh_token", self.refresh_token.text().strip())
            
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
        
        self.btn_vacuum = QPushButton("DB 최적화 (Vacuum)")
        layout.addRow("", self.btn_vacuum)
        
        layout.addRow(QLabel(""))
        self.btn_reset = QPushButton("공장 초기화")
        self.btn_reset.setStyleSheet("background-color: #c0392b; color: white;")
        layout.addRow("위험 구역:", self.btn_reset)

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
