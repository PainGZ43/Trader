"""
설정 다이얼로그
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QLabel, QLineEdit, QPushButton, QSpinBox,
                             QDoubleSpinBox, QCheckBox, QComboBox, QGroupBox,
                             QFormLayout, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os
from pathlib import Path


class SettingsDialog(QDialog):
    """설정 다이얼로그"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("설정")
        self.setMinimumSize(700, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e2329;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #2b3139;
                background-color: #1e2329;
            }
            QTabBar::tab {
                background-color: #2b3139;
                color: #b7bdc6;
                padding: 10px 20px;
                border: 1px solid #474d57;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #1e2329;
                color: #fcd535;
            }
            QLabel {
                color: #b7bdc6;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #2b3139;
                color: #ffffff;
                border: 1px solid #474d57;
                border-radius: 4px;
                padding: 8px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border: 1px solid #fcd535;
            }
            QPushButton {
                background-color: #2b3139;
                color: #ffffff;
                border: 1px solid #474d57;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3f47;
            }
            QPushButton#saveButton {
                background-color: #0ecb81;
                border: none;
            }
            QPushButton#saveButton:hover {
                background-color: #10d98f;
            }
            QGroupBox {
                border: 1px solid #474d57;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                color: #fcd535;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 탭 위젯
        tabs = QTabWidget()
        
        # API 설정 탭
        api_tab = self.create_api_tab()
        tabs.addTab(api_tab, "API 설정")
        
        # 거래 설정 탭
        trading_tab = self.create_trading_tab()
        tabs.addTab(trading_tab, "거래 설정")
        
        # 알림 설정 탭
        notification_tab = self.create_notification_tab()
        tabs.addTab(notification_tab, "알림 설정")
        
        # 일반 설정 탭
        general_tab = self.create_general_tab()
        tabs.addTab(general_tab, "일반 설정")
        
        layout.addWidget(tabs)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("저장")
        save_btn.setObjectName("saveButton")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
    def create_api_tab(self):
        """API 설정 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Upbit API 그룹
        api_group = QGroupBox("Upbit API 키")
        api_layout = QFormLayout()
        
        self.access_key_input = QLineEdit()
        self.access_key_input.setEchoMode(QLineEdit.Password)
        self.access_key_input.setPlaceholderText("Access Key를 입력하세요")
        api_layout.addRow("Access Key:", self.access_key_input)
        
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setEchoMode(QLineEdit.Password)
        self.secret_key_input.setPlaceholderText("Secret Key를 입력하세요")
        api_layout.addRow("Secret Key:", self.secret_key_input)
        
        # 키 표시 체크박스
        show_keys_cb = QCheckBox("API 키 표시")
        show_keys_cb.stateChanged.connect(self.toggle_key_visibility)
        api_layout.addRow("", show_keys_cb)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # 안내 메시지
        info_label = QLabel(
            "⚠️ API 키는 안전하게 보관하세요.\n"
            "• Upbit 웹사이트의 마이페이지 > Open API 관리에서 발급받으세요.\n"
            "• 자산 조회, 주문 권한이 필요합니다."
        )
        info_label.setStyleSheet("color: #f0b90b; padding: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        return widget
        
    def create_trading_tab(self):
        """거래 설정 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 포지션 관리 그룹
        position_group = QGroupBox("포지션 관리")
        position_layout = QFormLayout()
        
        self.max_position_input = QSpinBox()
        self.max_position_input.setRange(10000, 100000000)
        self.max_position_input.setSingleStep(100000)
        self.max_position_input.setSuffix(" 원")
        position_layout.addRow("최대 포지션 크기:", self.max_position_input)
        
        position_group.setLayout(position_layout)
        layout.addWidget(position_group)
        
        # 리스크 관리 그룹
        risk_group = QGroupBox("리스크 관리")
        risk_layout = QFormLayout()
        
        self.stop_loss_input = QDoubleSpinBox()
        self.stop_loss_input.setRange(0.1, 50.0)
        self.stop_loss_input.setSingleStep(0.5)
        self.stop_loss_input.setSuffix(" %")
        risk_layout.addRow("손절률:", self.stop_loss_input)
        
        self.take_profit_input = QDoubleSpinBox()
        self.take_profit_input.setRange(0.5, 500.0)
        self.take_profit_input.setSingleStep(1.0)
        self.take_profit_input.setSuffix(" %")
        risk_layout.addRow("익절률:", self.take_profit_input)
        
        self.max_daily_trades_input = QSpinBox()
        self.max_daily_trades_input.setRange(1, 1000)
        risk_layout.addRow("최대 일일 거래 횟수:", self.max_daily_trades_input)
        
        self.daily_loss_limit_input = QSpinBox()
        self.daily_loss_limit_input.setRange(10000, 10000000)
        self.daily_loss_limit_input.setSingleStep(10000)
        self.daily_loss_limit_input.setSuffix(" 원")
        risk_layout.addRow("일일 손실 한도:", self.daily_loss_limit_input)
        
        risk_group.setLayout(risk_layout)
        layout.addWidget(risk_group)
        
        layout.addStretch()
        return widget
        
    def create_notification_tab(self):
        """알림 설정 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 알림 활성화
        self.enable_notifications_cb = QCheckBox("알림 활성화")
        layout.addWidget(self.enable_notifications_cb)
        
        # 카카오톡 알림 그룹
        kakao_group = QGroupBox("카카오톡 알림")
        kakao_layout = QFormLayout()
        
        self.kakao_token_input = QLineEdit()
        self.kakao_token_input.setEchoMode(QLineEdit.Password)
        self.kakao_token_input.setPlaceholderText("카카오 API 토큰을 입력하세요")
        kakao_layout.addRow("API 토큰:", self.kakao_token_input)
        
        kakao_group.setLayout(kakao_layout)
        layout.addWidget(kakao_group)
        
        # 안내 메시지
        info_label = QLabel(
            "카카오톡 알림을 사용하려면:\n"
            "1. Kakao Developers에서 애플리케이션 생성\n"
            "2. REST API 키 발급\n"
            "3. 카카오톡 메시지 템플릿 등록"
        )
        info_label.setStyleSheet("color: #b7bdc6; padding: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        return widget
        
    def create_general_tab(self):
        """일반 설정 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 로그 설정 그룹
        log_group = QGroupBox("로그 설정")
        log_layout = QFormLayout()
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_layout.addRow("로그 레벨:", self.log_level_combo)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # AI 모델 설정 그룹
        ai_group = QGroupBox("AI 모델 설정")
        ai_layout = QFormLayout()
        
        self.retrain_interval_input = QSpinBox()
        self.retrain_interval_input.setRange(1, 30)
        self.retrain_interval_input.setSuffix(" 일")
        ai_layout.addRow("재학습 주기:", self.retrain_interval_input)
        
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)
        
        layout.addStretch()
        return widget
        
    def toggle_key_visibility(self, state):
        """API 키 표시/숨김 토글"""
        if state == Qt.Checked:
            self.access_key_input.setEchoMode(QLineEdit.Normal)
            self.secret_key_input.setEchoMode(QLineEdit.Normal)
            self.kakao_token_input.setEchoMode(QLineEdit.Normal)
        else:
            self.access_key_input.setEchoMode(QLineEdit.Password)
            self.secret_key_input.setEchoMode(QLineEdit.Password)
            self.kakao_token_input.setEchoMode(QLineEdit.Password)
    
    def load_settings(self):
        """현재 설정 로드"""
        # API 설정
        self.access_key_input.setText(self.config.UPBIT_ACCESS_KEY)
        self.secret_key_input.setText(self.config.UPBIT_SECRET_KEY)
        
        # 거래 설정
        self.max_position_input.setValue(int(self.config.MAX_POSITION_SIZE))
        self.stop_loss_input.setValue(self.config.STOP_LOSS_PERCENT)
        self.take_profit_input.setValue(self.config.TAKE_PROFIT_PERCENT)
        self.max_daily_trades_input.setValue(self.config.MAX_DAILY_TRADES)
        self.daily_loss_limit_input.setValue(int(self.config.DAILY_LOSS_LIMIT))
        
        # 알림 설정
        self.enable_notifications_cb.setChecked(self.config.ENABLE_NOTIFICATIONS)
        self.kakao_token_input.setText(self.config.KAKAO_TOKEN)
        
        # 일반 설정
        self.log_level_combo.setCurrentText(self.config.LOG_LEVEL)
        self.retrain_interval_input.setValue(self.config.RETRAIN_INTERVAL_DAYS)
    
    def save_settings(self):
        """설정 저장"""
        try:
            # .env 파일 경로
            env_path = self.config.PROJECT_ROOT / '.env'
            
            # 새로운 설정 값
            settings = {
                'UPBIT_ACCESS_KEY': self.access_key_input.text(),
                'UPBIT_SECRET_KEY': self.secret_key_input.text(),
                'MAX_POSITION_SIZE': str(self.max_position_input.value()),
                'STOP_LOSS_PERCENT': str(self.stop_loss_input.value()),
                'TAKE_PROFIT_PERCENT': str(self.take_profit_input.value()),
                'MAX_DAILY_TRADES': str(self.max_daily_trades_input.value()),
                'DAILY_LOSS_LIMIT': str(self.daily_loss_limit_input.value()),
                'ENABLE_NOTIFICATIONS': str(self.enable_notifications_cb.isChecked()),
                'KAKAO_TOKEN': self.kakao_token_input.text(),
                'LOG_LEVEL': self.log_level_combo.currentText(),
                'RETRAIN_INTERVAL_DAYS': str(self.retrain_interval_input.value()),
            }
            
            # 기존 .env 파일 읽기 또는 새로 생성
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 기존 설정 업데이트
                updated_lines = []
                updated_keys = set()
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key = line.split('=')[0].strip()
                        if key in settings:
                            updated_lines.append(f"{key}={settings[key]}\n")
                            updated_keys.add(key)
                        else:
                            updated_lines.append(line + '\n')
                    else:
                        updated_lines.append(line + '\n' if line else '\n')
                
                # 새로운 설정 추가
                for key, value in settings.items():
                    if key not in updated_keys:
                        updated_lines.append(f"{key}={value}\n")
                
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.writelines(updated_lines)
            else:
                # .env 파일이 없으면 새로 생성
                with open(env_path, 'w', encoding='utf-8') as f:
                    for key, value in settings.items():
                        f.write(f"{key}={value}\n")
            
            # Config 객체 업데이트
            self.config.UPBIT_ACCESS_KEY = settings['UPBIT_ACCESS_KEY']
            self.config.UPBIT_SECRET_KEY = settings['UPBIT_SECRET_KEY']
            self.config.MAX_POSITION_SIZE = float(settings['MAX_POSITION_SIZE'])
            self.config.STOP_LOSS_PERCENT = float(settings['STOP_LOSS_PERCENT'])
            self.config.TAKE_PROFIT_PERCENT = float(settings['TAKE_PROFIT_PERCENT'])
            self.config.MAX_DAILY_TRADES = int(settings['MAX_DAILY_TRADES'])
            self.config.DAILY_LOSS_LIMIT = float(settings['DAILY_LOSS_LIMIT'])
            self.config.ENABLE_NOTIFICATIONS = settings['ENABLE_NOTIFICATIONS'] == 'True'
            self.config.KAKAO_TOKEN = settings['KAKAO_TOKEN']
            self.config.LOG_LEVEL = settings['LOG_LEVEL']
            self.config.RETRAIN_INTERVAL_DAYS = int(settings['RETRAIN_INTERVAL_DAYS'])
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 저장 중 오류가 발생했습니다:\n{str(e)}")
