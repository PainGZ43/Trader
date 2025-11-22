"""
헤더 바 위젯
"""
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton, 
                             QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class HeaderBar(QWidget):
    """상단 헤더 바"""
    
    def __init__(self):
        super().__init__()
        self.setFixedHeight(70)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e2329;
                border-bottom: 1px solid #2b3139;
            }
        """)
        
        # 상태 추적 딕셔너리
        self.statuses = {
            'api': False,
            'database': False,
            'trading': False
        }
        
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # 로고
        logo = QLabel("🚀 Upbit Auto Trader")
        logo_font = QFont()
        logo_font.setPointSize(18)
        logo_font.setBold(True)
        logo.setFont(logo_font)
        logo.setStyleSheet("color: #fcd535;")
        layout.addWidget(logo)
        
        # 스페이서
        layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # 시스템 상태
        self.status_label = QLabel("● 시스템 준비 중")
        self.status_label.setStyleSheet("color: #858585; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # 자동매매 토글
        self.trading_btn = QPushButton("자동매매: OFF")
        self.trading_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b3139;
                color: #b7bdc6;
                border: 1px solid #474d57;
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3f47;
            }
        """)
        self.trading_btn.clicked.connect(self.toggle_trading)
        self.trading_on = False
        layout.addWidget(self.trading_btn)
        
        # 계정 정보
        account_label = QLabel("총 자산: ₩10,000,000")
        account_label.setStyleSheet("color: #1fc7d4; font-weight: bold; font-size: 14px;")
        layout.addWidget(account_label)
        
        # 설정 버튼
        settings_btn = QPushButton("⚙️")
        settings_btn.setFixedSize(40, 40)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b3139;
                border-radius: 20px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #3a3f47;
            }
        """)
        layout.addWidget(settings_btn)
        
    def toggle_trading(self):
        """자동매매 토글"""
        self.trading_on = not self.trading_on
        if self.trading_on:
            self.trading_btn.setText("자동매매: ON")
            self.trading_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0ecb81;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #10d98f;
                }
            """)
        else:
            self.trading_btn.setText("자동매매: OFF")
            self.trading_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2b3139;
                    color: #b7bdc6;
                    border: 1px solid #474d57;
                    border-radius: 4px;
                    padding: 8px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #3a3f47;
                }
            """)
    
    def update_status(self, status_type, status_value):
        """
        시스템 상태 업데이트
        
        Args:
            status_type (str): 상태 타입 ('api', 'database', 'trading')
            status_value (bool): 상태 값
        """
        if status_type in self.statuses:
            self.statuses[status_type] = status_value
        
        # 상태 메시지 생성
        status_parts = []
        
        # API 상태
        if self.statuses['api']:
            status_parts.append("API 연결됨")
        else:
            status_parts.append("API 미설정")
        
        # DB 상태
        if self.statuses['database']:
            status_parts.append("DB 연결됨")
        else:
            status_parts.append("DB 연결 실패")
        
        # Trading 상태
        if self.statuses['trading']:
            status_parts.append("거래 중")
        
        # 메시지 조합
        status_message = " | ".join(status_parts)
        
        # 색상 결정 (모든 핵심 시스템이 정상이면 녹색)
        if self.statuses['api'] and self.statuses['database']:
            if self.statuses['trading']:
                color = "#0ecb81"  # 녹색 (거래 중)
                status_message = "● " + status_message
            else:
                color = "#1fc7d4"  # 청록색 (준비 완료)
                status_message = "● " + status_message
        else:
            color = "#f6465d"  # 빨간색 (문제 있음)
            status_message = "● " + status_message
        
        self.status_label.setText(status_message)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

