"""
호가 및 주문 위젯
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QLineEdit, QSlider, QTabWidget, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class OrderBookWidget(QWidget):
    """호가 및 주문 위젯"""
    
    def __init__(self):
        super().__init__()
        self.setFixedWidth(320)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 탭 위젯 (호가 / 주문)
        tabs = QTabWidget()
        tabs.addTab(self.create_orderbook(), "호가")
        tabs.addTab(self.create_order_panel(), "주문")
        
        layout.addWidget(tabs)
        
    def create_orderbook(self):
        """호가창"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 호가 테이블
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(['가격', '수량', '총액'])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        
        # 샘플호가 데이터
        asks = [  # 매도호가
            ('125,470,000', '0.152', '19M'),
            ('125,465,000', '0.234', '29M'),
            ('125,460,000', '0.387', '48M'),
            ('125,458,000', '0.521', '65M'),
            ('125,455,000', '0.698', '87M'),
        ]
        
        bids = [  # 매수호가
            ('125,450,000', '0.845', '106M'),
            ('125,445,000', '0.623', '78M'),
            ('125,440,000', '0.456', '57M'),
            ('125,435,000', '0.289', '36M'),
            ('125,430,000', '0.134', '17M'),
        ]
        
        table.setRowCount(len(asks) + 1 + len(bids))
        
        # 매도호가 (빨간색)
        for i, (price, qty, total) in enumerate(asks):
            for j, text in enumerate([price, qty, total]):
                item = QTableWidgetItem(text)
                item.setBackground(QColor('#2a1617'))
                item.setForeground(QColor('#f6465d'))
                if j == 0:
                    item.setForeground(QColor('#ffffff'))
                table.setItem(i, j, item)
        
        # 현재가
        current_row = len(asks)
        for j, text in enumerate(['125,458,000', '---', '---']):
            item = QTableWidgetItem(text)
            item.setBackground(QColor('#fcd535'))
            item.setForeground(QColor('#1e2329'))
            if j == 0:
                font = item.font()
                font.setBold(True)
                font.setPointSize(12)
                item.setFont(font)
            table.setItem(current_row, j, item)
        
        # 매수호가 (초록색)
        for i, (price, qty, total) in enumerate(bids):
            row = current_row + 1 + i
            for j, text in enumerate([price, qty, total]):
                item = QTableWidgetItem(text)
                item.setBackground(QColor('#162328'))
                item.setForeground(QColor('#1fc7d4'))
                if j == 0:
                    item.setForeground(QColor('#ffffff'))
                table.setItem(row, j, item)
        
        layout.addWidget(table)
        
        return widget
        
    def create_order_panel(self):
        """주문 패널"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 매수/매도 탭
        order_tabs = QTabWidget()
        order_tabs.addTab(self.create_buy_form(), "매수")
        order_tabs.addTab(self.create_sell_form(), "매도")
        
        layout.addWidget(order_tabs)
        
        return widget
        
    def create_buy_form(self):
        """매수 폼"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        
        # 주문 가격
        layout.addWidget(QLabel("주문 가격"))
        price_input = QLineEdit("125,458,000")
        price_input.setStyleSheet("padding: 10px;")
        layout.addWidget(price_input)
        
        # 주문 수량
        layout.addWidget(QLabel("주문 수량"))
        qty_input = QLineEdit("0.001")
        qty_input.setStyleSheet("padding: 10px;")
        layout.addWidget(qty_input)
        
        # 수량 슬라이더
        slider_layout = QHBoxLayout()
        for pct in ['10%', '25%', '50%', '100%']:
            btn = QPushButton(pct)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2b3139;
                    border: 1px solid #474d57;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #3a3f47;
                }
            """)
            slider_layout.addWidget(btn)
        layout.addLayout(slider_layout)
        
        # 주문 총액
        total_label = QLabel("주문 총액: ₩125,458")
        total_label.setStyleSheet("color: #1fc7d4; font-weight: bold; margin-top: 10px;")
        layout.addWidget(total_label)
        
        # 매수 가능
        available = QLabel("매수 가능: ₩10,000,000")
        available.setStyleSheet("color: #b7bdc6; font-size: 12px;")
        layout.addWidget(available)
        
        layout.addStretch()
        
        # 매수 버튼
        buy_btn = QPushButton("매수")
        buy_btn.setProperty("buttonType", "buy")
        buy_btn.setMinimumHeight(50)
        buy_btn.setStyleSheet("""
            QPushButton {
                background-color: #0ecb81;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #10d98f;
            }
        """)
        layout.addWidget(buy_btn)
        
        return widget
        
    def create_sell_form(self):
        """매도 폼"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        
        # 주문 가격
        layout.addWidget(QLabel("주문 가격"))
        price_input = QLineEdit("125,458,000")
        price_input.setStyleSheet("padding: 10px;")
        layout.addWidget(price_input)
        
        # 주문 수량
        layout.addWidget(QLabel("주문 수량"))
        qty_input = QLineEdit("0.001")
        qty_input.setStyleSheet("padding: 10px;")
        layout.addWidget(qty_input)
        
        # 수량 슬라이더
        slider_layout = QHBoxLayout()
        for pct in ['10%', '25%', '50%', '100%']:
            btn = QPushButton(pct)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2b3139;
                    border: 1px solid #474d57;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #3a3f47;
                }
            """)
            slider_layout.addWidget(btn)
        layout.addLayout(slider_layout)
        
        # 주문 총액
        total_label = QLabel("주문 총액: ₩125,458")
        total_label.setStyleSheet("color: #f6465d; font-weight: bold; margin-top: 10px;")
        layout.addWidget(total_label)
        
        # 매도 가능
        available = QLabel("매도 가능: 0.0 BTC")
        available.setStyleSheet("color: #b7bdc6; font-size: 12px;")
        layout.addWidget(available)
        
        layout.addStretch()
        
        # 매도 버튼
        sell_btn = QPushButton("매도")
        sell_btn.setProperty("buttonType", "sell")
        sell_btn.setMinimumHeight(50)
        sell_btn.setStyleSheet("""
            QPushButton {
                background-color: #f6465d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff526f;
            }
        """)
        layout.addWidget(sell_btn)
        
        return widget
