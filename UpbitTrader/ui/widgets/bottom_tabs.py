"""
하단 탭 위젯
"""
from PyQt5.QtWidgets import (QWidget, QTabWidget, QVBoxLayout, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLabel)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class BottomTabsWidget(QWidget):
    """하단 탭 위젯"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 탭 위젯
        tabs = QTabWidget()
        tabs.addTab(self.create_holdings_tab(), "보유 자산")
        tabs.addTab(self.create_open_orders_tab(), "미체결")
        tabs.addTab(self.create_order_history_tab(), "체결 내역")
        tabs.addTab(self.create_trade_history_tab(), "거래 내역")
        tabs.addTab(self.create_ai_analysis_tab(), "AI 분석")
        
        layout.addWidget(tabs)
        
    def create_holdings_tab(self):
        """보유 자산 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            '코인', '보유 수량', '평균 매수가', '현재가', '평가 금액', '평가 손익', '수익률'
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        
        # 샘플 데이터
        holdings = [
            ('BTC', '0.05', '120,000,000', '125,458,000', '6,272,900', '+272,900', '+4.59%'),
            ('ETH', '2.5', '4,200,000', '4,567,000', '11,417,500', '+917,500', '+8.73%'),
        ]
        
        table.setRowCount(len(holdings))
        for i, row_data in enumerate(holdings):
            for j, text in enumerate(row_data):
                item = QTableWidgetItem(text)
                if j == 6:  # 수익률
                    if '+' in text:
                        item.setForeground(QColor('#f6465d'))
                    else:
                        item.setForeground(QColor('#1fc7d4'))
                table.setItem(i, j, item)
        
        layout.addWidget(table)
        
        # 요약
        summary = QLabel("총 평가 금액: ₩17,690,400 | 총 평가 손익: +₩1,190,400 (+7.21%)")
        summary.setStyleSheet("""
            background-color: #2b3139;
            color: #f6465d;
            padding: 10px;
            font-weight: bold;
        """)
        layout.addWidget(summary)
        
        return widget
        
    def create_open_orders_tab(self):
        """미체결 주문 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            '시간', '코인', '타입', '가격', '수량', '미체결', '상태'
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setRowCount(0)
        
        layout.addWidget(table)
        
        # 빈 상태 메시지
        empty_msg = QLabel("미체결 주문이 없습니다")
        empty_msg.setAlignment(Qt.AlignCenter)
        empty_msg.setStyleSheet("color: #5e6673; padding: 50px;")
        layout.addWidget(empty_msg)
        
        return widget
        
    def create_order_history_tab(self):
        """체결 내역 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            '체결 시간', '코인', '타입', '체결가', '체결량', '체결 금액', '수수료'
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        
        # 샘플 데이터
        orders = [
            ('15:23:45', 'BTC', '매수', '125,000,000', '0.05', '6,250,000', '3,125'),
            ('14:15:32', 'ETH', '매수', '4,200,000', '2.5', '10,500,000', '5,250'),
        ]
        
        table.setRowCount(len(orders))
        for i, row_data in enumerate(orders):
            for j, text in enumerate(row_data):
                item = QTableWidgetItem(text)
                if j == 2:  # 타입
                    if text == '매수':
                        item.setForeground(QColor('#f6465d'))
                    else:
                        item.setForeground(QColor('#1fc7d4'))
                table.setItem(i, j, item)
        
        layout.addWidget(table)
        
        return widget
        
    def create_trade_history_tab(self):
        """거래 내역 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            '코인', '진입 시간', '청산 시간', '진입가', '청산가', '수익  ', '수익률', '전략'
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setRowCount(0)
        
        layout.addWidget(table)
        
        return widget
        
    def create_ai_analysis_tab(self):
        """AI 분석 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # AI 성과 정보
        info = QLabel("""
        <h2 style='color: #fcd535;'>🤖 AI 모델 성과</h2>
        <p style='font-size: 14px;'>
        <b>예측 정확도:</b> <span style='color: #0ecb81;'>85.3%</span><br>
        <b>방향 정확도:</b> <span style='color: #0ecb81;'>78.9%</span><br>
        <b>평균 신뢰도:</b> <span style='color: #1fc7d4;'>82.1%</span><br>
        <b>마지막 학습:</b> 2025-11-22 02:00<br>
        <b>다음 재학습:</b> 2025-11-29 02:00
        </p>
        """)
        info.setStyleSheet("background-color: #2b3139; padding: 20px; border-radius: 8px;")
        layout.addWidget(info)
        
        layout.addStretch()
        
        return widget
