import asyncio
from qasync import asyncSlot
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QComboBox, QDateEdit, QGroupBox, QFormLayout,
                             QAbstractItemView, QRadioButton, QWidget)
from PyQt6.QtCore import Qt, QDate, QTimer
from data.key_manager import key_manager

class AddKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API 키 등록")
        self.setFixedSize(400, 350)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Form Layout
        form_layout = QFormLayout()
        
        # Fields
        self.owner_input = QLineEdit()
        self.owner_input.setPlaceholderText("예: 모의투자1")
        
        self.app_key_input = QLineEdit()
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Auto-detected fields (Read-only initially)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["MOCK", "REAL"])
        self.type_combo.setEnabled(False)
        
        self.account_input = QLineEdit()
        self.account_input.setPlaceholderText("검증 후 자동 입력 또는 수동 입력")
        self.account_input.setEnabled(False) # Enable after verification if needed
        
        self.expiry_input = QDateEdit()
        self.expiry_input.setDate(QDate.currentDate().addYears(1))
        self.expiry_input.setCalendarPopup(True)
        self.expiry_input.setEnabled(False)
        
        form_layout.addRow("계좌주 (별칭):", self.owner_input)
        form_layout.addRow("App Key:", self.app_key_input)
        form_layout.addRow("Secret Key:", self.secret_key_input)
        form_layout.addRow("구분 (자동):", self.type_combo)
        form_layout.addRow("계좌번호 (자동/수동):", self.account_input)
        form_layout.addRow("만료일 (자동):", self.expiry_input)
        
        self.layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        self.verify_btn = QPushButton("검증 및 정보 가져오기")
        self.verify_btn.clicked.connect(self.verify_and_add)
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.verify_btn)
        btn_layout.addWidget(self.cancel_btn)
        self.layout.addLayout(btn_layout)
        
        self.result_key = None
        self.is_verified = False

    @asyncSlot()
    async def verify_and_add(self):
        # If already verified, just add
        if self.is_verified:
            self._finalize_add()
            return

        owner = self.owner_input.text().strip()
        app_key = self.app_key_input.text().strip()
        secret = self.secret_key_input.text().strip()
        
        if not all([owner, app_key, secret]):
            QMessageBox.warning(self, "입력 오류", "계좌주(별칭), App Key, Secret Key를 모두 입력해주세요.")
            return

        self.verify_btn.setEnabled(False)
        self.verify_btn.setText("검증 중...")
        
        try:
            # Probe Key Info
            info = await key_manager.probe_key_info(app_key, secret)
            
            if info["valid"]:
                # Auto-fill fields
                self.type_combo.setCurrentText(info["type"])
                if info["expiry_date"]:
                    self.expiry_input.setDate(QDate.fromString(info["expiry_date"], "yyyy-MM-dd"))
                
                # Account No: If not fetched, enable input
                if info["account_no"]:
                    self.account_input.setText(info["account_no"])
                    self.account_input.setEnabled(False)
                else:
                    self.account_input.setEnabled(True)
                    self.account_input.setFocus()
                    QMessageBox.information(self, "검증 성공", f"키가 유효합니다 ({info['type']}).\n계좌번호를 입력해주세요.")
                
                self.is_verified = True
                self.verify_btn.setText("등록 완료")
                self.verify_btn.setEnabled(True)
                
                # Disable Key Inputs
                self.app_key_input.setEnabled(False)
                self.secret_key_input.setEnabled(False)
                self.type_combo.setEnabled(False)
                self.expiry_input.setEnabled(True) # Allow manual edit if needed
                
            else:
                QMessageBox.critical(self, "검증 실패", "유효하지 않은 키입니다.\nApp Key와 Secret Key를 확인해주세요.")
                self.verify_btn.setEnabled(True)
                self.verify_btn.setText("검증 및 정보 가져오기")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"검증 중 오류 발생: {e}")
            self.verify_btn.setEnabled(True)
            self.verify_btn.setText("검증 및 정보 가져오기")

    @asyncSlot()
    async def _finalize_add(self):
        owner = self.owner_input.text().strip()
        key_type = self.type_combo.currentText()
        account = self.account_input.text().strip()
        app_key = self.app_key_input.text().strip()
        secret = self.secret_key_input.text().strip()
        expiry = self.expiry_input.date().toString("yyyy-MM-dd")
        
        if not account:
            QMessageBox.warning(self, "입력 오류", "계좌번호를 입력해주세요.")
            return

        success = await key_manager.add_key(owner, key_type, account, app_key, secret, expiry)
        if success:
            QMessageBox.information(self, "성공", "키가 정상적으로 등록되었습니다.")
            self.accept()
        else:
            QMessageBox.warning(self, "실패", "키 등록에 실패했습니다.\n(중복된 App Key이거나 최대 개수 10개를 초과했습니다.)")

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
        self.table.setHorizontalHeaderLabels(["사용", "상태", "계좌주", "구분", "계좌번호", "만료일"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Resize "Use" and "Status" columns to be smaller
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        
        self.layout.addWidget(self.table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("키 등록")
        self.add_btn.clicked.connect(self.open_add_dialog)
        
        # Removed Check Validity Button as requested
        
        self.delete_btn = QPushButton("삭제")
        self.delete_btn.clicked.connect(self.delete_key)
        
        self.close_btn = QPushButton("닫기")
        self.close_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        
        self.layout.addLayout(btn_layout)
        
        self.radio_group = None 
        self.load_keys()
        
        # Auto-check validity on open
        QTimer.singleShot(100, self.check_all_validity)

    def load_keys(self):
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
            self.table.setItem(row, 1, status_item)
            
            # 3. Other Info
            self.table.setItem(row, 2, QTableWidgetItem(k["owner"]))
            self.table.setItem(row, 3, QTableWidgetItem(k["type"]))
            self.table.setItem(row, 4, QTableWidgetItem(k["masked_account_no"]))
            self.table.setItem(row, 5, QTableWidgetItem(k["expiry_date"]))
            
            # Store UUID in a hidden item for other operations
            self.table.setItem(row, 0, QTableWidgetItem("")) 
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, k["uuid"])

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
        rows = self.table.rowCount()
        has_updates = False
        
        for row in range(rows):
            uuid = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            
            # Verify and update metadata (and cache)
            await key_manager.verify_key_by_uuid(uuid)
        
        # Reload keys to reflect updated cache and expiry dates
        self.load_keys()

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
