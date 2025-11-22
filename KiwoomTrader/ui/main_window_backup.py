import sys
import asyncio
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
from trading_manager import TradingManager
from config import Config
from ai.backtester import Backtester
from ai.strategy_optimizer import StrategyOptimizer
from ai.recommender import StockRecommender
from watchlist_manager import WatchlistManager
from strategy_manager import StrategyManager
from logger import logger

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from settings_manager import settings
        
        # Progress bar for backtest
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        
        self.init_ui()
        self.load_styles()
        
        # Timer for UI updates (1 sec interval)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(1000)
        
    def load_styles(self):
        try:
            with open("ui/styles.qss", "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            logger.error(f"Failed to load styles: {e}")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Initialize Log Console early (so self.log works)
        log_group = QGroupBox("시스템 로그")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        log_group.setMaximumHeight(150)
        
        # 1. Top Bar (Status & Controls)
        top_bar = QHBoxLayout()
        
        self.status_label = QLabel("시스템: 준비")
        self.status_label.setStyleSheet("color: #00b894; font-weight: bold;")
        
        self.balance_label = QLabel(f"예수금: {self.trader.balance:,.0f} 원")
        self.balance_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        # New Account Info Labels
        self.total_asset_label = QLabel("총 자산: 0 원")
        self.total_asset_label.setStyleSheet("font-size: 14px; color: #dfe6e9; margin-left: 15px;")
        
        self.daily_profit_label = QLabel("당일 손익: 0 (+0.00%)")
        self.daily_profit_label.setStyleSheet("font-size: 14px; color: #dfe6e9; margin-left: 10px;")
        
        self.start_btn = QPushButton("자동매매 시작")
        self.start_btn.setObjectName("buyBtn") # Reusing style
        self.start_btn.clicked.connect(self.toggle_trading)
        
        self.panic_btn = QPushButton("긴급 정지")
        self.panic_btn.setObjectName("panicBtn")
        self.panic_btn.clicked.connect(self.panic_stop)
        
        top_bar.addWidget(self.status_label)
        top_bar.addStretch()
        
        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("종목명 또는 코드 검색")
        self.search_input.setFixedWidth(200)
        self.search_input.returnPressed.connect(self.search_stock)
        
        self.search_btn = QPushButton("검색")
        self.search_btn.clicked.connect(self.search_stock)
        
        top_bar.addWidget(self.search_input)
        top_bar.addWidget(self.search_btn)
        top_bar.addStretch()
        
        top_bar.addWidget(self.balance_label)
        top_bar.addWidget(self.total_asset_label)
        top_bar.addWidget(self.daily_profit_label)
        top_bar.addWidget(self.start_btn)
        top_bar.addWidget(self.panic_btn)
        
        main_layout.addLayout(top_bar)
        
        # 2. Content Area (Tabs)
        self.tabs = QTabWidget()
        
        self.tab_dashboard = QWidget()
        self.tab_chart = QWidget()
        self.tab_watchlist = QWidget()
        self.tab_recommend = QWidget()
        self.tab_backtest = QWidget()
        self.tab_settings = QWidget()
        
        self.tabs.addTab(self.tab_dashboard, "대시보드")
        self.tabs.addTab(self.tab_chart, "실시간 차트")
        self.tabs.addTab(self.tab_watchlist, "⭐ 관심종목")
        self.tabs.addTab(self.tab_recommend, "🎯 AI 추천")
        self.tabs.addTab(self.tab_backtest, "백테스트")
        self.tabs.addTab(self.tab_settings, "설정")
        
        self.init_dashboard()
        self.init_chart()
        self.init_watchlist()
        self.init_recommend()
        self.init_backtest()
        self.init_settings()
        
        main_layout.addWidget(self.tabs)
        
        # 3. Add Log Console to Layout
        main_layout.addWidget(log_group)

        
        # 4. Progress Bar
        main_layout.addWidget(self.progress_bar)

    def init_dashboard(self):
        layout = QGridLayout()
        
        # Account Summary
        acc_group = QGroupBox("계좌 요약")
        acc_layout = QFormLayout()
        self.lbl_total_asset = QLabel("0")
        self.lbl_daily_profit = QLabel("0 (+0.00%)")
        acc_layout.addRow("총 자산:", self.lbl_total_asset)
        acc_layout.addRow("당일 손익:", self.lbl_daily_profit)
        acc_group.setLayout(acc_layout)
        
        # Active Positions
        pos_group = QGroupBox("보유 종목")
        pos_layout = QVBoxLayout()
        self.pos_table = QTableWidget()
        self.pos_table.setColumnCount(5)
        self.pos_table.setHorizontalHeaderLabels(["종목코드", "종목명", "수량", "평단가", "수익률"])
        self.pos_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        pos_layout.addWidget(self.pos_table)
        pos_group.setLayout(pos_layout)
        
        layout.addWidget(acc_group, 0, 0)
        layout.addWidget(pos_group, 1, 0)
        self.tab_dashboard.setLayout(layout)

    def init_chart(self):
        layout = QVBoxLayout()
        
        # Chart Widget
        self.chart_widget = pg.PlotWidget()
        self.chart_widget.setBackground('#1e1e1e')
        self.chart_widget.showGrid(x=True, y=True)
        layout.addWidget(self.chart_widget)
        
        self.tab_chart.setLayout(layout)
    
    def init_watchlist(self):
        """관심종목 탭 초기화"""
        layout = QVBoxLayout()
        
        # 상단 컨트롤
        control_layout = QHBoxLayout()
        
        self.watchlist_code_input = QLineEdit()
        self.watchlist_code_input.setPlaceholderText("종목 코드 (예: 005930)")
        self.watchlist_code_input.returnPressed.connect(self.add_to_watchlist)
        
        self.watchlist_name_input = QLineEdit()
        self.watchlist_name_input.setPlaceholderText("종목명 (선택)")
        self.watchlist_name_input.returnPressed.connect(self.add_to_watchlist)
        
        add_btn = QPushButton("➕ 추가")
        add_btn.clicked.connect(self.add_to_watchlist)
        add_btn.setStyleSheet("background-color: #00b894; color: white;")
        
        remove_btn = QPushButton("➖ 제거")
        remove_btn.clicked.connect(self.remove_from_watchlist)
        remove_btn.setStyleSheet("background-color: #d63031; color: white;")
        
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self.load_watchlist)
        
        control_layout.addWidget(QLabel("종목:"))
        control_layout.addWidget(self.watchlist_code_input)
        control_layout.addWidget(self.watchlist_name_input)
        control_layout.addWidget(add_btn)
        control_layout.addWidget(remove_btn)
        control_layout.addWidget(refresh_btn)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # 관심종목 테이블
        self.watchlist_table = QTableWidget()
        self.watchlist_table.setColumnCount(3)
        self.watchlist_table.setHorizontalHeaderLabels(["종목코드", "종목명", "현재가"])
        self.watchlist_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.watchlist_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.watchlist_table)
        
        self.tab_watchlist.setLayout(layout)
        
        # 초기 로드
        self.load_watchlist()
    
    def init_recommend(self):
        """AI 추천 탭 초기화"""
        layout = QVBoxLayout()
        
        # 설명
        desc_label = QLabel(
            "AI가 관심종목을 분석하여 매수 타이밍이 좋은 종목을 추천합니다.\n"
            "AI 점수 + 감성분석 + 기술적 지표를 종합하여 평가합니다."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #b2bec3; font-size: 12px; padding: 10px;")
        layout.addWidget(desc_label)
        
        # 분석 버튼
        btn_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton("🎯 관심종목 분석 시작")
        self.analyze_btn.setStyleSheet("background-color: #6c5ce7; color: white; font-weight: bold; padding: 10px;")
        self.analyze_btn.clicked.connect(self.analyze_watchlist)
        
        btn_layout.addWidget(self.analyze_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 진행률
        self.recommend_progress = QProgressBar()
        self.recommend_progress.setRange(0, 100)
        self.recommend_progress.setValue(0)
        self.recommend_progress.setVisible(False)
        layout.addWidget(self.recommend_progress)
        
        # 추천 결과 테이블
        self.recommend_table = QTableWidget()
        self.recommend_table.setColumnCount(7)
        self.recommend_table.setHorizontalHeaderLabels([
            "종목코드", "종목명", "현재가", "AI점수", "감성", "기술", "추천"
        ])
        self.recommend_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.recommend_table)
        
        self.tab_recommend.setLayout(layout)

    def init_backtest(self):
        layout = QVBoxLayout()
        
        control_layout = QHBoxLayout()
        self.bt_code_input = QLineEdit("005930")
        self.bt_start_btn = QPushButton("백테스트 실행")
        self.bt_start_btn.clicked.connect(self.run_backtest)
        self.bt_optimize_btn = QPushButton("🚀 전략 최적화")
        self.bt_optimize_btn.clicked.connect(self.run_optimization)
        self.bt_optimize_btn.setStyleSheet("background-color: #6c5ce7; color: white; font-weight: bold;")
        control_layout.addWidget(QLabel("종목코드:"))
        control_layout.addWidget(self.bt_code_input)
        control_layout.addWidget(self.bt_start_btn)
        control_layout.addWidget(self.bt_optimize_btn)
        control_layout.addStretch()
        
        self.bt_result_text = QTextEdit()
        self.bt_result_text.setReadOnly(True)
        
        layout.addLayout(control_layout)
        layout.addWidget(self.bt_result_text)
        self.tab_backtest.setLayout(layout)
    
    def init_settings(self):
        """설정 탭 초기화 - AI 학습 포함"""
        layout = QVBoxLayout()
        
        # AI 학습 섹션
        ai_train_group = QGroupBox("🤖 AI 모델 학습")
        ai_train_layout = QVBoxLayout()
        
        # 설명
        desc_label = QLabel(
            "고급 AI 모델(LSTM + XGBoost)을 학습합니다.\n"
            "실제 과거 데이터를 다운로드하여 학습하므로 10-15분 정도 소요됩니다."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #b2bec3; font-size: 12px;")
        ai_train_layout.addWidget(desc_label)
        
        # 학습 설정
        settings_layout = QFormLayout()
        
        self.train_code_input = QLineEdit("005930")
        self.train_code_input.setPlaceholderText("종목 코드 (예: 005930)")
        
        self.train_interval_combo = QComboBox()
        # Seconds not supported by yfinance standardly, keeping minutes/hours/days
        self.train_interval_combo.addItems(["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"])
        self.train_interval_combo.setCurrentText("1h")
        self.train_interval_combo.setToolTip("1h 권장 (1m은 데이터가 너무 많음)")
        self.train_interval_combo.currentTextChanged.connect(self.on_interval_changed)
        
        self.train_period_combo = QComboBox()
        # Initial population will be handled by on_interval_changed
        self.train_period_combo.currentTextChanged.connect(self.update_estimated_time)
        
        self.use_gpu_check = QCheckBox("GPU 사용 (Use GPU)")
        self.use_gpu_check.setChecked(False)
        self.use_gpu_check.stateChanged.connect(self.update_estimated_time)
        
        self.estimated_time_label = QLabel("예상 소요 시간: 계산 중...")
        self.estimated_time_label.setStyleSheet("color: #fdcb6e; font-style: italic;")
        
        # Trigger initial update
        self.on_interval_changed(self.train_interval_combo.currentText())
        
        settings_layout.addRow("종목 코드:", self.train_code_input)
        settings_layout.addRow("데이터 간격:", self.train_interval_combo)
        settings_layout.addRow("학습 기간:", self.train_period_combo)
        settings_layout.addRow("", self.use_gpu_check)
        settings_layout.addRow("", self.estimated_time_label)
        
        ai_train_layout.addLayout(settings_layout)
        
        # 학습 버튼
        button_layout = QHBoxLayout()
        
        self.train_start_btn = QPushButton("🚀 학습 시작")
        self.train_start_btn.setStyleSheet("background-color: #00b894; color: white; font-weight: bold; padding: 10px;")
        self.train_start_btn.clicked.connect(self.start_ai_training)
        
        self.train_stop_btn = QPushButton("⏹️ 중지")
        self.train_stop_btn.setStyleSheet("background-color: #d63031; color: white; padding: 10px;")
        self.train_stop_btn.setEnabled(False)
        self.train_stop_btn.clicked.connect(self.cancel_training)
        
        button_layout.addWidget(self.train_start_btn)
        button_layout.addWidget(self.train_stop_btn)
        button_layout.addStretch()
        
        ai_train_layout.addLayout(button_layout)
        
        # 진행률 표시
        self.train_progress = QProgressBar()
        self.train_progress.setRange(0, 100)
        self.train_progress.setValue(0)
        self.train_progress.setVisible(False)
        self.train_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #636e72;
                border-radius: 5px;
                text-align: center;
                background-color: #2d3436;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00b894, stop:1 #00cec9);
                border-radius: 3px;
            }
        """)
        ai_train_layout.addWidget(self.train_progress)
        
        # 결과 표시
        self.train_result_text = QTextEdit()
        self.train_result_text.setReadOnly(True)
        self.train_result_text.setMaximumHeight(200)
        self.train_result_text.setPlaceholderText("학습 결과가 여기에 표시됩니다...")
        ai_train_layout.addWidget(self.train_result_text)
        
        ai_train_group.setLayout(ai_train_layout)
        layout.addWidget(ai_train_group)
        
        # 일반 설정 섹션
        general_group = QGroupBox("⚙️ 일반 설정")
        general_layout = QFormLayout()
        
        # Settings Button
        self.open_settings_btn = QPushButton("🛠️ API 및 계좌 설정")
        self.open_settings_btn.clicked.connect(self.open_settings_dialog)
        self.open_settings_btn.setStyleSheet("padding: 10px; font-weight: bold;")
        
        general_layout.addRow(self.open_settings_btn)
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        layout.addStretch()
        self.tab_settings.setLayout(layout)

    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec_():
            self.log("설정이 저장되었습니다. 일부 변경사항은 재시작 후 적용됩니다.")
            # Reload dynamic settings if needed
            pass

    def on_interval_changed(self, interval):
        """데이터 간격 변경 시 학습 기간 옵션 자동 조정"""
        self.train_period_combo.blockSignals(True)
        self.train_period_combo.clear()
        
        periods = []
        default_period = ""
        
        if interval == "1m":
            # Max 7 days
            periods = ["1d", "5d"]
            default_period = "5d"
        elif interval in ["2m", "5m", "15m", "30m", "90m"]:
            # Max 60 days
            periods = ["1d", "5d", "1mo"]
            default_period = "1mo"
        elif interval in ["60m", "1h"]:
            # Max 730 days (2 years)
            periods = ["1mo", "3mo", "6mo", "1y", "2y"]
            default_period = "1y"
        else:
            # Daily+ (Unlimited)
            periods = ["6mo", "1y", "2y", "5y", "10y", "max"]
            default_period = "5y"
            
        self.train_period_combo.addItems(periods)
        self.train_period_combo.setCurrentText(default_period)
        self.train_period_combo.blockSignals(False)
        
        self.update_estimated_time()

    def update_estimated_time(self):
        """예상 학습 시간 계산"""
        period = self.train_period_combo.currentText()
        interval = self.train_interval_combo.currentText()
        use_gpu = self.use_gpu_check.isChecked()
        
        # Base time in minutes (rough estimation)
        base_time = 5 
        
        # Period factor
        if period == "1mo": factor = 0.2
        elif period == "3mo": factor = 0.5
        elif period == "6mo": factor = 0.8
        elif period == "1y": factor = 1.0
        elif period == "2y": factor = 1.8
        elif period == "5y": factor = 4.0
        else: factor = 1.0
        
        # Interval factor (smaller interval = more data)
        if interval == "1m": factor *= 10.0
        elif interval == "5m": factor *= 3.0
        elif interval == "30m": factor *= 1.5
        elif interval == "1h": factor *= 1.0
        elif interval == "1d": factor *= 0.2
        else: factor *= 1.0
        
        est_minutes = base_time * factor
        
        if use_gpu:
            est_minutes *= 0.4 # GPU speedup
            
        self.estimated_time_label.setText(f"예상 소요 시간: 약 {est_minutes:.1f} 분")


    def update_ui(self):
        # Update Status
        if self.trader.is_running:
            self.status_label.setText("시스템: 실행 중")
            self.status_label.setStyleSheet("color: #00b894; font-weight: bold;")
        else:
            self.status_label.setText("시스템: 중지됨")
            self.status_label.setStyleSheet("color: #d63031; font-weight: bold;")
            
        # Update Balance
        self.balance_label.setText(f"예수금: {self.trader.balance:,.0f} 원")
        self.lbl_total_asset.setText(f"{self.trader.total_assets:,.0f} 원")
        
        # Update Top Bar Labels
        self.total_asset_label.setText(f"총 자산: {self.trader.total_assets:,.0f} 원")
        
        # Calculate Daily Profit (Mock logic for now, needs real PnL tracking)
        # Assuming initial balance was 100,000,000 or tracked elsewhere
        start_balance = 100000000 # Example fixed start balance
        profit = self.trader.total_assets - start_balance
        profit_pct = (profit / start_balance) * 100 if start_balance > 0 else 0
        
        profit_str = f"{profit:+,.0f} ({profit_pct:+.2f}%)"
        self.daily_profit_label.setText(f"당일 손익: {profit_str}")
        
        if profit > 0:
            self.daily_profit_label.setStyleSheet("font-size: 14px; color: #00b894; margin-left: 10px; font-weight: bold;")
        elif profit < 0:
            self.daily_profit_label.setStyleSheet("font-size: 14px; color: #d63031; margin-left: 10px; font-weight: bold;")
        else:
            self.daily_profit_label.setStyleSheet("font-size: 14px; color: #dfe6e9; margin-left: 10px;")
            
        self.lbl_daily_profit.setText(profit_str)
        
        # Update Positions Table
        self.pos_table.setRowCount(len(self.trader.portfolio))
        for i, (code, data) in enumerate(self.trader.portfolio.items()):
            self.pos_table.setItem(i, 0, QTableWidgetItem(code))
            self.pos_table.setItem(i, 1, QTableWidgetItem(data.get('name', 'Unknown')))
            self.pos_table.setItem(i, 2, QTableWidgetItem(str(data['qty'])))
            self.pos_table.setItem(i, 3, QTableWidgetItem(f"{data['avg_price']:,.0f}"))
            
            # Mock current price for profit calc
            curr_price = data['avg_price'] # Placeholder
            profit_pct = 0.0
            
            item_profit = QTableWidgetItem(f"{profit_pct:.2f}%")
            if profit_pct > 0:
                item_profit.setForeground(QColor("#00b894"))
            elif profit_pct < 0:
                item_profit.setForeground(QColor("#d63031"))
            self.pos_table.setItem(i, 4, item_profit)

    def toggle_trading(self):
        if not self.trader.is_running:
            asyncio.create_task(self.trader.start())
            self.start_btn.setText("자동매매 중지")
            self.start_btn.setStyleSheet("background-color: #d63031;")
            self.log("자동매매 시작됨")
        else:
            asyncio.create_task(self.trader.stop())
            self.start_btn.setText("자동매매 시작")
            self.start_btn.setStyleSheet("background-color: #00b894;")
            self.log("자동매매 중지됨")

    def panic_stop(self):
        asyncio.create_task(self.trader.stop())
        self.log("긴급 정지 발동!")
        QMessageBox.critical(self, "긴급 정지", "긴급 정지가 발동되었습니다! 모든 작업이 중단됩니다.")

    def run_backtest(self):
        code = self.bt_code_input.text()
        
        # Calculate dates: Last 1 year
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=365)
        
        start_date = start_dt.strftime("%Y-%m-%d")
        end_date = end_dt.strftime("%Y-%m-%d")
        
        self.log(f"{code} 백테스트 실행 중... ({start_date} ~ {end_date})")
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Define progress callback
        def progress_callback(pct):
            self.progress_bar.setValue(pct)
            QApplication.processEvents()  # Update UI
        
        # Run backtest with progress callback
        result = self.backtester.run(code, start_date, end_date, progress_callback=progress_callback)
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Process Daily Summary with BUY/SELL separation
        daily_stats = {}
        for trade in result['trades']:
            date = trade['date'][:10]  # Extract date part only (YYYY-MM-DD)
            if date not in daily_stats:
                daily_stats[date] = {'buy': 0, 'sell': 0, 'profit': 0}
            
            if trade['type'] == 'BUY':
                daily_stats[date]['buy'] += 1
            elif trade['type'] == 'SELL':
                daily_stats[date]['sell'] += 1
                daily_stats[date]['profit'] += trade.get('profit', 0)

        # Build HTML daily report with colors
        daily_report_html = "<h3>📊 일별 매매 요약</h3><table border='1' cellpadding='5' style='border-collapse: collapse; width: 100%;'>"
        daily_report_html += "<tr style='background-color: #2d3436; color: white;'><th>날짜</th><th>매수</th><th>매도</th><th>손익</th></tr>"
        
        for date, stats in sorted(daily_stats.items()):
            profit = stats['profit']
            if profit > 0:
                profit_color = '#00b894'
                profit_str = f"+{profit:,.0f}원"
            elif profit < 0:
                profit_color = '#d63031'
                profit_str = f"{profit:,.0f}원"
            else:
                profit_color = '#636e72'
                profit_str = "0원"
            
            daily_report_html += f"<tr>"
            daily_report_html += f"<td>{date}</td>"
            daily_report_html += f"<td style='color: #0984e3;'>{stats['buy']}회</td>"
            daily_report_html += f"<td style='color: #e17055;'>{stats['sell']}회</td>"
            daily_report_html += f"<td style='color: {profit_color}; font-weight: bold;'>{profit_str}</td>"
            daily_report_html += "</tr>"
        
        daily_report_html += "</table>"
        
        # Build main report in HTML format
        total_profit_color = '#00b894' if result['profit_pct'] > 0 else '#d63031'
        
        report_html = f"""
        <html>
        <body style='font-family: "Malgun Gothic", sans-serif; background-color: #1e1e1e; color: #dfe6e9;'>
            <h2 style='color: #74b9ff;'>📈 백테스트 결과</h2>
            <table style='width: 100%;'>
                <tr><td><b>기간:</b></td><td>{start_date} ~ {end_date}</td></tr>
                <tr><td><b>종목코드:</b></td><td>{code}</td></tr>
                <tr><td><b>최종 잔고:</b></td><td>{result['final_balance']:,.0f}원</td></tr>
                <tr><td><b>총 수익:</b></td><td style='color: {total_profit_color}; font-weight: bold;'>{result['total_profit']:,.0f}원 ({result['profit_pct']:.2f}%)</td></tr>
                <tr><td><b>매매 횟수:</b></td><td>{result['trade_count']}회</td></tr>
                <tr><td><b>MDD:</b></td><td style='color: #d63031;'>{result['mdd']:.2f}%</td></tr>
            </table>
            <br>
            {daily_report_html}
        </body>
        </html>
        """
        
        self.bt_result_text.setHtml(report_html)
        self.log("백테스트 완료")
    
    def run_optimization(self):
        """전략 파라미터 최적화 실행"""
        code = self.bt_code_input.text()
        
       # Calculate dates: Last 1 year
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=365)
        
        start_date = start_dt.strftime("%Y-%m-%d")
        end_date = end_dt.strftime("%Y-%m-%d")
        
        self.log(f"🚀 전략 최적화 시작... (종목: {code}, 기간: {start_date} ~ {end_date})")
        self.log("⚠️ 최적화는 수십 ~ 수백 번의 백테스트를 실행하므로 시간이 걸릴 수 있습니다.")
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Define progress callback
        def progress_callback(pct):
            self.progress_bar.setValue(pct)
            QApplication.processEvents()
        
        # Run optimization
        optimizer = StrategyOptimizer()
        best_result, best_params, all_results = optimizer.optimize(
            code, start_date, end_date, progress_callback=progress_callback
        )
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Get top 5 results
        top_results = optimizer.get_top_results(5)
        
        # Build HTML report
        report_html = f"""
        <html>
        <body style='font-family: "Malgun Gothic", sans-serif; background-color: #1e1e1e; color: #dfe6e9;'>
            <h2 style='color: #6c5ce7;'>🚀 전략 최적화 결과</h2>
            <h3 style='color: #74b9ff;'>📊 최고 성과 전략</h3>
            <table style='width: 100%; border: 1px solid #636e72;' cellpadding='5'>
                <tr style='background-color: #2d3436; color: white;'>
                    <th>파라미터</th><th>값</th>
                </tr>
                <tr><td>볼륨 임계값</td><td>{best_params['vol_threshold']}</td></tr>
                <tr><td>AI 점수 임계값</td><td>{best_params['ai_threshold']}</td></tr>
                <tr><td>익절 목표</td><td>{best_params['take_profit']}%</td></tr>
                <tr><td>손절 목표</td><td>{best_params['stop_loss']}%</td></tr>
                <tr><td>쿨다운</td><td>{best_params['cooldown']}분</td></tr>
            </table>
            <br>
            <h4 style='color: #00b894;'>✨ 성과</h4>
            <table style='width: 100%;'>
                <tr><td><b>총 수익:</b></td><td style='color: #00b894; font-weight: bold;'>{best_result['total_profit']:,.0f}원 ({best_result['profit_pct']:.2f}%)</td></tr>
                <tr><td><b>최종 잔고:</b></td><td>{best_result['final_balance']:,.0f}원</td></tr>
                <tr><td><b>매매 횟수:</b></td><td>{best_result['trade_count']}회</td></tr>
                <tr><td><b>MDD:</b></td><td style='color: #d63031;'>{best_result['mdd']:.2f}%</td></tr>
                <tr><td><b>평가 점수:</b></td><td style='color: #fdcb6e; font-weight: bold;'>{best_result['score']:.2f}</td></tr>
            </table>
            <br>
            <h4>🏆 상위 5개 전략</h4>
            <table border='1' cellpadding='5' style='border-collapse: collapse; width: 100%;'>
                <tr style='background-color: #2d3436; color: white;'>
                    <th>순위</th><th>수익률</th><th>MDD</th><th>매매</th><th>점수</th><th>TP/SL</th><th>AI</th>
                </tr>
        """
        
        for idx, res in enumerate(top_results, 1):
            profit_color = '#00b894' if res['profit_pct'] > 0 else '#d63031'
            report_html += f"""
                <tr>
                    <td>{idx}</td>
                    <td style='color: {profit_color}; font-weight: bold;'>{res['profit_pct']:.2f}%</td>
                    <td style='color: #d63031;'>{res['mdd']:.2f}%</td>
                    <td>{res['trade_count']}회</td>
                    <td style='color: #fdcb6e;'>{res['score']:.2f}</td>
                    <td>{res['params']['take_profit']}/{res['params']['stop_loss']}</td>
                    <td>{res['params']['ai_threshold']}</td>
                </tr>
            """
        
        report_html += """
            </table>
            <br>
            <p style='color: #636e72; font-size: 12px;'>
                ⓘ 평가 점수 = 수익률 - (MDD / 2)<br>
                높은 수익률과 낮은 MDD를 동시에 고려합니다.
            </p>
            <br>
            <button onclick='alert(\"전략 선택 기능은 아래 버튼을 사용하세요\")' 
                    style='background-color: #00b894; color: white; padding: 10px 20px; border: none; cursor: pointer; font-size: 14px; border-radius: 5px;'>
                💾 결과 저장 완료
            </button>
        </body>
        </html>
        """
        
        self.bt_result_text.setHtml(report_html)
        self.log(f"✅ 최적화 완료! 총 {len(all_results)}개 조합 테스트 완료")
        
        # 결과 저장
        self.strategy_manager.save_optimization_results(code, all_results, best_params)
        self.log("💾 최적화 결과 저장 완료")
        
        # 전략 선택 다이얼로그 표시
        self.show_strategy_selection_dialog()

    def start_ai_training(self):
        """AI 모델 학습 시작"""
        import threading
        
        # UI 잠금
        self.train_start_btn.setEnabled(False)
        self.train_stop_btn.setEnabled(True)
        self.train_progress.setVisible(True)
        self.train_progress.setValue(0)
        self.train_result_text.clear()
        
        # 파라미터 가져오기
        # 파라미터 가져오기
        stock_code = self.train_code_input.text()
        period = self.train_period_combo.currentText()
        interval = self.train_interval_combo.currentText()
        use_gpu = self.use_gpu_check.isChecked()
        
        self.log(f"🤖 AI 학습 시작: {stock_code}, {period}, {interval}")
        self.train_result_text.append(f"[시작] 종목: {stock_code}, 기간: {period}, 간격: {interval}\n")
        
        # 별도 스레드에서 학습 실행
        def train_thread():
            try:
                from ai.data_collector import DataCollector
                from ai.indicators import IndicatorCalculator
                from ai.lstm_model import LSTMPredictor
                from ai.xgboost_model import XGBoostPredictor
                import numpy as np
                
                # 1. 데이터 수집 (20%)
                self.train_progress.setValue(5)
                self.train_result_text.append("[1/4] 데이터 다운로드 중...")
                QApplication.processEvents()
                
                collector = DataCollector()
                yf_symbol = DataCollector.convert_korean_code(stock_code)
                df = collector.get_stock_data(yf_symbol, period=period, interval=interval, use_cache=False)
                
                if df is None or len(df) < 1000:
                    self.train_result_text.append("❌ 오류: 데이터가 부족합니다!")
                    self._finish_training(False)
                    return
                
                self.train_progress.setValue(20)
                self.train_result_text.append(f"✓ 다운로드 완료: {len(df)}개 캔들\n")
                QApplication.processEvents()
                
                # 2. 지표 계산 (30%)
                self.train_result_text.append("[2/4] 기술적 지표 계산 중...")
                QApplication.processEvents()
                
                df = IndicatorCalculator.calculate_all(df)
                df = df.dropna()
                
                if len(df) < 500:
                    self.train_result_text.append("❌ 오류: 지표 계산 후 데이터 부족!")
                    self._finish_training(False)
                    return
                
                self.train_progress.setValue(30)
                self.train_result_text.append(f"✓ 지표 계산 완료: {len(df)}개 데이터 포인트\n")
                QApplication.processEvents()
                
                # 3. LSTM 학습 (30-60%)
                self.train_result_text.append("[3/4] LSTM 모델 학습 중...")
                self.train_result_text.append("  (시간이 걸릴 수 있습니다...)")
                QApplication.processEvents()
                
                lookback = 100
                X_lstm, y_lstm, scaler = collector.prepare_training_data(df, lookback=lookback)
                
                if len(X_lstm) < 100:
                    self.train_result_text.append("❌ 오류: LSTM 학습 데이터 부족!")
                    self._finish_training(False)
                    return
                
                lstm_model = LSTMPredictor(lookback=lookback, n_features=X_lstm.shape[2])
                
                # 간단한 진행률 업데이트 (LSTM 학습 중 30-60%)
                for epoch_pct in range(30, 61, 5):
                    self.train_progress.setValue(epoch_pct)
                    QApplication.processEvents()
                
                lstm_history = lstm_model.train(X_lstm, y_lstm, epochs=20, batch_size=32)
                
                self.train_progress.setValue(60)
                self.train_result_text.append("✓ LSTM 학습 완료\n")
                QApplication.processEvents()
                
                # 4. XGBoost 학습 (60-90%)
                self.train_result_text.append("[4/4] XGBoost 모델 학습 중...")
                QApplication.processEvents()
                
                feature_cols = IndicatorCalculator.get_feature_names()
                X_xgb = df[feature_cols].values
                y_xgb = (df['close'].shift(-1) > df['close']).astype(int).values
                
                mask = ~np.isnan(y_xgb)
                X_xgb = X_xgb[mask]
                y_xgb = y_xgb[mask]
                
                self.train_progress.setValue(70)
                QApplication.processEvents()
                
                xgboost_model = XGBoostPredictor()
                xgb_metrics = xgboost_model.train(X_xgb, y_xgb)
                
                self.train_progress.setValue(90)
                self.train_result_text.append("✓ XGBoost 학습 완료\n")
                QApplication.processEvents()
                
                # 5. 완료 (100%)
                self.train_progress.setValue(100)
                self.train_result_text.append("\n" + "="*50)
                self.train_result_text.append("\n✅ 학습 완료!\n")
                self.train_result_text.append("="*50 + "\n")
                self.train_result_text.append(f"📊 XGBoost 정확도: {xgb_metrics['accuracy']:.2%}\n")
                self.train_result_text.append(f"📊 XGBoost AUC: {xgb_metrics['auc']:.4f}\n")
                self.train_result_text.append(f"\n모델 저장 위치:\n")
                self.train_result_text.append(f"  - {lstm_model.model_path}\n")
                self.train_result_text.append(f"  - {xgboost_model.model_path}\n")
                
                self.log(f"✅ AI 학습 완료: 정확도 {xgb_metrics['accuracy']:.2%}")
                self._finish_training(True)
                
            except Exception as e:
                self.train_result_text.append(f"\n❌ 오류 발생: {str(e)}\n")
                self.log(f"❌ AI 학습 실패: {str(e)}")
                self._finish_training(False)
        
        # 스레드 시작
        thread = threading.Thread(target=train_thread, daemon=True)
        thread.start()
    
    def _finish_training(self, success):
        """학습 완료 후 UI 복원"""
        self.train_start_btn.setEnabled(True)
        self.train_stop_btn.setEnabled(False)
        if not success:
            self.train_progress.setVisible(False)

    def add_to_watchlist(self):
        """관심종목 추가"""
        code = self.watchlist_code_input.text().strip()
        name = self.watchlist_name_input.text().strip()
        
        if not code:
            self.log("종목 코드를 입력하세요")
            return
        
        if self.watchlist_manager.add(code, name):
            self.log(f"✅ {code} 관심종목에 추가")
            self.watchlist_code_input.clear()
            self.watchlist_name_input.clear()
            self.load_watchlist()
        else:
            self.log(f"⚠️ {code}는 이미 관심종목에 있습니다")
    
    def remove_from_watchlist(self):
        """관심종목 제거"""
        selected = self.watchlist_table.selectedItems()
        if not selected:
            self.log("제거할 종목을 선택하세요")
            return
        
        row = selected[0].row()
        code = self.watchlist_table.item(row, 0).text()
        
        if self.watchlist_manager.remove(code):
            self.log(f"🗑️ {code} 관심종목에서 제거")
            self.load_watchlist()
        else:
            self.log(f"❌ {code} 제거 실패")
    
    def load_watchlist(self):
        """관심종목 로드 및 표시"""
        stocks = self.watchlist_manager.get_all()
        
        self.watchlist_table.setRowCount(len(stocks))
        
        for i, stock in enumerate(stocks):
            self.watchlist_table.setItem(i, 0, QTableWidgetItem(stock['code']))
            self.watchlist_table.setItem(i, 1, QTableWidgetItem(stock.get('name', '-')))
            self.watchlist_table.setItem(i, 2, QTableWidgetItem('-'))  # 현재가는 나중에 업데이트
        
        self.log(f"📋 관심종목 {len(stocks)}개 로드 완료")
    
    def analyze_watchlist(self):
        """관심종목 AI 분석"""
        import threading
        import asyncio
        
        stocks = self.watchlist_manager.get_codes()
        
        if not stocks:
            self.log("⚠️ 관심종목이 없습니다. 먼저 종목을 추가하세요.")
            return
        
        # UI 잠금
        self.analyze_btn.setEnabled(False)
        self.recommend_progress.setVisible(True)
        self.recommend_progress.setValue(0)
        self.recommend_table.setRowCount(0)
        
        self.log(f"🎯 {len(stocks)}개 종목 분석 시작...")
        
        def analyze_thread():
            try:
                # 비동기 루프 생성
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # 진행률 업데이트 함수
                def update_progress(current, total):
                    pct = int((current / total) * 100)
                    self.recommend_progress.setValue(pct)
                    QApplication.processEvents()
                
                # 종목 분석
                results = []
                for idx, code in enumerate(stocks):
                    update_progress(idx, len(stocks))
                    result = loop.run_until_complete(self.recommender.analyze_stock(code))
                    if result:
                        results.append(result)
                
                loop.close()
                
                # 결과 정렬 (점수 높은 순)
                results.sort(key=lambda x: x['score'], reverse=True)
                
                # UI 업데이트
                self.recommend_progress.setValue(100)
                self.display_recommendations(results)
                
                self.log(f"✅ 분석 완료! 상위 {min(5, len(results))}개 종목 추천")
                
            except Exception as e:
                self.log(f"❌ 분석 실패: {str(e)}")
                logger.error(f"Analysis error: {e}")
            
            finally:
                # UI 복원
                self.analyze_btn.setEnabled(True)
                self.recommend_progress.setVisible(False)
        
        # 스레드 시작
        thread = threading.Thread(target=analyze_thread, daemon=True)
        thread.start()
    
    def display_recommendations(self, results):
        """추천 결과 표시"""
        self.recommend_table.setRowCount(len(results))
        
        for i, result in enumerate(results):
            # 종목코드
            self.recommend_table.setItem(i, 0, QTableWidgetItem(result['code']))
            
            # 종목명 (관심종목에서 가져오기)
            stocks = self.watchlist_manager.get_all()
            name = next((s['name'] for s in stocks if s['code'] == result['code']), '-')
            self.recommend_table.setItem(i, 1, QTableWidgetItem(name))
            
            # 현재가
            price_item = QTableWidgetItem(f"{result['current_price']:,.0f}")
            self.recommend_table.setItem(i, 2, price_item)
            
            # AI 점수
            ai_item = QTableWidgetItem(f"{result['ai_score']:.2f}")
            if result['ai_score'] > 0.7:
                ai_item.setForeground(QColor("#00b894"))
            elif result['ai_score'] < 0.4:
                ai_item.setForeground(QColor("#d63031"))
            self.recommend_table.setItem(i, 3, ai_item)
            
            # 감성 점수
            sent_item = QTableWidgetItem(f"{result['sentiment_score']:.2f}")
            if result['sentiment_score'] > 0.3:
                sent_item.setForeground(QColor("#00b894"))
            elif result['sentiment_score'] < -0.3:
                sent_item.setForeground(QColor("#d63031"))
            self.recommend_table.setItem(i, 4, sent_item)
            
            # 기술 점수
            tech_item = QTableWidgetItem(f"{result['technical_score']:.2f}")
            self.recommend_table.setItem(i, 5, tech_item)
            
            # 추천 등급
            rec_item = QTableWidgetItem(f"{result['grade']} - {result['recommendation']}")
            rec_item.setFont(QFont("Malgun Gothic", 10, QFont.Bold))
            
            if result['grade'] == 'A':
                rec_item.setForeground(QColor("#00b894"))
            elif result['grade'] == 'B':
                rec_item.setForeground(QColor("#74b9ff"))
            elif result['grade'] in ['D', 'F']:
                rec_item.setForeground(QColor("#d63031"))
            
            self.recommend_table.setItem(i, 6, rec_item)

    def show_strategy_selection_dialog(self):
        """전략 선택 다이얼로그 표시"""
        latest = self.strategy_manager.get_latest_results()
        
        if not latest:
            QMessageBox.information(self, "전략 없음", "저장된 최적화 결과가 없습니다.")
            return
        
        # 간단한 전략 선택 (상위 10개 표시)
        top_10 = latest['top_10']
        
        msg = "전략 최적화 결과 저장 완료!\n\n"
        msg += f"총 테스트: {latest['total_tested']}개\n"
        msg += f"상위 전략: {len(top_10)}개\n\n"
        msg += f"최고 성능: 수익률 {top_10[0]['profit_pct']:.2f}%, MDD {top_10[0]['mdd']:.2f}%\n"
        
        QMessageBox.information(self, "전략 저장 완료", msg)
        self.log("💾 전략이 data/strategies.json에 저장되었습니다")

    def search_stock(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            return
            
        asyncio.create_task(self._perform_search(keyword))
        
    async def _perform_search(self, keyword):
        # Fetch master list
        stocks = await self.trader.api.get_master_list()
        
        # Filter
        results = [s for s in stocks if keyword in s['name'] or keyword in s['code']]
        
        if not results:
            QMessageBox.information(self, "검색 결과", "검색된 종목이 없습니다.")
            return
            
        if len(results) == 1:
            # Exact match or only one result
            self.select_stock(results[0])
        else:
            # Multiple results - Show dialog
            self.show_search_dialog(results)
            
    def show_search_dialog(self, results):
        dialog = QDialog(self)
        dialog.setWindowTitle("종목 선택")
        layout = QVBoxLayout()
        
        list_widget = QListWidget()
        for s in results:
            list_widget.addItem(f"{s['name']} ({s['code']})")
            
        def on_select():
            idx = list_widget.currentRow()
            if idx >= 0:
                self.select_stock(results[idx])
                dialog.accept()
                
        list_widget.itemDoubleClicked.connect(on_select)
        
        select_btn = QPushButton("선택")
        select_btn.clicked.connect(on_select)
        
        layout.addWidget(list_widget)
        layout.addWidget(select_btn)
        dialog.setLayout(layout)
        dialog.exec_()
        
    def select_stock(self, stock):
        self.log(f"종목 선택: {stock['name']} ({stock['code']})")
        self.search_input.setText("")
        self.bt_code_input.setText(stock['code']) # Update backtest input
        # Future: Update chart with this stock
        QMessageBox.information(self, "종목 선택", f"선택된 종목: {stock['name']}\n백테스트 및 차트 대상이 변경되었습니다.")
    
    def log(self, message):
        """로그 메시지 출력"""
        self.log_text.append(f"[{QTime.currentTime().toString()}] {message}")
    
    def update_ui(self):
        """UI 업데이트 (타이머 콜백)"""
        # Update balance
        self.balance_label.setText(f"예수금: {self.trader.balance:,.0f} 원")
        
        # Update positions
        # TODO: Implement position update logic
        pass
    
    def toggle_trading(self):
        """자동매매 시작/중지"""
        if not self.trader.is_running:
            self.trader.is_running = True
            self.start_btn.setText("자동매매 중지")
            self.start_btn.setStyleSheet("background-color: #d63031;")
            self.log("✅ 자동매매 시작됨")
        else:
            self.trader.is_running = False
            self.start_btn.setText("자동매매 시작")
            self.start_btn.setStyleSheet("background-color: #00b894;")
            self.log("⏸️ 자동매매 중지됨")
    
    def panic_stop(self):
        """긴급 정지"""
        self.trader.is_running = False
        self.log("🚨 긴급 정지 발동!")
        QMessageBox.critical(self, "긴급 정지", "긴급 정지가 발동되었습니다!")
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("환경 설정")
        self.setMinimumWidth(400)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()

        # 1. API Settings
        api_group = QGroupBox("키움 API 설정")
        api_layout = QFormLayout()
        
        self.app_key_input = QLineEdit()
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setEchoMode(QLineEdit.Password)
        self.account_input = QLineEdit()
        
        api_layout.addRow("App Key:", self.app_key_input)
        api_layout.addRow("Secret Key:", self.secret_key_input)
        api_layout.addRow("계좌번호:", self.account_input)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["모의투자 (VTS)", "실전투자 (Real)"])
        api_layout.addRow("투자 모드:", self.mode_combo)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # 2. Kakao Settings
        kakao_group = QGroupBox("카카오톡 알림 설정")
        kakao_layout = QFormLayout()
        
        self.kakao_access_input = QLineEdit()
        self.kakao_refresh_input = QLineEdit()
        
        kakao_layout.addRow("Access Token:", self.kakao_access_input)
        kakao_layout.addRow("Refresh Token:", self.kakao_refresh_input)
        
        kakao_group.setLayout(kakao_layout)
        layout.addWidget(kakao_group)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def load_settings(self):
        self.app_key_input.setText(settings.get("APP_KEY", ""))
        self.secret_key_input.setText(settings.get("SECRET_KEY", ""))
        self.account_input.setText(settings.get("ACCOUNT_NO", ""))
        self.kakao_access_input.setText(settings.get("KAKAO_ACCESS_TOKEN", ""))
        self.kakao_refresh_input.setText(settings.get("KAKAO_REFRESH_TOKEN", ""))
        
        is_virtual = settings.get("IS_VIRTUAL", True)
        self.mode_combo.setCurrentIndex(0 if is_virtual else 1)

    def save_settings(self):
        new_settings = {
            "APP_KEY": self.app_key_input.text().strip(),
            "SECRET_KEY": self.secret_key_input.text().strip(),
            "ACCOUNT_NO": self.account_input.text().strip(),
            "KAKAO_ACCESS_TOKEN": self.kakao_access_input.text().strip(),
            "KAKAO_REFRESH_TOKEN": self.kakao_refresh_input.text().strip(),
            "IS_VIRTUAL": self.mode_combo.currentIndex() == 0
        }
        settings.save_settings(new_settings)
        QMessageBox.information(self, "저장 완료", "설정이 저장되었습니다.")
        self.accept()
