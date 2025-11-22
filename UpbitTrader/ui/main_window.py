"""
Main Window - 메인 윈도우
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QSplitter, QTabWidget, QMenuBar, QMenu, QAction,
                             QStatusBar, QLabel, QPushButton, QToolBar, QMessageBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon

from ui.widgets.header_bar import HeaderBar
from ui.widgets.market_list import MarketListWidget
from ui.widgets.chart_widget import ChartWidget
from ui.widgets.orderbook_widget import OrderBookWidget
from ui.widgets.bottom_tabs import BottomTabsWidget
from ui.styles import DARK_STYLESHEET

# Phase 1 인프라 imports
from config import config
from database import DatabaseManager
from utils import setup_logger, logger, ErrorHandler


class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Upbit Auto Trader - AI 기반 자동매매")
        self.setGeometry(100, 100, 1600, 900)
        self.setMinimumSize(1366, 768)
        
        # Phase 1 인프라 초기화
        self.config = config
        self.logger = logger
        self.error_handler = ErrorHandler(logger)
        
        # 데이터베이스 초기화
        try:
            self.db = DatabaseManager(self.config.DB_PATH)
            self.logger.info("데이터베이스 연결 성공")
        except Exception as e:
            self.error_handler.handle(e, "데이터베이스 초기화")
            self.db = None
        
        # API 키 설정 확인
        if not self.config.is_api_configured():
            self.logger.warning("API 키가 설정되지 않았습니다. 설정에서 API 키를 입력하세요.")
        
        # 다크 테마 적용
        self.setStyleSheet(DARK_STYLESHEET)
        
        self.logger.info("메인 윈도우 초기화 시작")
        
        self.init_ui()
        self.create_menu_bar()
        self.create_status_bar()
        
        # 시스템 상태 업데이트
        self.update_system_status()
        
        self.logger.info("메인 윈도우 초기화 완료")
        
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
        try:
            from api.upbit_api import MarketDataUpdater
            
            self.market_updater = MarketDataUpdater(fiat="KRW", update_interval=5)
            self.market_updater.data_updated.connect(self.on_market_data_updated)
            self.market_updater.start()
            
            self.logger.info("마켓 데이터 업데이터 시작")
            self.statusBar().showMessage("실시간 데이터 업데이트 시작...")
        except Exception as e:
            self.error_handler.handle(e, "마켓 업데이터 시작")
            self.statusBar().showMessage("마켓 업데이터 시작 실패")
    
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
        """설정 다이얼로그 열기"""
        from ui.dialogs.settings_dialog import SettingsDialog
        
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_():
            # 설정이 변경된 경우
            self.logger.info("설정이 업데이트되었습니다")
            self.update_system_status()
            QMessageBox.information(self, "설정", "설정이 저장되었습니다.\n일부 설정은 재시작 후 적용됩니다.")
        
    def open_logs(self):
        """로그 뷰어 열기"""
        from ui.dialogs.log_viewer import LogViewerDialog
        
        dialog = LogViewerDialog(self.config.LOG_FILE, self)
        dialog.exec_()
        
    def start_trading(self):
        """자동매매 시작"""
        if not self.config.is_api_configured():
            QMessageBox.warning(self, "API 키 필요", "자동매매를 시작하려면 먼저 설정에서 API 키를 입력하세요.")
            return
        
        self.logger.info("[자동매매] 시작 요청")
        # TODO: 실제 매매 엔진 시작
        self.statusBar().showMessage("자동매매 시작됨")
        self.header_bar.update_status("trading", True)
        
    def stop_trading(self):
        """자동매매 중지"""
        self.logger.info("[자동매매] 중지 요청")
        # TODO: 실제 매매 엔진 중지
        self.statusBar().showMessage("자동매매 중지됨")
        self.header_bar.update_status("trading", False)
        
    def emergency_stop(self):
        """긴급 전체 청산"""
        reply = QMessageBox.warning(
            self, 
            "긴급 청산 확인", 
            "모든 포지션을 즉시 청산하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.logger.warning("[긴급 청산] 전체 청산 시작")
            # TODO: 실제 전체 청산 로직
            self.stop_trading()
            self.statusBar().showMessage("긴급 청산 완료")
            QMessageBox.information(self, "긴급 청산", "모든 포지션이 청산되었습니다.")
        
    def open_backtest(self):
        print("백테스팅 열기")
        
    def show_about(self):
        """정보 다이얼로그"""
        QMessageBox.about(self, "정보", 
                         "Upbit Auto Trader v1.0\n\n"
                         "AI 기반 암호화폐 자동매매 프로그램\n\n"
                         "© 2025")
    
    def update_system_status(self):
        """시스템 상태 업데이트"""
        try:
            # API 연결 상태
            api_status = self.config.is_api_configured()
            
            # DB 연결 상태
            db_status = self.db is not None
            
            # 헤더 바 상태 업데이트
            if hasattr(self, 'header_bar') and hasattr(self.header_bar, 'update_status'):
                self.header_bar.update_status("api", api_status)
                self.header_bar.update_status("database", db_status)
            
            # 상태 바 메시지
            status_msg = f"API: {'연결됨' if api_status else '미설정'} | DB: {'연결됨' if db_status else '연결 실패'}"
            self.statusBar().showMessage(status_msg)
            
        except Exception as e:
            self.error_handler.handle(e, "시스템 상태 업데이트")
    
    def closeEvent(self, event):
        """윈도우 종료 이벤트"""
        self.logger.info("프로그램 종료 중...")
        
        # 마켓 업데이터 중지
        if hasattr(self, 'market_updater'):
            self.market_updater.stop()
        
        # 데이터베이스 연결 종료
        if self.db:
            self.db.close()
            self.logger.info("데이터베이스 연결 종료")
        
        self.logger.info("프로그램 종료 완료")
        event.accept()
