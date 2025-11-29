from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QHBoxLayout, QMessageBox, QFormLayout)
from core.secure_storage import secure_storage
from core.config import config

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(400, 300)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Form Layout for Inputs
        form_layout = QFormLayout()
        
        self.app_key_input = QLineEdit()
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.account_input = QLineEdit()
        
        form_layout.addRow("Kiwoom App Key:", self.app_key_input)
        form_layout.addRow("Kiwoom Secret Key:", self.secret_key_input)
        form_layout.addRow("Account No:", self.account_input)
        
        layout.addLayout(form_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # Style
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: white;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #1e1e1e;
                color: white;
            }
            QPushButton {
                padding: 8px 15px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

    def load_settings(self):
        # Load from SecureStorage first, then Config
        app_key = secure_storage.get("KIWOOM_APP_KEY") or config.get("KIWOOM_APP_KEY", "")
        secret_key = secure_storage.get("KIWOOM_SECRET_KEY") or config.get("KIWOOM_SECRET_KEY", "")
        account = secure_storage.get("ACCOUNT_NO") or config.get("ACCOUNT_NO", "")
        
        self.app_key_input.setText(app_key)
        self.secret_key_input.setText(secret_key)
        self.account_input.setText(account)

    def save_settings(self):
        app_key = self.app_key_input.text().strip()
        secret_key = self.secret_key_input.text().strip()
        account = self.account_input.text().strip()
        
        if not app_key or not secret_key:
            QMessageBox.warning(self, "Input Error", "App Key and Secret Key are required.")
            return

        try:
            secure_storage.save("KIWOOM_APP_KEY", app_key)
            secure_storage.save("KIWOOM_SECRET_KEY", secret_key)
            secure_storage.save("ACCOUNT_NO", account)
            
            # Update runtime config as well (optional but good for immediate effect if config is used)
            config.set("KIWOOM_APP_KEY", app_key)
            config.set("KIWOOM_SECRET_KEY", secret_key)
            config.set("ACCOUNT_NO", account)
            
            QMessageBox.information(self, "Success", "Settings saved successfully.\nPlease restart the application for changes to take full effect.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
