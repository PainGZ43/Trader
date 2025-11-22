import sys
import os
import threading
import numpy as np
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg') # Prevent GUI crashes from plots in threads
import pyqtgraph as pg

from trading_manager import TradingManager
from config import Config
from ai.backtester import Backtester
from ai.strategy_optimizer import StrategyOptimizer
from logger import logger
from ui.settings_dialog import SettingsDialog
from strategy_manager import StrategyManager
from watchlist_manager import WatchlistManager
from ai.recommender import StockRecommender

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# ML Imports (Top-level for stability)
try:
    from ai.data_collector import DataCollector
    from ai.indicators import IndicatorCalculator
    from ai.lstm_model import LSTMPredictor, TENSORFLOW_AVAILABLE
    from ai.xgboost_model import XGBoostPredictor
except ImportError as e:
    print(f"Warning: ML modules not found: {e}")
    TENSORFLOW_AVAILABLE = False

class MainWindow(QMainWindow):
    # Define signals for thread communication
    training_progress_signal = pyqtSignal(int)
    training_log_signal = pyqtSignal(str)
    training_finished_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.trader = TradingManager()
        self.backtester = Backtester()
        self.watchlist_manager = WatchlistManager()
        self.strategy_manager = StrategyManager()
        self.recommender = StockRecommender()
        
        # Connect signals
        self.training_progress_signal.connect(self.update_training_progress)
        self.training_log_signal.connect(self.update_training_log)
        self.training_finished_signal.connect(self.on_training_finished)
        
        self.setWindowTitle("키움 AI 트레이더 (프리미엄)")
        self.setGeometry(100, 100, 1280, 800)
        
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
        
        # 1. Top Bar (Status & Controls)
        top_bar = QHBoxLayout()
        
        self.status_label = QLabel("시스템: 준비")
        self.status_label.setStyleSheet("color: #00b894; font-weight: bold;")
        
        self.balance_label = QLabel(f"예수금: {self.trader.balance:,.0f} 원")
        self.balance_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
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
        top_bar.addWidget(self.start_btn)
        top_bar.addWidget(self.panic_btn)
        
        main_layout.addLayout(top_bar)
        
        # 2. Content Area (Tabs)
        self.tabs = QTabWidget()
        
        self.tab_dashboard = QWidget()
        self.tab_chart = QWidget()
        self.tab_watchlist = QWidget()
        self.tab_recommend = QWidget()
        # self.tab_backtest = QWidget() # Removed
        # self.tab_settings = QWidget() # Removed
        
        self.init_dashboard()
        self.init_chart()
        self.init_ai_tab() # New
        self.init_watchlist()
        self.init_recommend()
        
        self.tabs.addTab(self.tab_dashboard, "대시보드")
        self.tabs.addTab(self.tab_chart, "실시간 차트")
        self.tabs.addTab(self.tab_ai, "🤖 AI 트레이딩 & 백테스트")
        self.tabs.addTab(self.tab_watchlist, "관심종목")
        self.tabs.addTab(self.tab_recommend, "AI 추천")
        
        main_layout.addWidget(self.tabs)
        
        # 3. Log Console
        log_group = QGroupBox("시스템 로그")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        log_group.setMaximumHeight(150)
        
        main_layout.addWidget(log_group)
        
        # 4. Progress Bar
        main_layout.addWidget(self.progress_bar)

    def on_interval_changed(self, interval):
        """데이터 간격 변경 시 학습 기간 옵션 자동 조정"""
        self.train_period_combo.blockSignals(True)
        self.train_period_combo.clear()
        
        periods = []
        default_period = ""
        
        if interval == "1m":
            periods = ["1d", "5d"]
            default_period = "5d"
        elif interval in ["2m", "5m", "15m", "30m", "90m"]:
            periods = ["1d", "5d", "1mo"]
            default_period = "1mo"
        elif interval in ["60m", "1h"]:
            periods = ["1mo", "3mo", "6mo", "1y", "2y"]
            default_period = "1y"
        else:
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
        
        # Base time in minutes
        base_time = 5 
        
        # Period factor
        if period == "1mo": factor = 0.2
        elif period == "3mo": factor = 0.5
        elif period == "6mo": factor = 0.8
        elif period == "1y": factor = 1.0
        elif period == "2y": factor = 1.8
        elif period == "5y": factor = 4.0
        else: factor = 1.0
        
        # Interval factor
        if interval == "1m": factor *= 10.0
        elif interval == "5m": factor *= 3.0
        elif interval == "30m": factor *= 1.5
        elif interval == "1h": factor *= 1.0
        elif interval == "1d": factor *= 0.2
        else: factor *= 1.0
        
        est_minutes = base_time * factor
        
        if use_gpu:
            est_minutes *= 0.4
            
        self.estimated_time_label.setText(f"예상 소요 시간: 약 {est_minutes:.1f} 분")

    def start_ai_training(self):
        """AI 모델 학습 시작"""
        self.training_cancel_flag = False
        
        # UI 잠금
        self.train_start_btn.setEnabled(False)
        self.train_stop_btn.setEnabled(True)
        self.train_progress.setVisible(True)
        self.train_progress.setValue(0)
        self.train_result_text.clear()
        
        # 파라미터 가져오기
        stock_code = self.train_code_input.text()
        period = self.train_period_combo.currentText()
        interval = self.train_interval_combo.currentText()
        
        # Start thread
        thread = threading.Thread(target=self._run_training_process, args=(stock_code, period, interval), daemon=True)
        thread.start()

    def _run_training_process(self, stock_code, period, interval):
        """AI 학습 프로세스 (백그라운드 스레드)"""
        try:
            self.training_progress_signal.emit(5)
            self.training_log_signal.emit("[1/4] 데이터 다운로드 중...")
            
            collector = DataCollector()
            yf_symbol = DataCollector.convert_korean_code(stock_code)
            df = collector.get_stock_data(yf_symbol, period=period, interval=interval, use_cache=False)
            
            if self.training_cancel_flag:
                self.training_log_signal.emit("❌ 학습이 중단되었습니다\n")
                self.training_finished_signal.emit(False)
                return
            
            if df is None or len(df) < 100:
                self.training_log_signal.emit("❌ 데이터 부족 (최소 100개 필요)\n")
                self.training_finished_signal.emit(False)
                return
            
            self.training_progress_signal.emit(20)
            self.training_log_signal.emit(f"✓ {len(df)}개 데이터 다운로드 완료\n")
            self.training_log_signal.emit("[2/4] 기술적 지표 계산 중...")
            
            df = IndicatorCalculator.calculate_all(df)
            df = df.dropna()
            
            if self.training_cancel_flag:
                self.training_log_signal.emit("❌ 학습이 중단되었습니다\n")
                self.training_finished_signal.emit(False)
                return
            
            self.training_progress_signal.emit(40)
            self.training_log_signal.emit("✓ 지표 계산 완료\n")
            
            # LSTM 학습
            self.training_log_signal.emit("[3/4] LSTM 모델 학습 중...")
            
            lookback = 100
            X_lstm, y_lstm, scaler = collector.prepare_training_data(df, lookback=lookback)
            
            if TENSORFLOW_AVAILABLE:
                lstm_model = LSTMPredictor(lookback=lookback, n_features=X_lstm.shape[2])
                lstm_model.train(X_lstm, y_lstm, epochs=30, batch_size=32)
                self.training_progress_signal.emit(60)
                self.training_log_signal.emit("✓ LSTM 학습 완료\n")
            else:
                self.training_log_signal.emit("⚠️ TensorFlow 미사용, LSTM 스킵\n")
            
            if self.training_cancel_flag:
                self.training_log_signal.emit("❌ 학습이 중단되었습니다\n")
                self.training_finished_signal.emit(False)
                return
            
            collector.save_scaler(scaler, 'models/scaler.pkl')
            
            # XGBoost 학습
            self.training_log_signal.emit("[4/4] XGBoost 모델 학습 중...")
            
            feature_cols = IndicatorCalculator.get_feature_names()
            X_xgb = df[feature_cols].values
            y_xgb = (df['close'].shift(-1) > df['close']).astype(int).values
            
            mask = ~np.isnan(y_xgb)
            X_xgb = X_xgb[mask]
            y_xgb = y_xgb[mask]
            
            self.training_progress_signal.emit(70)
            
            xgboost_model = XGBoostPredictor()
            xgb_metrics = xgboost_model.train(X_xgb, y_xgb)
            
            self.training_progress_signal.emit(90)
            self.training_log_signal.emit("✓ XGBoost 학습 완료\n")
            
            # 완료
            self.training_progress_signal.emit(100)
            self.training_log_signal.emit("\n" + "="*50)
            self.training_log_signal.emit("\n✅ AI 학습 완료!")
            self.training_log_signal.emit(f"\nXGBoost 정확도: {xgb_metrics['accuracy']:.2%}")
            self.training_log_signal.emit(f"\nAUC: {xgb_metrics['auc']:.2%}\n")
            self.training_log_signal.emit(f"\n모델 저장 위치:\n")
            self.training_log_signal.emit(f"  - models/xgboost_model.pkl\n")
            self.training_log_signal.emit(f"  - models/scaler.pkl\n")
            
            # 5. 전략 최적화
            self.training_log_signal.emit("\n[5/5] 전략 최적화 진행 중...")
            self.training_log_signal.emit("  - 최적의 TP, SL, 진입 조건을 탐색합니다.")
            
            optimizer = StrategyOptimizer()
            # 최근 5일 데이터로 최적화 (1분봉 기준)
            opt_start = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
            opt_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            best_result, best_params, _ = optimizer.optimize(stock_code, opt_start, opt_end)
            
            if best_params:
                self.training_log_signal.emit(f"\n✅ 최적화 완료!")
                self.training_log_signal.emit(f"  - 수익률: {best_result['profit_pct']:.2f}%")
                self.training_log_signal.emit(f"  - MDD: {best_result['mdd']:.2f}%")
                import json
                self.training_log_signal.emit(f"  - 파라미터: {json.dumps(best_params, indent=2, ensure_ascii=False)}")
                
                # 파라미터 저장
                with open('strategy_params.json', 'w') as f:
                    json.dump(best_params, f, indent=4)
                self.training_log_signal.emit(f"  - 설정 저장됨: strategy_params.json\n")
            else:
                self.training_log_signal.emit("\n⚠️ 최적화 실패 (데이터 부족 등)\n")

            self.training_finished_signal.emit(True)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.training_log_signal.emit(f"\n❌ 오류 발생: {str(e)}\n")
            self.training_finished_signal.emit(False)
        except BaseException as e:
            import traceback
            traceback.print_exc()
            self.training_log_signal.emit(f"\n❌ 심각한 오류 발생: {str(e)}\n")
            self.training_finished_signal.emit(False)

    @pyqtSlot(int)
    def update_training_progress(self, value):
        self.train_progress.setValue(value)

    @pyqtSlot(str)
    def update_training_log(self, message):
        self.train_result_text.append(message)
        if "✅ AI 학습 완료" in message or "❌" in message:
             self.log(message.strip())

    @pyqtSlot(bool)
    def on_training_finished(self, success):
        self._finish_training(success)
        if success:
             QMessageBox.information(self, "학습 완료", "✅ AI 모델 학습이 완료되었습니다!")

    def cancel_training(self):
        """AI 학습 중단"""
        self.training_cancel_flag = True
        self.train_stop_btn.setEnabled(False)
        self.train_result_text.append("\n⏹️ 학습 중단 중...\n")
        self.log("⏹️ AI 학습 중단 요청")
    
    def _finish_training(self, success):
        """학습 완료 후 UI 복원"""
        self.train_start_btn.setEnabled(True)
        self.train_stop_btn.setEnabled(False)
        self.train_progress.setVisible(False)
        self.training_cancel_flag = False
        
        if success:
            self.training_log_signal.emit("학습 프로세스가 정상적으로 종료되었습니다.")
        else:
            self.training_log_signal.emit("학습 프로세스가 중단되거나 실패했습니다.")

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

    def init_ai_tab(self):
        """AI 트레이딩 & 백테스트 탭 초기화 (통합)"""
        self.tab_ai = QWidget()
        layout = QHBoxLayout()
        
        # --- Left Panel: AI Training ---
        train_group = QGroupBox("🧠 AI 모델 학습")
        train_layout = QVBoxLayout()
        
        # Input Form
        form_layout = QFormLayout()
        self.train_code_input = QLineEdit("005930") # Samsung Electronics
        self.train_period_combo = QComboBox()
        self.train_period_combo.addItems(["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"])
        self.train_period_combo.setCurrentText("5y")
        
        self.train_interval_combo = QComboBox()
        self.train_interval_combo.addItems(["1m", "5m", "1h", "1d"])
        self.train_interval_combo.setCurrentText("1d")
        self.train_interval_combo.currentTextChanged.connect(self.on_interval_changed)
        
        self.use_gpu_check = QCheckBox("GPU 가속 사용 (TensorFlow)")
        self.use_gpu_check.setChecked(TENSORFLOW_AVAILABLE)
        self.use_gpu_check.setEnabled(TENSORFLOW_AVAILABLE)
        
        form_layout.addRow("종목코드:", self.train_code_input)
        form_layout.addRow("학습 기간:", self.train_period_combo)
        form_layout.addRow("데이터 간격:", self.train_interval_combo)
        form_layout.addRow("", self.use_gpu_check)
        
        train_layout.addLayout(form_layout)
        
        # Estimated Time
        self.estimated_time_label = QLabel("예상 소요 시간: 약 5.0 분")
        self.estimated_time_label.setStyleSheet("color: #0984e3; font-weight: bold;")
        train_layout.addWidget(self.estimated_time_label)
        self.train_period_combo.currentTextChanged.connect(self.update_estimated_time)
        self.train_interval_combo.currentTextChanged.connect(self.update_estimated_time)
        self.use_gpu_check.stateChanged.connect(self.update_estimated_time)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.train_start_btn = QPushButton("🚀 AI 학습 시작")
        self.train_start_btn.clicked.connect(self.start_ai_training)
        self.train_start_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c5ce7; color: white; font-weight: bold; padding: 10px;
            }
            QPushButton:hover { background-color: #5f27cd; }
        """)
        
        self.train_stop_btn = QPushButton("⏹️ 중단")
        self.train_stop_btn.clicked.connect(self.cancel_training)
        self.train_stop_btn.setEnabled(False)
        self.train_stop_btn.setStyleSheet("background-color: #d63031; color: white; padding: 10px;")
        
        btn_layout.addWidget(self.train_start_btn)
        btn_layout.addWidget(self.train_stop_btn)
        train_layout.addLayout(btn_layout)
        
        # Progress
        self.train_progress = QProgressBar()
        self.train_progress.setVisible(False)
        train_layout.addWidget(self.train_progress)
        
        # Log
        self.train_result_text = QTextEdit()
        self.train_result_text.setReadOnly(True)
        train_layout.addWidget(self.train_result_text)
        
        # Settings Button
        self.open_settings_btn = QPushButton("🛠️ API 및 계좌 설정")
        self.open_settings_btn.clicked.connect(self.open_settings_dialog)
        train_layout.addWidget(self.open_settings_btn)
        
        train_group.setLayout(train_layout)
        
        # --- Right Panel: Backtest & Strategy ---
        backtest_group = QGroupBox("🧪 전략 백테스트 및 최적화")
        backtest_layout = QVBoxLayout()
        
        # 1. Strategy Selection
        strat_group = QGroupBox("전략 설정")
        strat_layout = QFormLayout()
        
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItem("기본 전략 (Default)", None)
        self.strategy_combo.currentIndexChanged.connect(self.on_strategy_selected)
        
        self.optimize_btn = QPushButton("🔍 최적 전략 찾기")
        self.optimize_btn.clicked.connect(self.find_optimal_strategy)
        self.optimize_btn.setStyleSheet("background-color: #fdcb6e; color: black;")
        
        strat_layout.addRow("전략 선택:", self.strategy_combo)
        strat_layout.addRow("", self.optimize_btn)
        
        # Manual Params
        self.spin_vol = QDoubleSpinBox()
        self.spin_vol.setRange(1.0, 10.0)
        self.spin_vol.setSingleStep(0.1)
        self.spin_vol.setValue(3.0)
        
        self.spin_ai = QDoubleSpinBox()
        self.spin_ai.setRange(0.0, 1.0)
        self.spin_ai.setSingleStep(0.05)
        self.spin_ai.setValue(0.7)
        
        self.spin_tp = QDoubleSpinBox()
        self.spin_tp.setRange(0.1, 50.0)
        self.spin_tp.setSingleStep(0.1)
        self.spin_tp.setSuffix("%")
        self.spin_tp.setValue(1.0)
        
        self.spin_sl = QDoubleSpinBox()
        self.spin_sl.setRange(0.1, 50.0)
        self.spin_sl.setSingleStep(0.1)
        self.spin_sl.setSuffix("%")
        self.spin_sl.setValue(0.5)
        
        self.spin_cooldown = QSpinBox()
        self.spin_cooldown.setRange(0, 120)
        self.spin_cooldown.setSuffix("분")
        self.spin_cooldown.setValue(10)
        
        self.spin_time_exit = QSpinBox()
        self.spin_time_exit.setRange(0, 120)
        self.spin_time_exit.setSuffix("분")
        self.spin_time_exit.setValue(10)
        
        params_layout = QGridLayout()
        params_layout.addWidget(QLabel("거래량 배수:"), 0, 0)
        params_layout.addWidget(self.spin_vol, 0, 1)
        params_layout.addWidget(QLabel("AI 임계값:"), 0, 2)
        params_layout.addWidget(self.spin_ai, 0, 3)
        
        params_layout.addWidget(QLabel("익절(TP):"), 1, 0)
        params_layout.addWidget(self.spin_tp, 1, 1)
        params_layout.addWidget(QLabel("손절(SL):"), 1, 2)
        params_layout.addWidget(self.spin_sl, 1, 3)
        
        params_layout.addWidget(QLabel("쿨다운:"), 2, 0)
        params_layout.addWidget(self.spin_cooldown, 2, 1)
        params_layout.addWidget(QLabel("시간청산:"), 2, 2)
        params_layout.addWidget(self.spin_time_exit, 2, 3)
        
        strat_layout.addRow(params_layout)
        strat_group.setLayout(strat_layout)
        backtest_layout.addWidget(strat_group)
        
        # 2. Backtest Controls
        bt_form = QFormLayout()
        self.backtest_code_input = QLineEdit("005930")
        self.backtest_start_date = QDateEdit(datetime.now().date() - timedelta(days=7))
        self.backtest_start_date.setCalendarPopup(True)
        self.backtest_end_date = QDateEdit(datetime.now().date())
        self.backtest_end_date.setCalendarPopup(True)
        
        bt_form.addRow("종목코드:", self.backtest_code_input)
        bt_form.addRow("시작일:", self.backtest_start_date)
        bt_form.addRow("종료일:", self.backtest_end_date)
        
        backtest_layout.addLayout(bt_form)
        
        self.run_backtest_btn = QPushButton("▶️ 백테스트 실행 (상세 리포트)")
        self.run_backtest_btn.clicked.connect(self.run_backtest)
        self.run_backtest_btn.setStyleSheet("""
            QPushButton {
                background-color: #00b894; color: white; font-weight: bold; padding: 10px;
            }
            QPushButton:hover { background-color: #00a884; }
        """)
        backtest_layout.addWidget(self.run_backtest_btn)
        
        # Backtest Log
        self.backtest_log = QTextEdit()
        self.backtest_log.setReadOnly(True)
        self.backtest_log.setStyleSheet("background-color: #2d3436; color: #dfe6e9; font-family: Consolas;")
        backtest_layout.addWidget(self.backtest_log)
        
        backtest_group.setLayout(backtest_layout)
        
        # Add to Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(train_group)
        splitter.addWidget(backtest_group)
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
        self.tab_ai.setLayout(layout)
        
        # Load strategies
        self.load_strategies()

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
        code = self.backtest_code_input.text()
        start_date = self.backtest_start_date.date().toString("yyyy-MM-dd")
        end_date = self.backtest_end_date.date().toString("yyyy-MM-dd")
        
        self.log(f"{code} 백테스트 실행 중... ({start_date} ~ {end_date})")
        
        # Show progress bar (using train_progress for now or create new one? 
        # Actually init_ai_tab has backtest_log but no separate progress bar for backtest.
        # Let's use the main window progress bar or the one in AI tab?
        # The AI tab has train_progress. Let's use the main window progress bar if possible, 
        # but init_ui added self.progress_bar at the bottom.
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Define progress callback
        def progress_callback(pct):
            self.progress_bar.setValue(pct)
            QApplication.processEvents()
        
        # Reload models to ensure latest training is used
        if self.backtester.reload_models():
            self.log("AI 모델을 성공적으로 불러왔습니다.")
        else:
            self.log("⚠️ AI 모델 로드 실패 (기본 전략으로 진행)")
            
        # Run backtest
        result = self.backtester.run(code, start_date, end_date, progress_callback=progress_callback)
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Build Report (Simplified for Log)
        report = f"""
        [백테스트 결과]
        기간: {start_date} ~ {end_date}
        수익률: {result['profit_pct']:.2f}%
        총 손익: {result['total_profit']:,.0f}원
        MDD: {result['mdd']:.2f}%
        매매횟수: {result['trade_count']}회
        """
        self.backtest_log.append(report)
        self.log(f"백테스트 완료: 수익률 {result['profit_pct']:.2f}%")

    def log(self, message):
        self.log_text.append(f"[{QTime.currentTime().toString()}] {message}")
        # Also log to AI tab if relevant? No, keep separate.

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
        self.train_code_input.setText(stock['code']) # Update training input
        self.backtest_code_input.setText(stock['code']) # Update backtest input
        # Future: Update chart with this stock
        QMessageBox.information(self, "종목 선택", f"선택된 종목: {stock['name']}\nAI 학습 및 백테스트 대상이 변경되었습니다.")

    def open_settings_dialog(self):
        """설정 대화상자 열기"""
        dialog = SettingsDialog(self)
        dialog.exec_()


    # Watchlist Management Methods
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

    # AI Recommendations Methods
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
        self.analyze_btn.clicked.connect(self.analyze_watchlist)
        self.analyze_btn.setStyleSheet("background-color: #6c5ce7; color: white; padding: 10px; font-weight: bold;")
        
        btn_layout.addWidget(self.analyze_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 진행 바
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

    def analyze_watchlist(self):
        """관심종목 AI 분석"""
        stocks = self.watchlist_manager.get_all()
        
        if not stocks:
            self.log("분석할 관심종목이 없습니다")
            return
        
        self.log(f"🎯 {len(stocks)}개 종목 AI 분석 시작...")
        self.analyze_btn.setEnabled(False)
        self.recommend_progress.setVisible(True)
        self.recommend_progress.setValue(0)
        
        def analyze_thread():
            def update_progress(current, total):
                pct = int((current / total) * 100)
                self.recommend_progress.setValue(pct)
                QApplication.processEvents()
            
            try:
                results = self.recommender.analyze_stocks(
                    [s['code'] for s in stocks],
                    progress_callback=update_progress
                )
                
                self.recommend_progress.setValue(100)
                self.display_recommendations(results)
                self.log(f"✅ AI 분석 완료: {len(results)}개 종목")
            except Exception as e:
                self.log(f"❌ AI 분석 실패: {str(e)}")
            finally:
                self.analyze_btn.setEnabled(True)
                self.recommend_progress.setVisible(False)
        
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
            self.recommend_table.setItem(i, 2, QTableWidgetItem(f"{result.get('price', 0):,.0f}"))
            
            # AI점수
            ai_item = QTableWidgetItem(f"{result['ai_score']:.2f}")
            ai_item.setForeground(QColor("#74b9ff"))
            self.recommend_table.setItem(i, 3, ai_item)
            
            # 감성
            sent_item = QTableWidgetItem(f"{result['sentiment_score']:.2f}")
            self.recommend_table.setItem(i, 4, sent_item)
            
            # 기술
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
