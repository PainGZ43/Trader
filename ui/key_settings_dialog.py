import asyncio
from qasync import asyncSlot
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QComboBox, QDateEdit, QGroupBox, QFormLayout,
                             QAbstractItemView, QRadioButton, QWidget, QButtonGroup, QSpinBox, QCheckBox)
from PyQt6.QtCore import Qt, QDate, QTimer
from data.key_manager import key_manager

class AddKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API 키 등록")
        self.setFixedSize(400, 350)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Investment Type Selection
        type_group_box = QGroupBox("투자 구분")
        type_layout = QHBoxLayout()
        
        self.radio_real = QRadioButton("실전투자")
        self.radio_mock = QRadioButton("모의투자")
        self.radio_virtual = QRadioButton("가상투자")
        self.radio_mock.setChecked(True) # Default
        
        self.type_group = QButtonGroup()
        self.type_group.addButton(self.radio_real, 1)
        self.type_group.addButton(self.radio_mock, 2)
        self.type_group.addButton(self.radio_virtual, 3)
        
        self.type_group.buttonToggled.connect(self.update_ui_state)
        
        type_layout.addWidget(self.radio_real)
        type_layout.addWidget(self.radio_mock)
        type_layout.addWidget(self.radio_virtual)
        type_group_box.setLayout(type_layout)
        self.layout.addWidget(type_group_box)
        
        # Form Layout
        self.form_layout = QFormLayout()
        
        # Fields
        self.owner_input = QLineEdit()
        self.owner_input.setPlaceholderText("예: 내 계좌 1")
        
        self.account_input = QLineEdit()
        self.account_input.setPlaceholderText("계좌번호 (하이픈 없이 입력)")
        
        self.app_key_input = QLineEdit()
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Labels for visibility control
        self.lbl_owner = QLabel("계좌주 (별칭):")
        self.lbl_account = QLabel("계좌번호:")
        self.lbl_app = QLabel("App Key:")
        self.lbl_secret = QLabel("Secret Key:")
        
        self.form_layout.addRow(self.lbl_owner, self.owner_input)
        self.form_layout.addRow(self.lbl_account, self.account_input)
        self.form_layout.addRow(self.lbl_app, self.app_key_input)
        self.form_layout.addRow(self.lbl_secret, self.secret_key_input)
        
        self.layout.addLayout(self.form_layout)
        
        btn_layout = QHBoxLayout()
        self.verify_btn = QPushButton("검증 및 등록")
        self.verify_btn.clicked.connect(self.verify_and_add)
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.verify_btn)
        btn_layout.addWidget(self.cancel_btn)
        self.layout.addLayout(btn_layout)
        
        self.detected_type = "MOCK"
        self.detected_expiry = ""
        
        self.update_ui_state()

    def update_ui_state(self):
        is_virtual = self.radio_virtual.isChecked()
        
        # Show/Hide fields
        self.lbl_account.setVisible(not is_virtual)
        self.account_input.setVisible(not is_virtual)
        self.lbl_app.setVisible(not is_virtual)
        self.app_key_input.setVisible(not is_virtual)
        self.lbl_secret.setVisible(not is_virtual)
        self.secret_key_input.setVisible(not is_virtual)
        
        if is_virtual:
            self.verify_btn.setText("등록")
            self.owner_input.setPlaceholderText("예: 가상계좌 1")
        else:
            self.verify_btn.setText("검증 및 등록")
            self.owner_input.setPlaceholderText("예: 모의투자 1")

    @asyncSlot()
    async def verify_and_add(self):
        owner = self.owner_input.text().strip()
        
        if not owner:
            QMessageBox.warning(self, "입력 오류", "계좌주(별칭)을 입력해주세요.")
            return

        is_virtual = self.radio_virtual.isChecked()
        
        if is_virtual:
            # Virtual: Just add with empty credentials
            success = await key_manager.add_key(owner, "VIRTUAL", "", "", "", "")
            if success:
                # QMessageBox.information(self, "성공", "가상투자 키가 등록되었습니다.")
                self.accept()
            else:
                QMessageBox.warning(self, "실패", "키 등록에 실패했습니다.")
            return

        # Real/Mock: Full validation
        account = self.account_input.text().strip()
        app_key = self.app_key_input.text().strip()
        secret = self.secret_key_input.text().strip()
        
        if not all([account, app_key, secret]):
            QMessageBox.warning(self, "입력 오류", "모든 필드(계좌번호, App Key, Secret Key)를 입력해주세요.")
            return

        self.verify_btn.setEnabled(False)
        self.verify_btn.setText("검증 중...")
        
        try:
            # Probe Key Info (Auto-detect Type & Expiry)
            info = await key_manager.probe_key_info(app_key, secret)
            
            if info["valid"]:
                self.detected_type = info["type"]
                self.detected_expiry = info["expiry_date"]
                
                # Check if detected type matches selection (Optional warning, but we can just use detected)
                selected_type = "REAL" if self.radio_real.isChecked() else "MOCK"
                if self.detected_type != selected_type:
                     QMessageBox.information(self, "알림", f"선택한 타입({selected_type})과 감지된 타입({self.detected_type})이 다릅니다.\n감지된 타입으로 등록합니다.")
                
                # Finalize Add
                success = await key_manager.add_key(owner, self.detected_type, account, app_key, secret, self.detected_expiry)
                
                if success:
                    # QMessageBox.information(self, "성공", f"키가 등록되었습니다.\n타입: {self.detected_type}\n만료일: {self.detected_expiry}")
                    self.accept()
                else:
                    QMessageBox.warning(self, "실패", "키 등록에 실패했습니다.\n(중복된 App Key이거나 최대 개수 초과)")
                    self.verify_btn.setEnabled(True)
                    self.verify_btn.setText("검증 및 등록")
            else:
                QMessageBox.critical(self, "검증 실패", "유효하지 않은 키입니다.\nApp Key와 Secret Key를 확인해주세요.")
                self.verify_btn.setEnabled(True)
                self.verify_btn.setText("검증 및 등록")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"작업 중 오류 발생: {e}")
            self.verify_btn.setEnabled(True)
            self.verify_btn.setText("검증 및 등록")

class KeySettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API 키 관리")
        self.resize(700, 400)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["사용", "상태", "계좌주 (수정가능)", "구분", "계좌번호", "만료일"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Allow editing only specific items, but QTableWidget is all or nothing with triggers usually.
        # We set DoubleClicked trigger, but disable flags for non-editable items.
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        
        # Connect change signal
        self.table.itemChanged.connect(self.on_item_changed)
        
        # Resize "Use" and "Status" columns to be smaller
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        
        self.layout.addWidget(self.table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("키 등록")
        self.add_btn.clicked.connect(self.open_add_dialog)
        
        self.refresh_btn = QPushButton("새로고침 (정보 갱신)")
        self.refresh_btn.clicked.connect(self.check_all_validity)
        
        self.delete_btn = QPushButton("삭제")
        self.delete_btn.clicked.connect(self.delete_key)
        
        self.close_btn = QPushButton("닫기")
        self.close_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        
        # Global Settings
        settings_group = QGroupBox("전역 설정")
        settings_layout = QHBoxLayout()
        
        # 1. Expiry Alert
        self.alert_days_spin = QSpinBox()
        self.alert_days_spin.setRange(1, 365)
        self.alert_days_spin.setValue(key_manager.get_expiry_alert_days())
        self.alert_days_spin.setSuffix(" 일 전 알림")
        self.alert_days_spin.valueChanged.connect(lambda v: key_manager.set_expiry_alert_days(v))
        
        settings_layout.addWidget(QLabel("만료 알림:"))
        settings_layout.addWidget(self.alert_days_spin)
        
        # 2. Auto Login
        self.auto_login_check = QCheckBox("프로그램 시작 시 활성 키로 자동 로그인")
        self.auto_login_check.setChecked(key_manager.is_auto_login_enabled())
        self.auto_login_check.toggled.connect(lambda c: key_manager.set_auto_login_enabled(c))
        
        settings_layout.addSpacing(20)
        settings_layout.addWidget(self.auto_login_check)
        settings_layout.addStretch()
        
        settings_group.setLayout(settings_layout)
        self.layout.addWidget(settings_group)

        self.layout.addLayout(btn_layout)
        
        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)
        
        self.radio_group = None 
        self.is_loading = False # Flag to prevent signal recursion
        self.load_keys()
        
        # Auto-check validity on open
        QTimer.singleShot(100, self.check_all_validity)

    def load_keys(self):
        self.is_loading = True
        self.table.setRowCount(0)
        keys = key_manager.get_keys()
        
        for row, k in enumerate(keys):
            self.table.insertRow(row)
            
            # 1. Active Radio Button
            radio_widget = QWidget()
            radio_layout = QHBoxLayout(radio_widget)
            radio_layout.setContentsMargins(0, 0, 0, 0)
            radio_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            radio = QRadioButton()
            if k["is_active"]:
                radio.setChecked(True)
            
            radio.setProperty("uuid", k["uuid"])
            radio.clicked.connect(lambda checked, r=radio: self.on_radio_clicked(r))
            
            radio_layout.addWidget(radio)
            self.table.setCellWidget(row, 0, radio_widget)
            
            # 2. Validity Status (Use Cached)
            status_text = "❓"
            status_color = Qt.GlobalColor.black
            
            if k.get("is_valid") is True:
                status_text = "✅ 유효"
                status_color = Qt.GlobalColor.green
            elif k.get("is_valid") is False:
                status_text = "❌ 무효"
                status_color = Qt.GlobalColor.red
                
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setForeground(status_color)
            status_item.setFlags(status_item.flags() ^ Qt.ItemFlag.ItemIsEditable) # Not editable
            self.table.setItem(row, 1, status_item)
            
            # 3. Owner (Editable)
            owner_item = QTableWidgetItem(k["owner"])
            owner_item.setFlags(owner_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, owner_item)
            
            # 4. Type (Not Editable)
            type_item = QTableWidgetItem(k["type"])
            type_item.setFlags(type_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, type_item)
            
            # 5. Account No (Not Editable)
            acc_item = QTableWidgetItem(k["masked_account_no"])
            acc_item.setFlags(acc_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, acc_item)
            
            # 6. Expiry (Not Editable)
            expiry_item = QTableWidgetItem(k["expiry_date"])
            expiry_item.setFlags(expiry_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, expiry_item)
            
            # Store UUID in a hidden item for other operations
            self.table.setItem(row, 0, QTableWidgetItem("")) 
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, k["uuid"])
            
        self.is_loading = False

    def on_item_changed(self, item):
        if self.is_loading:
            return
            
        # Only handle Owner column (index 2)
        if item.column() == 2:
            row = item.row()
            uuid = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            new_owner = item.text().strip()
            
            if not new_owner:
                QMessageBox.warning(self, "오류", "계좌주(별칭)은 비워둘 수 없습니다.")
                self.load_keys() # Revert
                return
                
            if key_manager.update_key_owner(uuid, new_owner):
                # Success feedback (optional, maybe status bar)
                pass
            else:
                QMessageBox.warning(self, "오류", "계좌주 수정에 실패했습니다.")
                self.load_keys() # Revert

    def open_add_dialog(self):
        try:
            dialog = AddKeyDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_keys()
                # Auto-check validity for the new key (or all)
                self.check_all_validity()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"키 등록 창을 여는 중 오류가 발생했습니다:\n{e}")

    def on_radio_clicked(self, radio):
        uuid = radio.property("uuid")
        if key_manager.set_active_key(uuid):
            # Reload to update UI (uncheck others)
            self.load_keys()
            QMessageBox.information(self, "설정 완료", "활성 키가 변경되었습니다.")

    @asyncSlot()
    async def check_all_validity(self):
        self.refresh_btn.setEnabled(False)
        self.status_label.setText("서버와 통신하여 키 정보를 갱신 중입니다...")
        
        rows = self.table.rowCount()
        
        for row in range(rows):
            uuid = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            
            # Verify and update metadata (and cache)
            await key_manager.verify_key_by_uuid(uuid)
        
        # Reload keys to reflect updated cache and expiry dates
        self.load_keys()
        
        self.status_label.setText("갱신 완료")
        self.refresh_btn.setEnabled(True)
        # Clear status after 3 seconds
        QTimer.singleShot(3000, lambda: self.status_label.setText(""))

    def delete_key(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "선택", "삭제할 키를 선택해주세요.")
            return
            
        uuid = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        confirm = QMessageBox.question(self, "삭제 확인", "정말 삭제하시겠습니까?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            if key_manager.delete_key(uuid):
                self.load_keys()
