"""
마켓 리스트 위젯 - 실시간 데이터 연동
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QPushButton, QHBoxLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor


class MarketListWidget(QWidget):
    """마켓 리스트 (좌측 사이드바)"""
    
    # 티커 선택 시그널
    ticker_selected = pyqtSignal(str)  # 선택된 티커 전달
    
    def __init__(self):
        super().__init__()
        self.setFixedWidth(280)
        self.current_data = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 검색 바
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 코인 검색...")
        self.search.setStyleSheet("""
            QLineEdit {
                background-color: #2b3139;
                border: none;
                border-bottom: 1px solid #474d57;
                padding: 12px;
                font-size: 13px;
            }
        """)
        self.search.textChanged.connect(self.filter_markets)
        layout.addWidget(self.search)
        
        # 필터 버튼들
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(5, 5, 5, 5)
        filter_layout.setSpacing(5)
        
        for text in ['전체', 'KRW', '관심']:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2b3139;
                    border: 1px solid #474d57;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #3a3f47;
                }
            """)
            filter_layout.addWidget(btn)
        
        layout.addLayout(filter_layout)
        
        # 마켓 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['★', '코인', '현재가', '변동률'])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 30)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 70)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        
        # 클릭 이벤트 연결
        self.table.cellClicked.connect(self.on_market_clicked)
        
        layout.addWidget(self.table)
        
    def update_market_data(self, market_data):
        """실시간 마켓 데이터 업데이트"""
        self.current_data = market_data
        self.display_markets(market_data)
        
    def display_markets(self, market_data):
        """마켓 데이터 표시"""
        self.table.setRowCount(len(market_data))
        
        for i, data in enumerate(market_data):
            ticker = data['ticker']
            symbol = ticker.split('-')[1] if '-' in ticker else ticker
            current_price = data.get('current_price', 0)
            change_percent = data.get('change_percent', 0)
            
            # 관심 아이콘
            star_item = QTableWidgetItem('☆')
            star_item.setTextAlignment(Qt.AlignCenter)
            star_item.setData(Qt.UserRole, ticker)  # 티커 저장
            self.table.setItem(i, 0, star_item)
            
            # 코인명
            name_item = QTableWidgetItem(f"{symbol}")
            name_item.setForeground(QColor('#ffffff'))
            name_item.setData(Qt.UserRole, ticker)
            self.table.setItem(i, 1, name_item)
            
            # 현재가 포맷팅
            if current_price:
                if current_price >= 1000:
                    price_str = f"{current_price:,.0f}"
                elif current_price >= 1:
                    price_str = f"{current_price:,.2f}"
                else:
                    price_str = f"{current_price:.4f}"
            else:
                price_str = "-"
            
            price_item = QTableWidgetItem(price_str)
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            price_item.setData(Qt.UserRole, ticker)
            self.table.setItem(i, 2, price_item)
            
            # 변동률
            change_str = f"{change_percent:+.2f}%"
            change_item = QTableWidgetItem(change_str)
            change_item.setTextAlignment(Qt.AlignCenter)
            change_item.setData(Qt.UserRole, ticker)
            
            if change_percent > 0:
                change_item.setForeground(QColor('#f6465d'))
                change_item.setBackground(QColor('#2a1617'))
            elif change_percent < 0:
                change_item.setForeground(QColor('#1fc7d4'))
                change_item.setBackground(QColor('#162328'))
            else:
                change_item.setForeground(QColor('#b7bdc6'))
                
            self.table.setItem(i, 3, change_item)
            
            # 행 높이
            self.table.setRowHeight(i, 55)
    
    def on_market_clicked(self, row, column):
        """마켓 클릭 이벤트"""
        item = self.table.item(row, 1)  # 코인명 컬럼
        if item:
            ticker = item.data(Qt.UserRole)
            if ticker:
                print(f"선택된 티커: {ticker}")
                self.ticker_selected.emit(ticker)
    
    def filter_markets(self, text):
        """검색 필터"""
        for i in range(self.table.rowCount()):
            item = self.table.item(i, 1)
            if item:
                symbol = item.text()
                if text.upper() in symbol.upper():
                    self.table.setRowHidden(i, False)
                else:
                    self.table.setRowHidden(i, True)
