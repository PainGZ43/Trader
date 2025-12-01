from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QPushButton, QHBoxLayout, QMessageBox
from ui.widgets.settings_tabs import AccountSettingsTab, StrategySettingsTab, RiskSettingsTab, SystemSettingsTab

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings & Management")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tab_account = AccountSettingsTab()
        self.tab_strategy = StrategySettingsTab()
        self.tab_risk = RiskSettingsTab()
        self.tab_system = SystemSettingsTab()
        
        self.tabs.addTab(self.tab_account, "Accounts & API")
        self.tabs.addTab(self.tab_strategy, "Strategy Tuning")
        self.tabs.addTab(self.tab_risk, "Risk & Notification")
        self.tabs.addTab(self.tab_system, "System Health")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save All")
        self.btn_save.clicked.connect(self.save_all)
        self.btn_cancel = QPushButton("Close")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
        
        # Style
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: white; }
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #333; color: #aaa; padding: 8px 12px; }
            QTabBar::tab:selected { background: #444; color: white; border-bottom: 2px solid #3498db; }
            QPushButton { padding: 8px 15px; background-color: #3498db; color: white; border: none; border-radius: 4px; }
            QPushButton:hover { background-color: #2980b9; }
            QLabel { color: white; }
            QLineEdit, QSpinBox, QComboBox { padding: 5px; background-color: #1e1e1e; color: white; border: 1px solid #555; }
        """)

    def save_all(self):
        # Save All Tabs
        self.tab_account.save_settings()
        self.tab_strategy.save_settings()
        self.tab_risk.save_settings()
        restart_required = self.tab_system.save_settings()
        
        if restart_required:
            from core.language import language_manager
            QMessageBox.information(
                self, 
                language_manager.get_text("msg_restart_title"), 
                language_manager.get_text("msg_restart_body")
            )
        else:
            QMessageBox.information(self, "Saved", "All settings have been saved successfully.")
            
        self.accept()
