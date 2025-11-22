"""
Main Window - 메인 윈도우
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QSplitter, QTabWidget, QMenuBar, QMenu, QAction,
                             QStatusBar, QLabel, QPushButton, QToolBar)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon

from ui.widgets.header_bar import HeaderBar
from ui.widgets.market_list import MarketListWidget
from ui.widgets.chart_widget import ChartWidget
from ui.widgets.orderbook_widget import OrderBookWidget
from ui.widgets.bottom_tabs import BottomTabsWidget
from ui.styles import DARK_STYLESHEET


class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Upbit Auto Trader - AI 기반 자동매매")
        self.setGeometry(100, 100, 1600, 900)
        self.setMinimumSize(1366, 768)
        
        # 다크 테마 적용
        self.setStyleSheet(DARK_STYLESHEET)
        
        self.init_ui()
        self.create_menu_bar()
        self.create_status_bar()
        
    def init_ui(self):
        """UI 초기화"""
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 헤더 바 추가
        self.header_bar = HeaderBar()
        main_layout.addWidget(self.header_bar)
        
        # 수평 스플리터 (3분할: 마켓 리스트 | 차트 | 호가/주문)
        h_splitter = QSplitter(Qt.Horizontal)
        
        # 좌측: 마켓 리스트
        self.market_list = MarketListWidget()
        self.market_list.ticker_selected.connect(self.on_ticker_selected)  # 시그널 연결
        h_splitter.addWidget(self.market_list)
        
        # 중앙: 차트
        self.chart_widget = ChartWidget()
        h_splitter.addWidget(self.chart_widget)
        
        # 우측: 호가 및 주문
        self.orderbook_widget = OrderBookWidget()
        h_splitter.addWidget(self.orderbook_widget)
        
        # 스플리터 비율 설정 (280:1000:280)
        h_splitter.setSizes([280, 1000, 320])
        h_splitter.setHandleWidth(1)
        
        # 수직 스플리터 (상단: 메인영역 | 하단: 탭)
        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.addWidget(h_splitter)
        
        # 하단 탭
        self.bottom_tabs = BottomTabsWidget()
        v_splitter.addWidget(self.bottom_tabs)
        
        # 수직 비율 설정
        v_splitter.setSizes([600, 250])
        v_splitter.setHandleWidth(1)
        
        main_layout.addWidget(v_splitter)
        
        # 실시간 데이터 업데이터 시작
        self.start_market_updater()
    
    def start_market_updater(self):
        """실시간 마켓 데이터 업데이터 시작"""
        from api.upbit_api import MarketDataUpdater
        
        self.market_updater = MarketDataUpdater(fiat="KRW", update_interval=5)
        self.market_updater.data_updated.connect(self.on_market_data_updated)
        self.market_updater.start()
        
        self.statusBar().showMessage("실시간 데이터 업데이트 시작...")
    
    def on_market_data_updated(self, market_data):
        """마켓 데이터 업데이트 콜백"""
        self.market_list.update_market_data(market_data)
        self.statusBar().showMessage(f"마켓 데이터 업데이트됨 ({len(market_data)}개)")
    
    def on_ticker_selected(self, ticker):
        """티커 선택 시 차트 업데이트"""
        self.chart_widget.update_ticker(ticker)
        self.statusBar().showMessage(f"{ticker} 차트 로드 중...")
        
    def create_menu_bar(self):
        """메뉴 바 생성"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #1e2329;
                color: #ffffff;
                border-bottom: 1px solid #2b3139;
                padding: 5px;
            }
            QMenuBar::item {
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #2b3139;
            }
        """)
        
        # 파일 메뉴
        file_menu = menubar.addMenu('파일')
        file_menu.addAction(self.create_action('설정', 'Ctrl+,', self.open_settings))
        file_menu.addAction(self.create_action('로그 보기', 'Ctrl+L', self.open_logs))
        file_menu.addSeparator()
        file_menu.addAction(self.create_action('종료', 'Ctrl+Q', self.close))
        
        # 거래 메뉴
        trading_menu = menubar.addMenu('거래')
        trading_menu.addAction(self.create_action('자동매매 시작', 'Ctrl+S', self.start_trading))
        trading_menu.addAction(self.create_action('자동매매 중지', 'Ctrl+X', self.stop_trading))
        trading_menu.addSeparator()
        trading_menu.addAction(self.create_action('긴급 전체 청산', 'Ctrl+E', self.emergency_stop))
        
        # 전략 메뉴
        strategy_menu = menubar.addMenu('전략')
        strategy_menu.addAction(self.create_action('AI 전략', '', None, checkable=True))
        strategy_menu.addAction(self.create_action('RSI 전략', '', None, checkable=True))
        strategy_menu.addAction(self.create_action('복합 전략', '', None, checkable=True))
        
        # 분석 메뉴
        analysis_menu = menubar.addMenu('분석')
        analysis_menu.addAction(self.create_action('백테스팅', '', self.open_backtest))
        analysis_menu.addAction(self.create_action('성과 분석', '', None))
        analysis_menu.addAction(self.create_action('AI 모델 평가', '', None))
        
        # 도움말 메뉴
        help_menu = menubar.addMenu('도움말')
        help_menu.addAction(self.create_action('사용자 매뉴얼', 'F1', None))
        help_menu.addAction(self.create_action('단축키 목록', '', None))
        help_menu.addSeparator()
        help_menu.addAction(self.create_action('정보', '', self.show_about))
        
    def create_action(self, text, shortcut='', slot=None, checkable=False):
        """액션 생성 헬퍼"""
        action= QAction(text, self)
        if shortcut:
            action.setShortcut(shortcut)
        if slot:
            action.triggered.connect(slot)
        if checkable:
            action.setCheckable(True)
        return action
        
    def create_status_bar(self):
        """상태 바 생성"""
        status_bar = self.statusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #1e2329;
                color: #b7bdc6;
                border-top: 1px solid #2b3139;
            }
        """)
        status_bar.showMessage("준비 완료")
        
    # 메뉴 액션 슬롯들
    def open_settings(self):
        print("설정 열기")
        
    def open_logs(self):
        print("로그 보기")
        
    def start_trading(self):
        print("자동매매 시작")
        self.statusBar().showMessage("자동매매 시작됨")
        
    def stop_trading(self):
        print("자동매매 중지")
        self.statusBar().showMessage("자동매매 중지됨")
        
    def emergency_stop(self):
        print("긴급 청산!")
        
    def open_backtest(self):
        print("백테스팅 열기")
        
    def show_about(self):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.about(self, "정보", 
                         "Upbit Auto Trader v1.0\n\n"
                         "AI 기반 암호화폐 자동매매 프로그램\n\n"
                         "© 2025")
